from fastapi import APIRouter, status

from models.simulation import ControlResponse, SimulationConfig, SimulationStatus
from services.simulation_service import simulation_service


router = APIRouter(prefix="/simulation", tags=["Simulation"])


@router.get("/status", response_model=SimulationStatus)
def get_simulation_status() -> SimulationStatus:
    return simulation_service.get_status()


@router.post("/status", response_model=SimulationStatus, status_code=status.HTTP_200_OK)
def update_simulation_status(status_config: SimulationConfig) -> SimulationStatus:
    return simulation_service.update_status(status_config)


@router.get("/config", response_model=SimulationConfig)
def get_simulation_config() -> SimulationConfig:
    return simulation_service.get_config()


@router.post("/config", response_model=SimulationConfig, status_code=status.HTTP_200_OK)
def update_simulation_config(config: SimulationConfig) -> SimulationConfig:
    return simulation_service.update_config(config)


@router.post("/control/start", response_model=ControlResponse)
def start_simulation() -> ControlResponse:
    return simulation_service.start()


@router.post("/control/pause", response_model=ControlResponse)
def pause_simulation() -> ControlResponse:
    return simulation_service.pause()


@router.post("/control/reset", response_model=ControlResponse)
def reset_simulation() -> ControlResponse:
    return simulation_service.reset()
