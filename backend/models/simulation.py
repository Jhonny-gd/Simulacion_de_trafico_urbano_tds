from enum import Enum

from pydantic import BaseModel, Field


class SimulationState(str, Enum):
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"


class TrafficLightState(str, Enum):
    RED = "red"
    YELLOW = "yellow"
    GREEN = "green"


class VehicleType(str, Enum):
    CAR = "car"
    BUS = "bus"
    TRUCK = "truck"
    MOTORCYCLE = "motorcycle"
    EMERGENCY = "emergency"


class VehicleDirection(str, Enum):
    NORTH = "north"
    SOUTH = "south"
    EAST = "east"
    WEST = "west"
    STRAIGHT = "straight"
    LEFT = "left"
    RIGHT = "right"


class VehicleSignal(str, Enum):
    NONE = "none"
    LEFT = "left"
    RIGHT = "right"
    HAZARD = "hazard"


class RouteControl(str, Enum):
    DEFAULT = "default"
    SHORTEST = "shortest"
    LESS_CONGESTED = "less_congested"
    MANUAL = "manual"


class SimulationConfig(BaseModel):
    conteo_vehiculos: int = Field(default=0, ge=0)
    densidad_trafico: float = Field(default=0.0, ge=0.0)
    velocidad_promedio: float = Field(default=0.0, ge=0.0)
    flujo_vehicular: float = Field(default=0.0, ge=0.0)
    nivel_congestion: float = Field(default=0.0, ge=0.0, le=100.0)
    estado_semaforo: TrafficLightState = TrafficLightState.RED
    tiempo_luz_verde: int = Field(default=30, ge=1)
    tiempo_luz_roja: int = Field(default=30, ge=1)
    modo_automatico_semaforo: bool = True
    control_manual_semaforo: TrafficLightState | None = None
    tipo_vehiculo: VehicleType = VehicleType.CAR
    direccion_vehiculo: VehicleDirection = VehicleDirection.STRAIGHT
    cambio_velocidad_individual: float = Field(default=0.0)
    senales_vehiculo: VehicleSignal = VehicleSignal.NONE
    control_rutas: RouteControl = RouteControl.DEFAULT


class SimulationStatus(BaseModel):
    estado_simulacion: SimulationState
    configuracion: SimulationConfig


class ControlResponse(BaseModel):
    estado_simulacion: SimulationState
    message: str
