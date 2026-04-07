from __future__ import annotations

try:
    from openenv.core.client_types import StepResult
    from openenv.core.env_client import EnvClient
    from openenv.core.env_server.types import State
except ImportError:
    from openenv.core.client_types import StepResult
    from openenv.core.env_client import EnvClient
    from openenv.core.env_server.types import State

from models import AlertAction, AlertObservation, AlertState


class IndustrialIotAlertTriageEnv(EnvClient[AlertAction, AlertObservation, AlertState]):
    def _step_payload(self, action: AlertAction) -> dict:
        return action.model_dump()

    def _parse_result(self, payload: dict) -> StepResult[AlertObservation]:
        observation = AlertObservation(**payload["observation"])
        return StepResult(
            observation=observation,
            reward=payload.get("reward"),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: dict) -> AlertState:
        return AlertState(**payload)
