from time import sleep

from fastapi import APIRouter, Request, Response, status
from fastapi.responses import StreamingResponse

from models.simulation import ControlResponse, SimulationConfig, SimulationMetrics, SimulationStatus
from services.simulation_service import simulation_service


router = APIRouter(prefix="/simulation", tags=["Simulation"])


def stream_frames():
    last_frame = None
    while True:
        frame = simulation_service.get_stream_frame()
        if frame and frame != last_frame:
            last_frame = frame
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n"
                b"Cache-Control: no-cache\r\n\r\n"
                + frame
                + b"\r\n"
            )
        sleep(0.08)


@router.get("/status", response_model=SimulationStatus)
def get_simulation_status() -> SimulationStatus:
    return simulation_service.get_status()


@router.post("/status", response_model=SimulationStatus, status_code=status.HTTP_200_OK)
def update_simulation_status(metrics: SimulationMetrics) -> SimulationStatus:
    return simulation_service.update_status(metrics)


@router.post("/stream/frame", status_code=status.HTTP_204_NO_CONTENT)
async def update_stream_frame(request: Request) -> Response:
    simulation_service.update_stream_frame(await request.body())
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/stream.mjpg")
def get_stream() -> StreamingResponse:
    return StreamingResponse(
        stream_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame",
        headers={"Cache-Control": "no-store"},
    )


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
