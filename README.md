# Industrial IoT Alert Triage

Deterministic OpenEnv benchmark for industrial telemetry alert triage in real-world manufacturing and infrastructure operations.

## Real-World Motivation: Alert Fatigue in Industrial Operations

Industrial monitoring systems produce high volumes of telemetry alerts. In practice, operators must quickly decide whether an alert is harmless sensor noise, a calibration issue, or a genuine safety risk.

This environment models that triage burden directly: wrong ignores can miss imminent failures, while unnecessary shutdowns reduce uptime and increase operational cost.

## Environment Interface

This project implements the standard OpenEnv contract:

- reset
- step(action)
- state

Implementation lives in `server/environment.py`.

## Action Space

Defined in `models.py` as `AlertAction`:

- 0: Ignore or sensor fault
- 1: Recalibrate sensor
- 2: Emergency shutdown

## Observation Space (Data Definitions)

Defined in `models.py` as `AlertObservation` and `TelemetrySample`.

Each observation includes:

- sample fields:
	- sensor_id
	- facility_id
	- metric
	- current_value
	- baseline_mean
	- baseline_std
	- uptime_hours
	- timestamp
	- severity_hint
	- history_points
	- notes
- task context:
	- task_name
	- task_difficulty
	- guidance
	- available_actions
- episode context:
	- history_summary
	- episode_summary
	- reward_signal
- terminal info:
	- done
	- reward
	- info

## Deterministic Task Suite

Task definitions are in `tasks.py`.

1. `obvious_sensor_fault` (easy)
	 Goal: identify clearly healthy readings and obvious non-actionable anomalies.
	 Typical expected behavior: choose Ignore or Sensor Error when readings are stable and within operational patterns.

2. `sensor_drift_recalibration` (medium)
	 Goal: detect gradual drift before it escalates.
	 Typical expected behavior: choose Recalibrate Sensor when trend data indicates persistent offset from baseline.

3. `cascading_failure_escalation` (hard)
	 Goal: distinguish recoverable drift from imminent failure.
	 Typical expected behavior: escalate to Emergency Shutdown only when progression indicates credible near-term fault.

## Grading and Reward Design

Grading logic is implemented in `graders.py` and task progression in `server/environment.py`.

- deterministic expected actions per sample
- partial credit on intermediate decisions
- penalties for unsafe ignore behavior
- penalties for over-escalation
- loop penalty for repeated non-progress actions
- normalized reward and task score clamped to the 0.0 to 1.0 range

## Baseline Inference Compliance

Baseline runner is `inference.py`.

Required environment variables:

- API_BASE_URL
- MODEL_NAME
- HF_TOKEN or OPENAI_API_KEY

Structured stdout format:

- [START] task=... env=... model=...
- [STEP] step=... action=... reward=... done=... error=...
- [END] success=... steps=... score=... rewards=...

## Baseline Scores

Latest baseline run output from `inference.py`:

- obvious_sensor_fault score: 0.333
- sensor_drift_recalibration score: 0.075
- cascading_failure_escalation score: 0.042
- overall benchmark score: 0.150

## Quick Start

```bash
pip install -e .
```

## Validate

```bash
./.venv/bin/openenv validate
```

## Full Local Submission Rehearsal

```bash
./scripts/pre_submit_check.sh
```

## Run Locally

```bash
uvicorn server.app:app --host 0.0.0.0 --port 8000
```

## Docker

```bash
docker build -t industrial-iot-alert-triage .
docker run -p 8000:8000 industrial-iot-alert-triage
```

## Baseline Inference

Root script: `inference.py`

Required environment variables:

- API_BASE_URL
- MODEL_NAME
- HF_TOKEN or OPENAI_API_KEY

Structured logs:

- [START]
- [STEP]
- [END]
