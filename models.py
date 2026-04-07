from __future__ import annotations

from typing import Any, Literal

from openenv.core.env_server.types import Action, Observation, State
from pydantic import BaseModel, Field, ConfigDict


class TelemetrySample(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sensor_id: str
    facility_id: str
    metric: str
    current_value: float
    baseline_mean: float
    baseline_std: float
    uptime_hours: float
    timestamp: str
    severity_hint: Literal["healthy", "drift", "failure"]
    history_points: list[float] = Field(default_factory=list)
    notes: str = ""


class AlertAction(Action):
    model_config = ConfigDict(extra="forbid")

    decision: Literal[0, 1, 2] = Field(
        description="0 = Ignore/Sensor Error, 1 = Recalibrate Sensor, 2 = Trigger Emergency Shutdown"
    )
    rationale: str = Field(default="")


class RewardSignal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    raw_reward: float = 0.0
    normalized_reward: float = 0.0
    task_score: float = 0.0
    penalty: float = 0.0
    success: bool = False


class EpisodeSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    episode_score: float = 0.0
    task_name: str = ""
    correct_decisions: int = 0
    total_decisions: int = 0


class AlertObservation(Observation):
    model_config = ConfigDict(extra="forbid")

    sample: TelemetrySample
    guidance: str = ""
    task_name: str = ""
    task_difficulty: Literal["easy", "medium", "hard"] = "easy"
    available_actions: list[int] = Field(default_factory=lambda: [0, 1, 2])
    history_summary: list[str] = Field(default_factory=list)
    episode_summary: EpisodeSummary = Field(default_factory=EpisodeSummary)
    reward_signal: RewardSignal = Field(default_factory=RewardSignal)
    done: bool = False
    reward: float = 0.0
    info: dict[str, Any] = Field(default_factory=dict)


class AlertState(State):
    model_config = ConfigDict(extra="forbid")

    episode_id: str = ""
    step_count: int = 0
    task_name: str = ""
    task_difficulty: Literal["easy", "medium", "hard"] = "easy"
    total_samples: int = 0
    processed_samples: int = 0
    correct_decisions: int = 0
    incorrect_decisions: int = 0
    shutdown_count: int = 0
    terminated: bool = False
    last_action: int | None = None
