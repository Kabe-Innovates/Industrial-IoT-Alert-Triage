#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import inspect
import json
import os
import re
import sys
from typing import Any, List

from openai import OpenAI

from client import IndustrialIotAlertTriageEnv
from models import AlertAction
from tasks import ALL_TASKS

API_BASE_URL = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4.1-mini")
HF_TOKEN = os.getenv("HF_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or HF_TOKEN
API_KEY = OPENAI_API_KEY
IMAGE_NAME = os.getenv("IMAGE_NAME", "industrial-iot-alert-triage:latest")
BENCHMARK = os.getenv("BENCHMARK", "industrial_iot_alert_triage")
TASK_NAME = os.getenv("TASK_NAME", ALL_TASKS[0].name)
INFERENCE_MODE = os.getenv("INFERENCE_MODE", "single").strip().lower()
HOST_PORT = int(os.getenv("HOST_PORT", "18000"))
MAX_STEPS = int(os.getenv("MAX_STEPS", "6"))
SUCCESS_SCORE_THRESHOLD = float(os.getenv("SUCCESS_SCORE_THRESHOLD", "0.6"))
MAX_TOTAL_REWARD = float(os.getenv("MAX_TOTAL_REWARD", str(MAX_STEPS)))
DECISION_RE = re.compile(r"\b([012])\b")


def _as_lower_bool(value: bool) -> str:
    return "true" if value else "false"


def _format_error(error: str | None) -> str:
    return "null" if error is None else error


def _format_rewards(rewards: list[float]) -> str:
    return ",".join(f"{value:.2f}" for value in rewards)


def _emit(message: str) -> None:
    print(message, flush=True)


def log_start(task: str, env: str, model: str) -> None:
    _emit(f"[START] task={task} env={env} model={model}")


def log_step(step: int, action: int, reward: float, done: bool, error: str | None) -> None:
    _emit(
        f"[STEP] step={step} action={action} reward={reward:.2f} "
        f"done={_as_lower_bool(done)} error={_format_error(error)}"
    )


def log_end(success: bool, steps: int, score: float, rewards: list[float]) -> None:
    _emit(
        f"[END] success={_as_lower_bool(success)} steps={steps} "
        f"score={score:.3f} rewards={_format_rewards(rewards)}"
    )


def get_model_message(client: OpenAI, sample_text: str, history: list[str]) -> str:
    messages = [
        {"role": "system", "content": "You are an expert industrial diagnostic engineer. Reply with a single digit 0, 1, or 2 and a short rationale."},
        {"role": "user", "content": sample_text + "\n\nHistory:\n" + "\n".join(history[-4:])},
    ]
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=0.0,
            max_tokens=64,
        )
        text = (response.choices[0].message.content or "").strip()
        return text or "0"
    except Exception as exc:
        print(f"[DEBUG] Model request failed: {exc}", flush=True)
        return "hello"


def get_model_message_for_step(
    client: OpenAI,
    step: int,
    last_snapshot: str,
    last_reward: float,
    history: List[str],
) -> str:
    prompt = (
        f"Task: triage industrial telemetry alert #{step}.\n"
        f"Last reward: {last_reward:.3f}\n"
        f"Last observation: {last_snapshot}\n"
        f"History: {' | '.join(history[-4:]) if history else 'none'}\n\n"
        "Reply with one triage choice (0, 1, or 2) and short rationale."
    )
    return get_model_message(client, prompt, history)


def _extract_decision(model_message: str) -> int:
    match = DECISION_RE.search(model_message)
    if match:
        return int(match.group(1))
    return 0


async def main() -> None:
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY or "dummy-key")

    task_names = [task.name for task in ALL_TASKS] if INFERENCE_MODE == "multi" else [TASK_NAME]

    all_rewards: List[float] = []
    total_steps = 0
    task_scores: List[float] = []

    log_start(task=",".join(task_names), env=BENCHMARK, model=MODEL_NAME)

    for task_name in task_names:
        env = None

        history: List[str] = []
        rewards: List[float] = []
        steps_taken = 0
        score = 0.0
        success = False

        try:
            env = await IndustrialIotAlertTriageEnv.from_docker_image(
                IMAGE_NAME,
                env_vars={"TASK_NAME": task_name},
                ports={8000: HOST_PORT},
            )
            result = await env.reset()  # OpenENV.reset()
            last_snapshot = json.dumps(result.observation.sample.model_dump(), sort_keys=True)
            last_reward = 0.0

            for step in range(1, MAX_STEPS + 1):
                if result.done:
                    break

                message = get_model_message_for_step(client, step, last_snapshot, last_reward, history)
                decision = _extract_decision(message)

                result = await env.step(AlertAction(decision=decision, rationale=message[:120]))
                obs = result.observation

                reward = result.reward or 0.0
                done = result.done
                error = None

                rewards.append(reward)
                steps_taken = step
                last_snapshot = json.dumps(obs.sample.model_dump(), sort_keys=True)
                last_reward = reward

                log_step(step=step, action=decision, reward=reward, done=done, error=error)

                history.append(f"Step {step}: {message!r} -> reward {reward:+.2f}")

                if done:
                    break

            score = sum(rewards) / MAX_TOTAL_REWARD if MAX_TOTAL_REWARD > 0 else 0.0
            score = min(max(score, 0.0), 1.0)
            success = score >= SUCCESS_SCORE_THRESHOLD
            all_rewards.extend(rewards)
            total_steps += steps_taken
            task_scores.append(score)

        finally:
            if env is not None:
                try:
                    close_result = env.close()
                    if inspect.isawaitable(close_result):
                        await close_result
                except Exception as e:
                    print(f"[DEBUG] env.close() error (container cleanup): {e}", flush=True)

    overall = sum(task_scores) / len(task_scores) if task_scores else 0.0
    overall = min(max(overall, 0.0), 1.0)
    log_end(
        success=overall >= SUCCESS_SCORE_THRESHOLD,
        steps=total_steps,
        score=overall,
        rewards=all_rewards,
    )


if __name__ == "__main__":
    asyncio.run(main())
