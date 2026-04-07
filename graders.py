from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from models import AlertAction, AlertState, RewardSignal
from tasks import GradedTask


@dataclass(frozen=True)
class GraderResult:
    reward_signal: RewardSignal
    correct: bool
    explanation: str


def grade_step(
    task: GradedTask,
    state: AlertState,
    action: AlertAction,
    sample_index: int,
) -> GraderResult:
    expected = task.expected_actions[sample_index]
    base_credit = task.partial_credit[sample_index]

    if action.decision == expected:
        raw_reward = base_credit
        penalty = 0.0
        correct = True
        explanation = "Correct triage decision."
    elif action.decision == 0 and expected in {1, 2}:
        raw_reward = -0.6 if expected == 1 else -1.0
        penalty = abs(raw_reward)
        correct = False
        explanation = "Unsafe ignore decision."
    elif action.decision == 1 and expected == 2:
        raw_reward = -0.4
        penalty = abs(raw_reward)
        correct = False
        explanation = "Recalibration insufficient for imminent failure."
    elif action.decision == 2 and expected == 1:
        raw_reward = -0.5
        penalty = abs(raw_reward)
        correct = False
        explanation = "Over-escalation: shutdown was unnecessary."
    else:
        raw_reward = -0.3
        penalty = abs(raw_reward)
        correct = False
        explanation = "Incorrect triage decision."

    if action.rationale.strip() == "":
        raw_reward -= 0.05
        penalty += 0.05

    if state.last_action == action.decision:
        raw_reward -= task.penalty_on_noop_loop
        penalty += abs(task.penalty_on_noop_loop)

    normalized_reward = max(0.0, min(1.0, (raw_reward + 1.0) / 2.0))

    return GraderResult(
        reward_signal=RewardSignal(
            raw_reward=raw_reward,
            normalized_reward=normalized_reward,
            task_score=normalized_reward,
            penalty=penalty,
            success=correct,
        ),
        correct=correct,
        explanation=explanation,
    )


def grade_episode(correct_decisions: int, total_decisions: int) -> float:
    if total_decisions <= 0:
        return 0.0
    ratio = correct_decisions / total_decisions
    return max(0.0, min(1.0, ratio))


def summarize_scores(scores: Iterable[float]) -> float:
    values = list(scores)
    if not values:
        return 0.0
    return max(0.0, min(1.0, sum(values) / len(values)))
