from __future__ import annotations

import inspect
import os

from openenv.core.env_server import create_app

from models import AlertAction, AlertObservation
from server.environment import IndustrialIotAlertTriageEnvironment


def build_app():
    def env_factory() -> IndustrialIotAlertTriageEnvironment:
        return IndustrialIotAlertTriageEnvironment(task_name=os.getenv("TASK_NAME"))

    try:
        first_param = next(iter(inspect.signature(create_app).parameters.values()))
        expects_instance = "Callable" not in str(first_param.annotation)
    except (StopIteration, TypeError, ValueError):
        expects_instance = False

    env_arg = env_factory() if expects_instance else env_factory

    try:
        return create_app(env_arg, AlertAction, AlertObservation, env_name="industrial_iot_alert_triage")
    except TypeError:
        return create_app(env_arg, AlertAction, AlertObservation)


app = build_app()


def main() -> None:
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))


if __name__ == "__main__":
    main()
