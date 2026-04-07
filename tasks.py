from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from models import TelemetrySample


TaskDifficulty = Literal["easy", "medium", "hard"]


@dataclass(frozen=True)
class GradedTask:
    name: str
    difficulty: TaskDifficulty
    objective: str
    samples: list[TelemetrySample]
    expected_actions: list[int]
    partial_credit: list[float]
    penalty_on_invalid: float = -0.2
    penalty_on_noop_loop: float = -0.1


def _sample(
    *,
    sensor_id: str,
    facility_id: str,
    metric: str,
    current_value: float,
    baseline_mean: float,
    baseline_std: float,
    uptime_hours: float,
    timestamp: str,
    severity_hint: str,
    history_points: list[float],
    notes: str,
) -> TelemetrySample:
    return TelemetrySample(
        sensor_id=sensor_id,
        facility_id=facility_id,
        metric=metric,
        current_value=current_value,
        baseline_mean=baseline_mean,
        baseline_std=baseline_std,
        uptime_hours=uptime_hours,
        timestamp=timestamp,
        severity_hint=severity_hint,
        history_points=history_points,
        notes=notes,
    )


EASY_TASK = GradedTask(
    name="obvious_sensor_fault",
    difficulty="easy",
    objective="Identify obvious sensor failures or healthy readings.",
    samples=[
        _sample(
            sensor_id="temp-01",
            facility_id="plant-a",
            metric="temperature",
            current_value=79.5,
            baseline_mean=79.8,
            baseline_std=0.4,
            uptime_hours=120.0,
            timestamp="2026-04-08T09:00:00Z",
            severity_hint="healthy",
            history_points=[79.7, 79.8, 79.6, 79.9],
            notes="Stable operating temperature.",
        ),
        _sample(
            sensor_id="vib-03",
            facility_id="plant-a",
            metric="vibration",
            current_value=0.1,
            baseline_mean=0.12,
            baseline_std=0.03,
            uptime_hours=88.0,
            timestamp="2026-04-08T09:05:00Z",
            severity_hint="healthy",
            history_points=[0.11, 0.12, 0.10, 0.13],
            notes="No anomaly detected.",
        ),
    ],
    expected_actions=[0, 0],
    partial_credit=[1.0, 1.0],
)

MEDIUM_TASK = GradedTask(
    name="sensor_drift_recalibration",
    difficulty="medium",
    objective="Detect drift and request recalibration before failure cascades.",
    samples=[
        _sample(
            sensor_id="press-07",
            facility_id="plant-b",
            metric="pressure",
            current_value=34.9,
            baseline_mean=31.0,
            baseline_std=0.6,
            uptime_hours=244.0,
            timestamp="2026-04-08T10:00:00Z",
            severity_hint="drift",
            history_points=[31.1, 31.2, 31.4, 32.0],
            notes="Gradual upward drift; machine still safe but calibration likely off.",
        ),
        _sample(
            sensor_id="press-07",
            facility_id="plant-b",
            metric="pressure",
            current_value=35.4,
            baseline_mean=31.0,
            baseline_std=0.6,
            uptime_hours=244.5,
            timestamp="2026-04-08T10:05:00Z",
            severity_hint="drift",
            history_points=[31.4, 32.0, 33.1, 34.0],
            notes="Drift confirmed; sensor needs recalibration now.",
        ),
    ],
    expected_actions=[1, 1],
    partial_credit=[0.7, 1.0],
)

HARD_TASK = GradedTask(
    name="cascading_failure_escalation",
    difficulty="hard",
    objective="Prioritize shutdown only when readings indicate credible imminent failure.",
    samples=[
        _sample(
            sensor_id="motor-22",
            facility_id="plant-c",
            metric="motor_current",
            current_value=17.8,
            baseline_mean=16.2,
            baseline_std=0.3,
            uptime_hours=401.0,
            timestamp="2026-04-08T11:00:00Z",
            severity_hint="drift",
            history_points=[16.3, 16.5, 16.9, 17.1],
            notes="Elevated current plus temperature drift in a neighboring line.",
        ),
        _sample(
            sensor_id="motor-22",
            facility_id="plant-c",
            metric="motor_current",
            current_value=21.9,
            baseline_mean=16.2,
            baseline_std=0.3,
            uptime_hours=401.2,
            timestamp="2026-04-08T11:04:00Z",
            severity_hint="failure",
            history_points=[17.1, 18.5, 19.8, 21.0],
            notes="Rapid acceleration of anomaly suggests imminent mechanical failure.",
        ),
    ],
    expected_actions=[1, 2],
    partial_credit=[0.4, 1.0],
)

ALL_TASKS = [EASY_TASK, MEDIUM_TASK, HARD_TASK]
