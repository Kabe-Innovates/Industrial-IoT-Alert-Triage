from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from openenv.core.env_server.interfaces import Environment

from graders import grade_episode, grade_step
from models import AlertAction, AlertObservation, AlertState, EpisodeSummary, RewardSignal
from tasks import ALL_TASKS, GradedTask


class IndustrialIotAlertTriageEnvironment(Environment[AlertAction, AlertObservation, AlertState]):
    def __init__(self, task_name: str | None = None):
        self._task_index = 0
        self._fixed_task_name = task_name
        self._task = self._select_task(task_name)
        self._state = self._new_state()
        self._current_sample_index = 0
        self._history: list[str] = []
        self._last_observation: AlertObservation | None = None

    def _select_task(self, task_name: str | None) -> GradedTask:
        if task_name:
            for task in ALL_TASKS:
                if task.name == task_name:
                    return task
        return ALL_TASKS[self._task_index % len(ALL_TASKS)]

    def _task_catalog(self) -> list[dict[str, str]]:
        return [{"name": task.name, "difficulty": task.difficulty} for task in ALL_TASKS]

    def _new_state(self) -> AlertState:
        return AlertState(
            episode_id=str(uuid4()),
            step_count=0,
            task_name=self._task.name,
            task_difficulty=self._task.difficulty,
            total_samples=len(self._task.samples),
            processed_samples=0,
            correct_decisions=0,
            incorrect_decisions=0,
            shutdown_count=0,
            terminated=False,
            last_action=None,
        )

    def _build_observation(self, *, done: bool = False, reward: float = 0.0, explanation: str = "") -> AlertObservation:
        sample = self._task.samples[min(self._current_sample_index, len(self._task.samples) - 1)]
        summary = EpisodeSummary(
            episode_score=grade_episode(self._state.correct_decisions, max(1, self._state.processed_samples)),
            task_name=self._task.name,
            correct_decisions=self._state.correct_decisions,
            total_decisions=self._state.processed_samples,
        )
        obs = AlertObservation(
            sample=sample,
            guidance=explanation or self._task.objective,
            task_name=self._task.name,
            task_difficulty=self._task.difficulty,
            available_actions=[0, 1, 2],
            history_summary=list(self._history[-5:]),
            episode_summary=summary,
            reward_signal=RewardSignal(
                raw_reward=reward,
                normalized_reward=reward,
                task_score=summary.episode_score,
                penalty=0.0,
                success=False,
            ),
            done=done,
            reward=reward,
            info={
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "expected_actions": list(self._task.expected_actions),
                "active_task": self._task.name,
                "available_tasks": [task.name for task in ALL_TASKS],
                "task_catalog": self._task_catalog(),
            },
        )
        return obs

    def reset(self) -> AlertObservation:
        # If TASK_NAME is not pinned, rotate tasks across episodes so validators can
        # discover and grade all registered tasks deterministically.
        if self._fixed_task_name:
            self._task = self._select_task(self._fixed_task_name)
        else:
            self._task = ALL_TASKS[self._task_index % len(ALL_TASKS)]
            self._task_index = (self._task_index + 1) % len(ALL_TASKS)

        self._state = self._new_state()
        self._current_sample_index = 0
        self._history.clear()
        self._last_observation = self._build_observation(done=False, reward=0.0)
        return self._last_observation

    def step(self, action: AlertAction) -> AlertObservation:
        if self._state.terminated:
            return self._build_observation(done=True, reward=0.0, explanation="Episode already terminated.")

        current_index = min(self._current_sample_index, len(self._task.samples) - 1)
        result = grade_step(self._task, self._state, action, current_index)

        self._state.step_count += 1
        self._state.processed_samples += 1
        self._state.last_action = action.decision
        if result.correct:
            self._state.correct_decisions += 1
        else:
            self._state.incorrect_decisions += 1
            if action.decision == 2:
                self._state.shutdown_count += 1

        self._history.append(
            f"step={self._state.step_count} action={action.decision} reward={result.reward_signal.normalized_reward:.3f}"
        )

        self._current_sample_index += 1
        done = self._current_sample_index >= len(self._task.samples)
        self._state.terminated = done

        summary_score = grade_episode(self._state.correct_decisions, self._state.processed_samples)
        reward_value = result.reward_signal.normalized_reward
        self._last_observation = AlertObservation(
            sample=self._task.samples[current_index],
            guidance=result.explanation,
            task_name=self._task.name,
            task_difficulty=self._task.difficulty,
            available_actions=[0, 1, 2],
            history_summary=list(self._history[-5:]),
            episode_summary=EpisodeSummary(
                episode_score=summary_score,
                task_name=self._task.name,
                correct_decisions=self._state.correct_decisions,
                total_decisions=self._state.processed_samples,
            ),
            reward_signal=result.reward_signal,
            done=done,
            reward=reward_value,
            info={
                "task": self._task.name,
                "difficulty": self._task.difficulty,
                "active_task": self._task.name,
                "available_tasks": [task.name for task in ALL_TASKS],
                "task_catalog": self._task_catalog(),
                "expected_actions": list(self._task.expected_actions),
            },
        )
        return self._last_observation

    @property
    def state(self) -> AlertState:
        return self._state
