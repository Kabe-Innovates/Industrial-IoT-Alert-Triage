---
title: Industrial Iot Alert Triage
emoji: ⚡
colorFrom: gray
colorTo: pink
sdk: docker
app_port: 8000
pinned: false
---

# Industrial IoT Alert Triage

Deterministic OpenEnv benchmark for industrial telemetry alert triage.

## Overview

This environment models Level 1 operations triage for telemetry alerts.
At each step, the agent chooses one action:

- 0: Ignore or sensor fault
- 1: Recalibrate sensor
- 2: Emergency shutdown

OpenEnv interface support:

- reset()
- step(action)
- state()

## Deterministic Tasks

- obvious_sensor_fault (easy)
- sensor_drift_recalibration (medium)
- cascading_failure_escalation (hard)

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

Root script: inference.py

Required environment variables:

- API_BASE_URL
- MODEL_NAME
- HF_TOKEN or OPENAI_API_KEY

Structured logs:

- [START]
- [STEP]
- [END]
