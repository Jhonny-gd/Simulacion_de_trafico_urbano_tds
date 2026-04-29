from __future__ import annotations

import math
import time
from typing import Any

import requests
from controller import Supervisor


class TrafficSimulationManager:
    """Controller Supervisor para sincronizar Webots con el backend FastAPI."""

    API_BASE_URL = "http://127.0.0.1:8000"
    CONFIG_ENDPOINT = f"{API_BASE_URL}/simulation/config"
    STATUS_ENDPOINT = f"{API_BASE_URL}/simulation/status"

    REQUEST_TIMEOUT_SECONDS = 0.25
    CONFIG_POLL_INTERVAL_SECONDS = 1.0
    METRICS_PUSH_INTERVAL_SECONDS = 1.0

    # Area aproximada de la zona vial de la escena en metros cuadrados.
    ROAD_AREA_M2 = 25000.0

    VEHICLE_KEYWORDS = (
        "vehicle",
        "car",
        "bmw",
        "bus",
        "truck",
        "motorcycle",
        "taxi",
    )
    NON_VEHICLE_KEYWORDS = (
        "traffic light",
        "traffic cone",
        "crossroad",
        "road",
        "sign",
        "tree",
        "barrel",
        "stone",
    )

    def __init__(self) -> None:
        self.supervisor = Supervisor()
        self.timestep = int(self.supervisor.getBasicTimeStep())
        self.root = self.supervisor.getRoot()
        self.children_field = self.root.getField("children")

        self.vehicle_nodes = []
        self.traffic_light_nodes = []

        self.last_config_poll = 0.0
        self.last_metrics_push = 0.0
        self.backend_available = False
        self.last_backend_error = ""

        # Valores locales seguros. Se usan cuando FastAPI no responde.
        self.config = {
            "conteo_vehiculos": 0,
            "densidad_trafico": 0.0,
            "velocidad_promedio": 0.0,
            "flujo_vehicular": 0.0,
            "nivel_congestion": 0.0,
            "estado_semaforo": "red",
            "tiempo_luz_verde": 30,
            "tiempo_luz_roja": 30,
            "modo_automatico_semaforo": True,
            "control_manual_semaforo": None,
            "tipo_vehiculo": "car",
            "direccion_vehiculo": "straight",
            "cambio_velocidad_individual": 0.0,
            "senales_vehiculo": "none",
            "control_rutas": "default",
        }

        self.current_light_state = self.config["estado_semaforo"]
        self.last_light_switch = self.supervisor.getTime()

        self.refresh_scene_nodes()

    def run(self) -> None:
        while self.supervisor.step(self.timestep) != -1:
            now = time.monotonic()

            if now - self.last_config_poll >= self.CONFIG_POLL_INTERVAL_SECONDS:
                self.fetch_backend_config()
                self.last_config_poll = now

            self.refresh_scene_nodes()
            metrics = self.calculate_metrics()
            self.config.update(metrics)

            self.control_traffic_lights()

            if now - self.last_metrics_push >= self.METRICS_PUSH_INTERVAL_SECONDS:
                self.push_metrics_to_backend()
                self.last_metrics_push = now

    def fetch_backend_config(self) -> None:
        """Lee configuracion desde FastAPI sin bloquear la simulacion."""
        try:
            response = requests.get(
                self.CONFIG_ENDPOINT,
                timeout=self.REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            backend_config = response.json()

            for key in (
                "densidad_trafico",
                "velocidad_promedio",
                "tiempo_luz_verde",
                "tiempo_luz_roja",
                "estado_semaforo",
                "modo_automatico_semaforo",
            ):
                if key in backend_config:
                    self.config[key] = backend_config[key]

            self.backend_available = True
            self.last_backend_error = ""
        except requests.RequestException as exc:
            self.backend_available = False
            self.last_backend_error = str(exc)

    def push_metrics_to_backend(self) -> None:
        """Envia metricas actuales; si falla, Webots continua con datos locales."""
        try:
            response = requests.post(
                self.STATUS_ENDPOINT,
                json=self.config,
                timeout=self.REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            self.backend_available = True
            self.last_backend_error = ""
        except requests.RequestException as exc:
            self.backend_available = False
            self.last_backend_error = str(exc)

    def refresh_scene_nodes(self) -> None:
        """Recorre la escena y clasifica nodos relevantes del Supervisor."""
        vehicles = []
        traffic_lights = []

        for node in self.iter_scene_nodes():
            node_label = self.get_node_label(node)

            if self.is_traffic_light(node_label):
                traffic_lights.append(node)
            elif self.is_vehicle(node_label):
                vehicles.append(node)

        self.vehicle_nodes = vehicles
        self.traffic_light_nodes = traffic_lights

    def iter_scene_nodes(self):
        root_count = self.children_field.getCount()
        for index in range(root_count):
            node = self.children_field.getMFNode(index)
            yield from self.walk_node(node)

    def walk_node(self, node):
        if node is None:
            return

        yield node

        children = node.getField("children")
        if children is None:
            return

        for index in range(children.getCount()):
            yield from self.walk_node(children.getMFNode(index))

    def get_node_label(self, node) -> str:
        parts = []

        for getter_name in ("getTypeName", "getDef"):
            try:
                value = getattr(node, getter_name)()
                if value:
                    parts.append(str(value))
            except Exception:
                pass

        name_field = node.getField("name")
        if name_field is not None:
            try:
                parts.append(str(name_field.getSFString()))
            except Exception:
                pass

        return " ".join(parts).lower()

    def is_vehicle(self, node_label: str) -> bool:
        if not node_label:
            return False

        if any(keyword in node_label for keyword in self.NON_VEHICLE_KEYWORDS):
            return False

        return any(keyword in node_label for keyword in self.VEHICLE_KEYWORDS)

    def is_traffic_light(self, node_label: str) -> bool:
        return "trafficlight" in node_label.replace(" ", "") or "traffic light" in node_label

    def calculate_metrics(self) -> dict[str, Any]:
        vehicle_count = self.count_real_vehicles()
        average_speed = self.calculate_average_speed()
        density = self.calculate_traffic_density(vehicle_count)
        flow = self.calculate_vehicle_flow(vehicle_count, average_speed)
        congestion = self.calculate_congestion(density, average_speed)

        return {
            "conteo_vehiculos": vehicle_count,
            "densidad_trafico": density,
            "velocidad_promedio": average_speed,
            "flujo_vehicular": flow,
            "nivel_congestion": congestion,
            "estado_semaforo": self.current_light_state,
        }

    def count_real_vehicles(self) -> int:
        return len(self.vehicle_nodes)

    def calculate_traffic_density(self, vehicle_count: int) -> float:
        return round(vehicle_count / self.ROAD_AREA_M2, 6)

    def calculate_average_speed(self) -> float:
        speeds = []

        for vehicle in self.vehicle_nodes:
            try:
                velocity = vehicle.getVelocity()
                linear_speed = math.sqrt(velocity[0] ** 2 + velocity[1] ** 2 + velocity[2] ** 2)
                speeds.append(linear_speed)
            except Exception:
                continue

        if not speeds:
            return 0.0

        return round(sum(speeds) / len(speeds), 3)

    def calculate_vehicle_flow(self, vehicle_count: int, average_speed: float) -> float:
        return round(vehicle_count * average_speed, 3)

    def calculate_congestion(self, density: float, average_speed: float) -> float:
        density_component = min(density * 1000.0, 100.0)
        speed_component = max(0.0, 100.0 - average_speed * 10.0)

        if self.count_real_vehicles() == 0:
            return 0.0

        return round((density_component * 0.6) + (speed_component * 0.4), 2)

    def control_traffic_lights(self) -> None:
        """Controla semaforos con modo automatico o estado manual del backend."""
        if self.config.get("modo_automatico_semaforo", True):
            self.update_automatic_traffic_light_state()
        else:
            requested_state = str(self.config.get("estado_semaforo", "red")).lower()
            self.current_light_state = self.normalize_light_state(requested_state)

        for traffic_light in self.traffic_light_nodes:
            self.apply_traffic_light_fields(traffic_light)

    def update_automatic_traffic_light_state(self) -> None:
        now = self.supervisor.getTime()
        green_time = max(1.0, float(self.config.get("tiempo_luz_verde", 30)))
        red_time = max(1.0, float(self.config.get("tiempo_luz_roja", 30)))
        elapsed = now - self.last_light_switch

        if self.current_light_state == "green" and elapsed >= green_time:
            self.current_light_state = "red"
            self.last_light_switch = now
        elif self.current_light_state != "green" and elapsed >= red_time:
            self.current_light_state = "green"
            self.last_light_switch = now

    def apply_traffic_light_fields(self, traffic_light) -> None:
        """Actualiza campos disponibles del PROTO sin asumir una implementacion unica."""
        self.set_field_value(traffic_light, "greenTime", float(self.config.get("tiempo_luz_verde", 30)))
        self.set_field_value(traffic_light, "redTime", float(self.config.get("tiempo_luz_roja", 30)))
        self.set_field_value(traffic_light, "startGreen", self.current_light_state == "green")

    def set_field_value(self, node, field_name: str, value: Any) -> None:
        field = node.getField(field_name)
        if field is None:
            return

        try:
            if isinstance(value, bool):
                field.setSFBool(value)
            elif isinstance(value, int):
                field.setSFInt32(value)
            elif isinstance(value, float):
                field.setSFFloat(value)
            elif isinstance(value, str):
                field.setSFString(value)
        except Exception:
            # Algunos campos de PROTO no son editables en runtime; se ignoran sin detener Webots.
            return

    def normalize_light_state(self, state: str) -> str:
        if state in ("green", "red", "yellow"):
            return state
        return "red"


if __name__ == "__main__":
    TrafficSimulationManager().run()
