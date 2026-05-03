from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, validator


class SimulationState(str, Enum):
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"


class TrafficLightState(str, Enum):
    RED = "red"
    YELLOW = "yellow"
    GREEN = "green"


class TrafficPhase(str, Enum):
    NORTH_SOUTH = "north_south"
    EAST_WEST = "east_west"


class VehicleType(str, Enum):
    SEDAN = "sedan"
    TRUCK = "camion"
    BUS = "autobus"
    MOTORCYCLE = "motocicleta"


class VehicleDirection(str, Enum):
    NORTH = "north"
    SOUTH = "south"
    EAST = "east"
    WEST = "west"
    STRAIGHT = "straight"
    LEFT = "left"
    RIGHT = "right"


class RouteControl(str, Enum):
    DEFAULT = "default"
    PRINCIPAL = "principal"
    SHORTEST = "shortest"
    LESS_CONGESTED = "less_congested"
    MANUAL = "manual"


class VehicleSignals(BaseModel):
    luces: bool = False
    direccional: bool = False
    bocina: bool = False
    emergencia: bool = False


class ApiModel(BaseModel):
    model_config = {
        "use_enum_values": True,
        "extra": "ignore",
        "validate_default": True,
    }


def normalize_light_state(value: Any) -> Any:
    if isinstance(value, str):
        return value.lower()
    return value


def normalize_traffic_phase(value: Any) -> Any:
    if not isinstance(value, str):
        return value

    phase_map = {
        "norte_sur": "north_south",
        "north-south": "north_south",
        "ns": "north_south",
        "este_oeste": "east_west",
        "east-west": "east_west",
        "ew": "east_west",
    }
    return phase_map.get(value.lower(), value.lower())


def normalize_vehicle_direction(value: Any) -> Any:
    if not isinstance(value, str):
        return value

    direction_map = {
        "recto": "straight",
        "izquierda": "left",
        "derecha": "right",
    }
    return direction_map.get(value.lower(), value.lower())


class SimulationConfig(ApiModel):
    densidad_trafico: float = Field(default=0.0, ge=0.0)
    velocidad_promedio: float = Field(default=70.0, ge=0.0)
    tiempo_luz_verde: int = Field(default=30, ge=1)
    tiempo_luz_roja: int = Field(default=30, ge=1)
    estado_semaforo: TrafficLightState = TrafficLightState.RED
    fase_semaforo: TrafficPhase = TrafficPhase.NORTH_SOUTH
    modo_automatico_semaforo: bool = True
    control_manual_semaforo: TrafficLightState | None = None
    tipo_vehiculo: VehicleType = VehicleType.SEDAN
    direccion_vehiculo: VehicleDirection = VehicleDirection.STRAIGHT
    cambio_velocidad_individual: float = Field(default=70.0, ge=0.0)
    vehiculo_seleccionado: str = Field(default="veh_01", min_length=1)
    velocidad_global: int = Field(default=70, ge=0, le=200)
    velocidad_maxima_coche: int = Field(default=120, ge=0, le=200)
    velocidad_maxima_camion: int = Field(default=90, ge=0, le=200)
    velocidad_maxima_autobus: int = Field(default=100, ge=0, le=200)
    velocidad_maxima_moto: int = Field(default=120, ge=0, le=200)
    senales_vehiculo: VehicleSignals = Field(default_factory=VehicleSignals)
    control_rutas: RouteControl = RouteControl.PRINCIPAL
    zona_semaforo: str = Field(default="Interseccion central", min_length=1)

    @validator("estado_semaforo", "control_manual_semaforo", pre=True)
    def normalize_lights(cls, value: Any) -> Any:
        return normalize_light_state(value)

    @validator("fase_semaforo", pre=True)
    def normalize_phase(cls, value: Any) -> Any:
        return normalize_traffic_phase(value)

    @validator("direccion_vehiculo", pre=True)
    def normalize_direction(cls, value: Any) -> Any:
        return normalize_vehicle_direction(value)

    @validator("senales_vehiculo", pre=True)
    def normalize_signals(cls, value: Any) -> Any:
        if isinstance(value, str):
            signals = VehicleSignals()
            if value in ("luces", "direccional", "bocina", "emergencia"):
                setattr(signals, value, True)
            return signals
        return value


class SimulationMetrics(ApiModel):
    vehiculos_activos: int = Field(default=0, ge=0)
    conteo_vehiculos: int = Field(default=0, ge=0)
    densidad_trafico: float = Field(default=0.0, ge=0.0)
    velocidad_promedio: float = Field(default=0.0, ge=0.0)
    flujo_vehicular: float = Field(default=0.0, ge=0.0)
    nivel_congestion: float = Field(default=0.0, ge=0.0, le=100.0)
    estado_semaforo: TrafficLightState = TrafficLightState.RED
    fase_semaforo: TrafficPhase = TrafficPhase.NORTH_SOUTH
    tiempo_simulacion: float = Field(default=0.0, ge=0.0)
    tiempo_restante_semaforo: float = Field(default=0.0, ge=0.0)
    semaforos_detectados: int = Field(default=0, ge=0)
    zona_semaforo: str = Field(default="Interseccion central", min_length=1)

    @validator("estado_semaforo", pre=True)
    def normalize_status_light(cls, value: Any) -> Any:
        return normalize_light_state(value)

    @validator("fase_semaforo", pre=True)
    def normalize_status_phase(cls, value: Any) -> Any:
        return normalize_traffic_phase(value)


class SimulationStatus(SimulationMetrics):
    estado: SimulationState
    estado_simulacion: SimulationState
    backend_conectado: bool = True
    webots_conectado: bool = False
    control_event_id: int = 0
    reset_event_id: int = 0
    configuracion: SimulationConfig


class ControlResponse(ApiModel):
    estado: SimulationState
    estado_simulacion: SimulationState
    control_event_id: int = 0
    reset_event_id: int = 0
    message: str
