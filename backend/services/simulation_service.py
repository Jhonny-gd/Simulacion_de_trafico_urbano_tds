from models.simulation import ControlResponse, SimulationConfig, SimulationState, SimulationStatus


class SimulationService:
    """Gestiona el estado temporal de la simulacion hasta integrar Webots o una base de datos."""

    def __init__(self) -> None:
        self._state = SimulationState.STOPPED
        self._config = SimulationConfig()

    def get_status(self) -> SimulationStatus:
        return SimulationStatus(
            estado_simulacion=self._state,
            configuracion=self._config,
        )

    def get_config(self) -> SimulationConfig:
        return self._config

    def update_config(self, config: SimulationConfig) -> SimulationConfig:
        self._config = config
        return self._config

    def update_status(self, status_config: SimulationConfig) -> SimulationStatus:
        self._config = status_config
        return self.get_status()

    def start(self) -> ControlResponse:
        self._state = SimulationState.RUNNING
        return ControlResponse(
            estado_simulacion=self._state,
            message="Simulacion iniciada correctamente.",
        )

    def pause(self) -> ControlResponse:
        self._state = SimulationState.PAUSED
        return ControlResponse(
            estado_simulacion=self._state,
            message="Simulacion pausada correctamente.",
        )

    def reset(self) -> ControlResponse:
        self._state = SimulationState.STOPPED
        self._config = SimulationConfig()
        return ControlResponse(
            estado_simulacion=self._state,
            message="Simulacion reiniciada correctamente.",
        )


simulation_service = SimulationService()
