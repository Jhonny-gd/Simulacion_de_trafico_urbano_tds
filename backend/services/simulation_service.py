from time import monotonic

from models.simulation import (
    ControlResponse,
    SimulationConfig,
    SimulationMetrics,
    SimulationState,
    SimulationStatus,
)


def model_to_dict(model):
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


class SimulationService:
    """Mantiene en memoria el estado compartido entre Vue, FastAPI y Webots."""

    WEBOTS_TIMEOUT_SECONDS = 3.5

    def __init__(self) -> None:
        self._state = SimulationState.STOPPED
        self._config = SimulationConfig()
        self._metrics = SimulationMetrics()
        self._last_webots_update: float | None = None
        self._control_event_id = 0
        self._reset_event_id = 0

    def get_status(self) -> SimulationStatus:
        metrics = model_to_dict(self._metrics)
        return SimulationStatus(
            **metrics,
            estado=self._state,
            estado_simulacion=self._state,
            backend_conectado=True,
            webots_conectado=self._is_webots_connected(),
            control_event_id=self._control_event_id,
            reset_event_id=self._reset_event_id,
            configuracion=self._config,
        )

    def get_config(self) -> SimulationConfig:
        return self._config

    def update_config(self, config: SimulationConfig) -> SimulationConfig:
        config_data = model_to_dict(config)
        if config_data.get("modo_automatico_semaforo"):
            config_data["control_manual_semaforo"] = None
        else:
            config_data["control_manual_semaforo"] = (
                config_data.get("control_manual_semaforo")
                or config_data.get("estado_semaforo")
            )

        self._config = SimulationConfig(**config_data)
        return self._config

    def update_status(self, metrics: SimulationMetrics) -> SimulationStatus:
        metrics_data = model_to_dict(metrics)
        vehicle_count = max(
            int(metrics_data.get("vehiculos_activos") or 0),
            int(metrics_data.get("conteo_vehiculos") or 0),
        )
        metrics_data["vehiculos_activos"] = vehicle_count
        metrics_data["conteo_vehiculos"] = vehicle_count

        self._metrics = SimulationMetrics(**metrics_data)
        self._last_webots_update = monotonic()
        return self.get_status()

    def start(self) -> ControlResponse:
        self._state = SimulationState.RUNNING
        self._control_event_id += 1
        return self._control_response("Simulacion iniciada correctamente.")

    def pause(self) -> ControlResponse:
        self._state = SimulationState.PAUSED
        self._control_event_id += 1
        return self._control_response("Simulacion pausada correctamente.")

    def reset(self) -> ControlResponse:
        self._state = SimulationState.STOPPED
        self._config = SimulationConfig()
        self._metrics = SimulationMetrics()
        self._last_webots_update = None
        self._control_event_id += 1
        self._reset_event_id += 1
        return self._control_response("Simulacion reiniciada correctamente.")

    def _is_webots_connected(self) -> bool:
        if self._last_webots_update is None:
            return False
        return monotonic() - self._last_webots_update <= self.WEBOTS_TIMEOUT_SECONDS

    def _control_response(self, message: str) -> ControlResponse:
        return ControlResponse(
            estado=self._state,
            estado_simulacion=self._state,
            control_event_id=self._control_event_id,
            reset_event_id=self._reset_event_id,
            message=message,
        )


simulation_service = SimulationService()
