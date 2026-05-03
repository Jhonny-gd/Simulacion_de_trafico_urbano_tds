from __future__ import annotations

import math
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import requests
from controller import Supervisor


class TrafficSimulationManager:
    """Sincroniza Webots con FastAPI sin detener la simulacion si el backend falla."""

    API_BASE_URL = "http://127.0.0.1:8000"
    CONFIG_ENDPOINT = f"{API_BASE_URL}/simulation/config"
    STATUS_ENDPOINT = f"{API_BASE_URL}/simulation/status"

    REQUEST_TIMEOUT_SECONDS = 0.35
    CONFIG_POLL_INTERVAL_SECONDS = 1.0
    STATUS_PUSH_INTERVAL_SECONDS = 1.0
    ROAD_AREA_M2 = 25000.0
    MANAGED_VEHICLE_DEFS = ("VEH_01",)
    SUMO_WORLD_OFFSET = (105.0, 105.0)
    ROUTE_REACHED_DISTANCE = 0.8
    STOP_ZONE_DISTANCE = 30.0
    STOP_LOOKAHEAD_DISTANCE = 62.0
    STOP_POINT_RADIUS = 14.0
    INTERSECTION_CLEAR_RADIUS = 18.0
    INTERSECTION_ENTRY_DISTANCE = 8.0
    SAFETY_DISTANCE = 13.0
    HEAVY_VEHICLE_SAFETY_DISTANCE = 24.0
    INITIAL_STOP_CLEARANCE = 34.0
    INITIAL_VEHICLE_CLEARANCE = 22.0
    INITIAL_MIN_SEGMENT_LENGTH = 36.0
    INITIAL_DEPARTURE_OFFSETS = (12.0, 22.0, 32.0, 44.0, 56.0)
    VEHICLE_TYPE_NAMES = (
        "bmwx5",
        "rangeroversportsvr",
        "truck",
        "bussimple",
        "motorbikesimple",
        "lincolnmkz",
        "toyotaprius",
        "teslamodel3",
        "citroenczero",
    )

    VEHICLE_KEYWORDS = (
        "vehicle",
        "bmw",
        "truck",
        "motorcycle",
        "taxi",
        "sedan",
        "rangeroversportsvr",
        "bussimple",
        "motorbikesimple",
        "lincolnmkz",
    )
    NON_VEHICLE_KEYWORDS = (
        "carwash",
        "bus stop",
        "busstop",
        "shelter",
        "house",
        "building",
        "tower",
        "station",
        "shop",
        "office",
        "traffic light",
        "trafficlight",
        "traffic cone",
        "crossroad",
        "road",
        "sign",
        "tree",
        "barrel",
        "stone",
    )

    CONFIG_KEYS = (
        "densidad_trafico",
        "velocidad_promedio",
        "tiempo_luz_verde",
        "tiempo_luz_roja",
        "estado_semaforo",
        "fase_semaforo",
        "modo_automatico_semaforo",
        "tipo_vehiculo",
        "direccion_vehiculo",
        "cambio_velocidad_individual",
        "vehiculo_seleccionado",
        "senales_vehiculo",
        "control_rutas",
        "zona_semaforo",
        "velocidad_global",
        "velocidad_maxima_coche",
        "velocidad_maxima_camion",
        "velocidad_maxima_autobus",
        "velocidad_maxima_moto",
    )

    def __init__(self) -> None:
        self.supervisor = Supervisor()
        self.timestep = int(self.supervisor.getBasicTimeStep())
        self.root = self.supervisor.getRoot()
        self.children_field = self.root.getField("children")

        self.vehicle_nodes = []
        self.traffic_light_nodes = []
        self.vehicle_initial_states: list[dict[str, Any]] = []
        self.lane_paths: dict[str, list[list[tuple[float, float]]]] = {}
        self.internal_lane_paths: dict[str, list[tuple[float, float]]] = {}
        self.connection_vias: dict[tuple[str, str], str] = {}
        self.route_paths: list[list[tuple[float, float]]] = []
        self.traffic_stop_points: list[tuple[float, float]] = []
        self.vehicle_route_states: list[dict[str, Any]] = []
        self.vehicles_aligned_on_start = False

        self.last_config_poll = 0.0
        self.last_status_push = 0.0
        self.backend_available = False
        self.last_backend_error = ""
        self.last_logged_backend_state: bool | None = None
        self.simulation_state = "stopped"
        self.last_logged_simulation_state: str | None = None
        self.last_logged_vehicle_count: int | None = None
        self.last_motion_log_time = 0.0
        self.last_no_motion_log_time = 0.0
        self.control_event_id = 0
        self.reset_event_id = 0
        self.handled_reset_event_id = 0

        self.config: dict[str, Any] = {
            "densidad_trafico": 0.0,
            "velocidad_promedio": 70.0,
            "tiempo_luz_verde": 30,
            "tiempo_luz_roja": 30,
            "estado_semaforo": "red",
            "fase_semaforo": "north_south",
            "modo_automatico_semaforo": True,
            "tipo_vehiculo": "sedan",
            "direccion_vehiculo": "straight",
            "cambio_velocidad_individual": 70.0,
            "vehiculo_seleccionado": "veh_01",
            "senales_vehiculo": {
                "luces": False,
                "direccional": False,
                "bocina": False,
                "emergencia": False,
            },
            "control_rutas": "principal",
            "zona_semaforo": "Interseccion central",
            "velocidad_global": 70,
            "velocidad_maxima_coche": 120,
            "velocidad_maxima_camion": 90,
            "velocidad_maxima_autobus": 100,
            "velocidad_maxima_moto": 120,
        }

        self.current_light_state = self.normalize_light_state(self.config["estado_semaforo"])
        self.current_traffic_phase = self.normalize_traffic_phase(self.config["fase_semaforo"])
        self.last_light_switch = self.supervisor.getTime()
        self.last_motion_time = self.supervisor.getTime()

        self.load_sumo_routes()
        self.refresh_scene_nodes()
        self.capture_initial_vehicle_states()
        print("[TrafficSimulationManager] Controller iniciado.")

    def run(self) -> None:
        while self.supervisor.step(self.timestep) != -1:
            now = time.monotonic()

            if now - self.last_config_poll >= self.CONFIG_POLL_INTERVAL_SECONDS:
                self.fetch_config()
                self.fetch_control_state()
                self.last_config_poll = now

            self.refresh_scene_nodes()
            should_move_vehicles = self.apply_simulation_control()
            self.update_traffic_light_logic()

            if should_move_vehicles:
                self.apply_vehicle_speed()
                self.update_vehicle_motion()

            if now - self.last_status_push >= self.STATUS_PUSH_INTERVAL_SECONDS:
                self.send_status()
                self.last_status_push = now

    def fetch_config(self) -> None:
        try:
            response = requests.get(self.CONFIG_ENDPOINT, timeout=self.REQUEST_TIMEOUT_SECONDS)
            response.raise_for_status()
            backend_config = response.json()

            for key in self.CONFIG_KEYS:
                if key in backend_config:
                    self.config[key] = backend_config[key]

            self.backend_available = True
            self.last_backend_error = ""
            self.log_backend_state()
            print("[TrafficSimulationManager] Config recibida desde FastAPI.")
        except requests.RequestException as exc:
            self.backend_available = False
            self.last_backend_error = str(exc)
            self.log_backend_state()

    def fetch_control_state(self) -> None:
        try:
            response = requests.get(self.STATUS_ENDPOINT, timeout=self.REQUEST_TIMEOUT_SECONDS)
            response.raise_for_status()
            status = response.json()

            self.simulation_state = str(
                status.get("estado_simulacion") or status.get("estado") or self.simulation_state
            ).lower()
            self.control_event_id = int(status.get("control_event_id") or self.control_event_id)
            self.reset_event_id = int(status.get("reset_event_id") or self.reset_event_id)

            status_config = status.get("configuracion") or {}
            for key in self.CONFIG_KEYS:
                if key in status_config:
                    self.config[key] = status_config[key]

            self.backend_available = True
            self.last_backend_error = ""
            self.log_backend_state()
            self.log_simulation_state()
            print(f"[TrafficSimulationManager] Estado de control recibido: {self.simulation_state}.")
        except requests.RequestException as exc:
            self.backend_available = False
            self.last_backend_error = str(exc)
            self.log_backend_state()

    def send_status(self) -> None:
        status_payload = self.build_status_payload()

        try:
            response = requests.post(
                self.STATUS_ENDPOINT,
                json=status_payload,
                timeout=self.REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            self.backend_available = True
            self.last_backend_error = ""
            self.log_backend_state()
            print(
                "[TrafficSimulationManager] Metricas enviadas: "
                f"{status_payload['vehiculos_activos']} vehiculos, "
                f"semaforo={status_payload['estado_semaforo']}, "
                f"congestion={status_payload['nivel_congestion']}%"
            )
        except requests.RequestException as exc:
            self.backend_available = False
            self.last_backend_error = str(exc)
            self.log_backend_state()

    def build_status_payload(self) -> dict[str, Any]:
        self.update_traffic_light_logic()

        vehicle_count = self.count_vehicles()
        traffic_light_count = self.count_traffic_lights()
        average_speed = self.calculate_average_speed()
        density = self.calculate_density(vehicle_count)
        flow = self.calculate_flow(vehicle_count, average_speed)
        congestion = self.calculate_congestion(vehicle_count, density, average_speed)

        return {
            "vehiculos_activos": vehicle_count,
            "conteo_vehiculos": vehicle_count,
            "densidad_trafico": density,
            "velocidad_promedio": average_speed,
            "flujo_vehicular": flow,
            "nivel_congestion": congestion,
            "estado_semaforo": self.current_light_state,
            "fase_semaforo": self.current_traffic_phase,
            "tiempo_simulacion": round(self.supervisor.getTime(), 1),
            "tiempo_restante_semaforo": self.calculate_traffic_light_remaining_time(),
            "semaforos_detectados": traffic_light_count,
            "zona_semaforo": str(self.config.get("zona_semaforo", "Interseccion central")),
        }

    def apply_simulation_control(self) -> bool:
        if self.reset_event_id != self.handled_reset_event_id:
            self.handled_reset_event_id = self.reset_event_id
            self.reset_simulation()

        if self.simulation_state == "running":
            return True

        self.pause_simulation_logic()
        return False

    def pause_simulation_logic(self) -> None:
        self.last_motion_time = self.supervisor.getTime()
        for vehicle in self.vehicle_nodes:
            self.apply_speed_to_vehicle(vehicle, 0.0)

    def reset_simulation(self) -> None:
        print("[TrafficSimulationManager] Reset recibido desde dashboard.")
        self.current_light_state = self.normalize_light_state(self.config.get("estado_semaforo", "red"))
        self.last_light_switch = self.supervisor.getTime()
        self.pause_simulation_logic()
        self.restore_vehicle_initial_states()
        self.reset_vehicle_route_states()

        try:
            self.supervisor.simulationResetPhysics()
            print("[TrafficSimulationManager] Fisica de Webots reiniciada.")
        except Exception as exc:
            print(f"[TrafficSimulationManager] No se pudo reiniciar fisica: {exc}")

    def count_vehicles(self) -> int:
        return len(self.vehicle_nodes)

    def count_traffic_lights(self) -> int:
        return len(self.traffic_light_nodes)

    def apply_vehicle_speed(self) -> None:
        speed_kmh = float(
            self.config.get("cambio_velocidad_individual")
            or self.config.get("velocidad_global")
            or self.config.get("velocidad_promedio")
            or 0.0
        )
        self.ensure_vehicle_route_states()

        for index, vehicle in enumerate(self.vehicle_nodes):
            if self.vehicle_should_stop_for_traffic(vehicle, index):
                self.apply_speed_to_vehicle(vehicle, 0.0)
            else:
                vehicle_speed_kmh = self.get_vehicle_speed_kmh(vehicle, speed_kmh)
                self.apply_speed_to_vehicle(vehicle, max(0.0, vehicle_speed_kmh / 3.6))

    def apply_speed_to_vehicle(self, vehicle, speed_mps: float) -> None:
        for field_name in ("speed", "maxSpeed", "cruisingSpeed", "targetSpeed"):
            self.set_field_value(vehicle, field_name, speed_mps)

        if speed_mps == 0.0:
            try:
                vehicle.setVelocity([0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
            except Exception:
                return

    def get_vehicle_speed_kmh(self, vehicle, base_speed_kmh: float) -> float:
        node_type = self.get_node_type_name(vehicle)

        if node_type in ("truck", "bussimple"):
            return min(base_speed_kmh * 0.28, 18.0)
        if node_type == "motorbikesimple":
            return min(base_speed_kmh * 0.45, 32.0)
        return min(base_speed_kmh * 0.4, 28.0)

    def update_vehicle_motion(self) -> None:
        now = self.supervisor.getTime()
        elapsed = max(0.0, now - self.last_motion_time)
        self.last_motion_time = now

        if elapsed <= 0.0:
            return

        speed_kmh = float(
            self.config.get("cambio_velocidad_individual")
            or self.config.get("velocidad_global")
            or self.config.get("velocidad_promedio")
            or 0.0
        )
        moved_count = 0

        if not self.vehicle_nodes and now - self.last_no_motion_log_time >= 2.0:
            self.last_no_motion_log_time = now
            print("[TrafficSimulationManager] No hay vehiculos detectados para mover.")
            return

        self.ensure_vehicle_route_states()

        for index, vehicle in enumerate(self.vehicle_nodes):
            if self.vehicle_should_stop_for_traffic(vehicle, index):
                self.apply_speed_to_vehicle(vehicle, 0.0)
                continue

            translation_field = vehicle.getField("translation")
            if translation_field is None:
                if now - self.last_no_motion_log_time >= 2.0:
                    self.last_no_motion_log_time = now
                    print(
                        "[TrafficSimulationManager] Vehiculo sin campo translation: "
                        f"{self.get_node_label(vehicle) or 'sin etiqueta'}."
                    )
                continue

            try:
                vehicle_speed_kmh = self.get_vehicle_speed_kmh(vehicle, speed_kmh)
                distance = max(0.0, vehicle_speed_kmh / 3.6) * elapsed
                moved = self.move_vehicle_on_route(vehicle, index, translation_field, distance)
                if not moved:
                    continue
                moved_count += 1
            except Exception as exc:
                if now - self.last_no_motion_log_time >= 2.0:
                    self.last_no_motion_log_time = now
                    print(f"[TrafficSimulationManager] No se pudo mover vehiculo: {exc}")
                continue

        if moved_count and now - self.last_motion_log_time >= 2.0:
            self.last_motion_log_time = now
            print(
                "[TrafficSimulationManager] Movimiento aplicado: "
                f"{moved_count} vehiculos, velocidad={speed_kmh} km/h, rutas=carriles SUMO."
            )

    def move_vehicle_on_route(self, vehicle, index: int, translation_field, distance: float) -> bool:
        if not self.route_paths:
            return False
        if distance <= 0.0:
            return False

        state = self.get_vehicle_route_state(index, vehicle)
        route = self.route_paths[state["route_index"]]
        if len(route) < 2:
            return False

        translation = list(translation_field.getSFVec3f())
        if not state["initialized"]:
            start_point = state.get("snap_point") or route[state["point_index"]]
            translation[0] = start_point[0]
            translation[1] = start_point[1]
            translation_field.setSFVec3f(translation)
            state["initialized"] = True

        remaining_distance = distance
        current_x = translation[0]
        current_y = translation[1]
        heading_x = 1.0
        heading_y = 0.0

        while remaining_distance > 0.0:
            next_index = (state["point_index"] + 1) % len(route)
            target_x, target_y = route[next_index]
            delta_x = target_x - current_x
            delta_y = target_y - current_y
            segment_length = math.hypot(delta_x, delta_y)

            if segment_length <= self.ROUTE_REACHED_DISTANCE:
                state["point_index"] = next_index
                continue

            heading_x = delta_x
            heading_y = delta_y
            if remaining_distance >= segment_length:
                current_x = target_x
                current_y = target_y
                state["point_index"] = next_index
                remaining_distance -= segment_length
                continue

            ratio = remaining_distance / segment_length
            current_x += delta_x * ratio
            current_y += delta_y * ratio
            remaining_distance = 0.0

        translation[0] = current_x
        translation[1] = current_y
        translation_field.setSFVec3f(translation)
        self.write_rotation_field(vehicle, "rotation", [0.0, 0.0, 1.0, math.atan2(heading_y, heading_x)])
        return True

    def get_vehicle_route_state(self, index: int, vehicle=None) -> dict[str, Any]:
        while len(self.vehicle_route_states) <= index:
            route_index, point_index, snap_point = self.find_nearest_route_position(
                vehicle,
                len(self.vehicle_route_states),
            )

            self.vehicle_route_states.append(
                {
                    "route_index": route_index,
                    "point_index": point_index,
                    "snap_point": snap_point,
                    "initialized": False,
                }
            )

        return self.vehicle_route_states[index]

    def find_nearest_route_position(self, vehicle, fallback_index: int) -> tuple[int, int, tuple[float, float] | None]:
        if not self.route_paths:
            return 0, 0, None

        translation = self.read_vec3_field(vehicle, "translation") if vehicle is not None else None
        if translation is None:
            route_index = fallback_index % len(self.route_paths)
            route = self.route_paths[route_index]
            point_index = (fallback_index * 3) % max(1, len(route) - 1)
            return route_index, point_index, None

        vehicle_point = (translation[0], translation[1])
        initial_heading = self.get_vehicle_heading_vector(vehicle)
        best_route_index = fallback_index % len(self.route_paths)
        best_point_index = 0
        best_snap_point = None
        best_score = float("inf")

        for route_index, route in enumerate(self.route_paths):
            for point_index in range(len(route) - 1):
                segment_start = route[point_index]
                segment_end = route[point_index + 1]
                projection = self.project_point_to_segment(vehicle_point, segment_start, segment_end)
                if projection is None:
                    continue

                snap_point, distance, segment_heading = projection
                heading_penalty = self.calculate_heading_penalty(initial_heading, segment_heading)
                score = distance + heading_penalty

                if score < best_score:
                    best_score = score
                    best_route_index = route_index
                    best_point_index = point_index
                    best_snap_point = snap_point

        return best_route_index, best_point_index, best_snap_point

    def get_vehicle_heading_vector(self, vehicle) -> tuple[float, float] | None:
        rotation = self.read_rotation_field(vehicle, "rotation")
        if not rotation or len(rotation) < 4:
            return None

        angle = rotation[3]
        if rotation[2] < 0:
            angle = -angle
        return math.cos(angle), math.sin(angle)

    def calculate_heading_penalty(
        self,
        initial_heading: tuple[float, float] | None,
        segment_heading: tuple[float, float],
    ) -> float:
        if initial_heading is None:
            return 0.0

        dot_product = (
            initial_heading[0] * segment_heading[0]
            + initial_heading[1] * segment_heading[1]
        )
        return max(0.0, 1.0 - dot_product) * 8.0

    def ensure_vehicle_route_states(self) -> None:
        if not self.route_paths:
            if self.last_no_motion_log_time == 0.0:
                print("[TrafficSimulationManager] No hay rutas SUMO cargadas para los vehiculos.")
            return

        for index in range(len(self.vehicle_nodes)):
            self.get_vehicle_route_state(index, self.vehicle_nodes[index])

    def reset_vehicle_route_states(self) -> None:
        for state in self.vehicle_route_states:
            state["initialized"] = self.vehicles_aligned_on_start
            state["snap_point"] = None

    def load_sumo_routes(self) -> None:
        net_path = self.get_world_asset_path("city_net", "sumo.net.xml")
        route_path = self.get_world_asset_path("city_net", "sumo.rou.xml")

        if not net_path.exists() or not route_path.exists():
            print("[TrafficSimulationManager] Red SUMO no encontrada; movimiento por carriles desactivado.")
            return

        try:
            self.lane_paths = self.load_sumo_lane_paths(net_path)
            self.internal_lane_paths = self.load_sumo_internal_lane_paths(net_path)
            self.connection_vias = self.load_sumo_connection_vias(net_path)
            self.traffic_stop_points = self.load_sumo_stop_points(net_path)
            self.route_paths = self.load_sumo_route_paths(route_path)
            print(
                "[TrafficSimulationManager] Rutas SUMO cargadas: "
                f"{len(self.route_paths)} rutas, {len(self.traffic_stop_points)} cruces."
            )
        except Exception as exc:
            self.lane_paths = {}
            self.internal_lane_paths = {}
            self.connection_vias = {}
            self.route_paths = []
            self.traffic_stop_points = []
            print(f"[TrafficSimulationManager] No se pudieron cargar rutas SUMO: {exc}")

    def get_world_asset_path(self, *parts: str) -> Path:
        controller_dir = Path(__file__).resolve().parent
        return controller_dir.parents[1] / "worlds" / Path(*parts)

    def load_sumo_lane_paths(self, net_path: Path) -> dict[str, list[list[tuple[float, float]]]]:
        tree = ET.parse(net_path)
        root = tree.getroot()
        lane_paths: dict[str, list[list[tuple[float, float]]]] = {}

        for edge in root.findall("edge"):
            edge_id = edge.attrib.get("id")
            if not edge_id or edge.attrib.get("function") == "internal":
                continue

            paths = []
            for lane in edge.findall("lane"):
                shape = lane.attrib.get("shape")
                if not shape:
                    continue
                points = self.parse_sumo_shape(shape)
                if len(points) >= 2:
                    paths.append(points)

            if paths:
                lane_paths[edge_id] = paths

        return lane_paths

    def load_sumo_internal_lane_paths(self, net_path: Path) -> dict[str, list[tuple[float, float]]]:
        tree = ET.parse(net_path)
        root = tree.getroot()
        internal_paths: dict[str, list[tuple[float, float]]] = {}

        for edge in root.findall("edge"):
            if edge.attrib.get("function") != "internal":
                continue

            for lane in edge.findall("lane"):
                lane_id = lane.attrib.get("id")
                shape = lane.attrib.get("shape")
                if not lane_id or not shape:
                    continue

                points = self.parse_sumo_shape(shape)
                if len(points) >= 2:
                    internal_paths[lane_id] = points

        return internal_paths

    def load_sumo_connection_vias(self, net_path: Path) -> dict[tuple[str, str], str]:
        tree = ET.parse(net_path)
        root = tree.getroot()
        vias: dict[tuple[str, str], str] = {}

        for connection in root.findall("connection"):
            from_edge = connection.attrib.get("from")
            to_edge = connection.attrib.get("to")
            via = connection.attrib.get("via")
            if not from_edge or not to_edge or not via:
                continue

            key = (from_edge, to_edge)
            if key not in vias or connection.attrib.get("state") == "M":
                vias[key] = via

        return vias

    def load_sumo_stop_points(self, net_path: Path) -> list[tuple[float, float]]:
        tree = ET.parse(net_path)
        root = tree.getroot()
        stop_points = []
        offset_x, offset_y = self.SUMO_WORLD_OFFSET

        for junction in root.findall("junction"):
            junction_id = str(junction.attrib.get("id", ""))
            if junction_id.startswith(":") or junction.attrib.get("type") == "internal":
                continue

            x_value = junction.attrib.get("x")
            y_value = junction.attrib.get("y")
            if x_value is None or y_value is None:
                continue

            stop_points.append((float(x_value) - offset_x, float(y_value) - offset_y))

        return stop_points

    def load_sumo_route_paths(self, route_path: Path) -> list[list[tuple[float, float]]]:
        tree = ET.parse(route_path)
        root = tree.getroot()
        route_paths = []

        for vehicle_index, vehicle in enumerate(root.findall("vehicle")):
            route = vehicle.find("route")
            if route is None:
                continue

            edge_ids = str(route.attrib.get("edges", "")).split()
            points: list[tuple[float, float]] = []
            previous_edge_id = None

            for edge_id in edge_ids:
                if previous_edge_id is not None:
                    via_id = self.connection_vias.get((previous_edge_id, edge_id))
                    via_path = self.internal_lane_paths.get(via_id or "")
                    if via_path:
                        points = self.extend_route_points(points, via_path)

                lane_options = self.lane_paths.get(edge_id)
                if not lane_options:
                    previous_edge_id = edge_id
                    continue
                lane_path = lane_options[vehicle_index % len(lane_options)]
                points = self.extend_route_points(points, lane_path)
                previous_edge_id = edge_id

            if len(points) >= 2:
                route_paths.append(points)

        return route_paths

    def parse_sumo_shape(self, shape: str) -> list[tuple[float, float]]:
        points = []
        offset_x, offset_y = self.SUMO_WORLD_OFFSET

        for point in shape.split():
            x_value, y_value = point.split(",")
            points.append((float(x_value) - offset_x, float(y_value) - offset_y))

        return points

    def extend_route_points(
        self,
        current_points: list[tuple[float, float]],
        next_points: list[tuple[float, float]],
    ) -> list[tuple[float, float]]:
        if not current_points:
            return list(next_points)

        points_to_add = list(next_points)
        if self.distance_between(current_points[-1], points_to_add[0]) < 0.5:
            points_to_add = points_to_add[1:]
        elif self.distance_between(current_points[-1], points_to_add[0]) > 24.0:
            return current_points

        return current_points + points_to_add

    def distance_between(self, first: tuple[float, float], second: tuple[float, float]) -> float:
        return math.hypot(first[0] - second[0], first[1] - second[1])

    def update_traffic_light_logic(self) -> None:
        previous_state = self.current_light_state
        previous_phase = self.current_traffic_phase

        if self.config.get("modo_automatico_semaforo", True):
            self.update_automatic_traffic_light_state()
        else:
            manual_state = self.config.get("control_manual_semaforo") or self.config.get("estado_semaforo", "red")
            requested_state = self.normalize_light_state(manual_state)
            self.current_light_state = requested_state
            requested_phase = self.normalize_traffic_phase(self.config.get("fase_semaforo", self.current_traffic_phase))
            self.current_traffic_phase = requested_phase

        if self.current_light_state != previous_state:
            self.last_light_switch = self.supervisor.getTime()
            print(f"[TrafficSimulationManager] Semaforo actualizado: {self.current_light_state}.")

        if self.current_traffic_phase != previous_phase:
            self.last_light_switch = self.supervisor.getTime()
            print(f"[TrafficSimulationManager] Fase de semaforo: {self.current_traffic_phase}.")

        for index, traffic_light in enumerate(self.traffic_light_nodes):
            self.apply_traffic_light_fields(traffic_light, index)

    def calculate_flow(self, vehicle_count: int, average_speed: float) -> float:
        return round(vehicle_count * average_speed, 3)

    def calculate_congestion(self, vehicle_count: int, density: float, average_speed: float) -> float:
        if vehicle_count == 0:
            return 0.0

        configured_density = float(self.config.get("densidad_trafico") or density)
        density_component = min(max(configured_density, density) * 100.0, 100.0)
        speed_component = max(0.0, 100.0 - average_speed * 10.0)
        red_light_component = 9.0 if self.config.get("modo_automatico_semaforo", True) else 18.0
        if self.current_light_state == "green" and not self.config.get("modo_automatico_semaforo", True):
            red_light_component = 0.0

        return round(min(100.0, (density_component * 0.45) + (speed_component * 0.4) + red_light_component), 2)

    def refresh_scene_nodes(self) -> None:
        vehicles = []
        traffic_lights = []

        for node in self.iter_scene_nodes():
            node_label = self.get_node_label(node)

            if self.is_traffic_light(node_label):
                traffic_lights.append(node)
            elif self.is_vehicle_node(node, node_label):
                self.add_unique_node(vehicles, node)

        for vehicle_def in self.MANAGED_VEHICLE_DEFS:
            explicit_vehicle = self.supervisor.getFromDef(vehicle_def)
            if explicit_vehicle is not None:
                self.add_unique_node(vehicles, explicit_vehicle)

        self.vehicle_nodes = vehicles
        self.traffic_light_nodes = traffic_lights
        self.align_vehicles_to_initial_routes()
        self.capture_initial_vehicle_states()
        self.log_vehicle_detection()

    def add_unique_node(self, nodes: list[Any], node) -> None:
        node_label = self.get_node_label(node)
        for existing_node in nodes:
            if self.get_node_label(existing_node) == node_label:
                return
        nodes.append(node)

    def capture_initial_vehicle_states(self) -> None:
        while len(self.vehicle_initial_states) < len(self.vehicle_nodes):
            vehicle = self.vehicle_nodes[len(self.vehicle_initial_states)]
            translation = self.read_vec3_field(vehicle, "translation")
            rotation = self.read_rotation_field(vehicle, "rotation")
            self.vehicle_initial_states.append(
                {
                    "translation": translation,
                    "rotation": rotation,
                }
            )

    def align_vehicles_to_initial_routes(self) -> None:
        if self.vehicles_aligned_on_start or not self.route_paths or not self.vehicle_nodes:
            return

        occupied_points: list[tuple[float, float]] = []
        self.vehicle_route_states = []
        self.vehicle_initial_states = []

        for index, vehicle in enumerate(self.vehicle_nodes):
            route_index, point_index, start_point = self.find_initial_route_slot(index, occupied_points)
            route = self.route_paths[route_index]
            heading = self.get_route_heading(route, point_index)
            translation = self.read_vec3_field(vehicle, "translation") or [start_point[0], start_point[1], 0.4]

            translation[0] = start_point[0]
            translation[1] = start_point[1]
            self.write_vec3_field(vehicle, "translation", translation)
            self.write_rotation_field(vehicle, "rotation", [0.0, 0.0, 1.0, math.atan2(heading[1], heading[0])])
            self.apply_speed_to_vehicle(vehicle, 0.0)

            self.vehicle_route_states.append(
                {
                    "route_index": route_index,
                    "point_index": point_index,
                    "snap_point": start_point,
                    "initialized": True,
                }
            )
            occupied_points.append(start_point)

        self.vehicles_aligned_on_start = True
        print(
            "[TrafficSimulationManager] Vehiculos alineados en carriles SUMO: "
            f"{len(self.vehicle_nodes)} vehiculos."
        )

    def find_initial_route_slot(
        self,
        vehicle_index: int,
        occupied_points: list[tuple[float, float]],
    ) -> tuple[int, int, tuple[float, float]]:
        route_count = len(self.route_paths)
        start_route_index = (vehicle_index * 3) % route_count

        for route_offset in range(route_count):
            route_index = (start_route_index + route_offset) % route_count
            route = self.route_paths[route_index]
            slot = self.find_departure_slot_on_route(route, occupied_points)
            if slot is not None:
                point_index, candidate = slot
                return route_index, point_index, candidate

        route_index = vehicle_index % route_count
        route = self.route_paths[route_index]
        point_index, point = self.find_longest_route_segment_midpoint(route)
        return route_index, point_index, point

    def find_departure_slot_on_route(
        self,
        route: list[tuple[float, float]],
        occupied_points: list[tuple[float, float]],
    ) -> tuple[int, tuple[float, float]] | None:
        if len(route) < 2:
            return None

        for point_index in range(len(route) - 1):
            segment_start = route[point_index]
            segment_end = route[point_index + 1]
            segment_length = self.distance_between(segment_start, segment_end)
            if segment_length < self.INITIAL_MIN_SEGMENT_LENGTH:
                continue

            heading = (
                (segment_end[0] - segment_start[0]) / segment_length,
                (segment_end[1] - segment_start[1]) / segment_length,
            )

            for offset in self.INITIAL_DEPARTURE_OFFSETS:
                if offset >= segment_length - 4.0:
                    continue

                candidate = (
                    segment_start[0] + heading[0] * offset,
                    segment_start[1] + heading[1] * offset,
                )

                if self.distance_to_nearest_point(candidate, self.traffic_stop_points) < self.INITIAL_STOP_CLEARANCE:
                    continue
                if self.distance_to_nearest_point(candidate, occupied_points) < self.INITIAL_VEHICLE_CLEARANCE:
                    continue

                return point_index, candidate

        return None

    def find_longest_route_segment_midpoint(
        self,
        route: list[tuple[float, float]],
    ) -> tuple[int, tuple[float, float]]:
        best_index = 0
        best_length = -1.0

        for point_index in range(len(route) - 1):
            segment_length = self.distance_between(route[point_index], route[point_index + 1])
            if segment_length > best_length:
                best_index = point_index
                best_length = segment_length

        segment_start = route[best_index]
        segment_end = route[min(best_index + 1, len(route) - 1)]
        midpoint = (
            segment_start[0] + (segment_end[0] - segment_start[0]) * 0.5,
            segment_start[1] + (segment_end[1] - segment_start[1]) * 0.5,
        )
        return best_index, midpoint

    def distance_to_nearest_point(
        self,
        point: tuple[float, float],
        points: list[tuple[float, float]],
    ) -> float:
        if not points:
            return 9999.0
        return min(self.distance_between(point, other_point) for other_point in points)

    def get_route_heading(self, route: list[tuple[float, float]], point_index: int) -> tuple[float, float]:
        next_index = min(point_index + 1, len(route) - 1)
        current_point = route[point_index]
        next_point = route[next_index]
        delta_x = next_point[0] - current_point[0]
        delta_y = next_point[1] - current_point[1]
        length = math.hypot(delta_x, delta_y)
        if length <= 0.01:
            return 1.0, 0.0
        return delta_x / length, delta_y / length

    def restore_vehicle_initial_states(self) -> None:
        for index, vehicle in enumerate(self.vehicle_nodes):
            if index >= len(self.vehicle_initial_states):
                continue

            initial_state = self.vehicle_initial_states[index]
            self.write_vec3_field(vehicle, "translation", initial_state.get("translation"))
            self.write_rotation_field(vehicle, "rotation", initial_state.get("rotation"))
            self.apply_speed_to_vehicle(vehicle, 0.0)

    def read_vec3_field(self, node, field_name: str) -> list[float] | None:
        field = node.getField(field_name)
        if field is None:
            return None

        try:
            return list(field.getSFVec3f())
        except Exception:
            return None

    def read_rotation_field(self, node, field_name: str) -> list[float] | None:
        field = node.getField(field_name)
        if field is None:
            return None

        try:
            return list(field.getSFRotation())
        except Exception:
            return None

    def write_vec3_field(self, node, field_name: str, value: list[float] | None) -> None:
        if value is None:
            return

        field = node.getField(field_name)
        if field is None:
            return

        try:
            field.setSFVec3f(value)
        except Exception:
            return

    def write_rotation_field(self, node, field_name: str, value: list[float] | None) -> None:
        if value is None:
            return

        field = node.getField(field_name)
        if field is None:
            return

        try:
            field.setSFRotation(value)
        except Exception:
            return

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

    def get_node_type_name(self, node) -> str:
        try:
            return str(node.getTypeName()).lower()
        except Exception:
            return ""

    def is_vehicle_node(self, node, node_label: str) -> bool:
        if not node_label:
            return False
        if any(keyword in node_label for keyword in self.NON_VEHICLE_KEYWORDS):
            return False
        if self.get_node_type_name(node) in self.VEHICLE_TYPE_NAMES:
            return True
        return any(keyword in node_label for keyword in self.VEHICLE_KEYWORDS)

    def is_traffic_light(self, node_label: str) -> bool:
        normalized_label = node_label.replace(" ", "")
        return "trafficlight" in normalized_label or "traffic light" in node_label

    def calculate_density(self, vehicle_count: int) -> float:
        scene_density = vehicle_count / self.ROAD_AREA_M2
        configured_density = float(self.config.get("densidad_trafico") or 0.0)
        return round(max(scene_density, configured_density), 6)

    def calculate_average_speed(self) -> float:
        speeds = []

        for vehicle in self.vehicle_nodes:
            try:
                velocity = vehicle.getVelocity()
                linear_speed = math.sqrt(velocity[0] ** 2 + velocity[1] ** 2 + velocity[2] ** 2)
                speeds.append(linear_speed)
            except Exception:
                continue

        if speeds:
            average_speed = sum(speeds) / len(speeds)
            if average_speed > 0.01:
                return round(average_speed, 3)

        configured_speed_kmh = float(
            self.config.get("cambio_velocidad_individual")
            or self.config.get("velocidad_global")
            or self.config.get("velocidad_promedio")
            or 0.0
        )
        if self.simulation_state != "running":
            configured_speed_kmh = 0.0
        return round(configured_speed_kmh / 3.6, 3)

    def update_automatic_traffic_light_state(self) -> None:
        now = self.supervisor.getTime()
        green_time = max(1.0, float(self.config.get("tiempo_luz_verde", 30)))
        red_time = max(1.0, float(self.config.get("tiempo_luz_roja", 30)))
        elapsed = now - self.last_light_switch

        self.current_light_state = "green"

        if self.current_traffic_phase == "north_south":
            active_duration = green_time
            next_phase = "east_west"
        else:
            active_duration = red_time
            next_phase = "north_south"

        if elapsed >= active_duration:
            self.current_traffic_phase = next_phase

    def calculate_traffic_light_remaining_time(self) -> float:
        now = self.supervisor.getTime()
        elapsed = now - self.last_light_switch

        if self.config.get("modo_automatico_semaforo", True):
            if self.current_traffic_phase == "north_south":
                duration = max(1.0, float(self.config.get("tiempo_luz_verde", 30)))
            else:
                duration = max(1.0, float(self.config.get("tiempo_luz_roja", 30)))
        elif self.current_light_state == "green":
            duration = max(1.0, float(self.config.get("tiempo_luz_verde", 30)))
        elif self.current_light_state == "red":
            duration = max(1.0, float(self.config.get("tiempo_luz_roja", 30)))
        else:
            duration = 5.0

        return round(max(0.0, duration - elapsed), 1)

    def apply_traffic_light_fields(self, traffic_light, index: int = 0) -> None:
        state = self.get_traffic_light_state_for_phase(traffic_light, index)
        self.set_field_value(traffic_light, "greenTime", float(self.config.get("tiempo_luz_verde", 30)))
        self.set_field_value(traffic_light, "redTime", float(self.config.get("tiempo_luz_roja", 30)))
        self.set_field_value(traffic_light, "startGreen", state == "green")
        self.set_field_value(traffic_light, "state", state)

    def get_traffic_light_state_for_phase(self, traffic_light, index: int) -> str:
        if not self.config.get("modo_automatico_semaforo", True):
            return self.current_light_state

        traffic_light_phase = self.get_node_phase(traffic_light, index)
        return "green" if traffic_light_phase == self.current_traffic_phase else "red"

    def vehicle_should_stop_for_traffic(self, vehicle, index: int) -> bool:
        return self.vehicle_should_stop_for_safe_distance(vehicle, index) or self.vehicle_should_stop_for_red_light(vehicle, index)

    def vehicle_should_stop_for_red_light(self, vehicle, index: int) -> bool:
        stop_info = self.get_next_stop_info(index, vehicle)
        if stop_info is None:
            return False

        stop_distance, _ = stop_info
        if stop_distance > self.STOP_ZONE_DISTANCE:
            return False

        if not self.config.get("modo_automatico_semaforo", True):
            return self.current_light_state != "green"

        route_phase = self.get_vehicle_route_phase(index)
        if route_phase:
            return route_phase != self.current_traffic_phase

        return self.get_node_phase(vehicle, index) != self.current_traffic_phase

    def vehicle_should_stop_for_occupied_intersection(self, vehicle, index: int) -> bool:
        stop_info = self.get_next_stop_info(index, vehicle)
        if stop_info is None:
            return False

        stop_distance, stop_point = stop_info
        if stop_distance <= self.INTERSECTION_ENTRY_DISTANCE or stop_distance > self.STOP_ZONE_DISTANCE:
            return False

        for other_index, other_vehicle in enumerate(self.vehicle_nodes):
            if other_index == index:
                continue

            other_translation = self.read_vec3_field(other_vehicle, "translation")
            if other_translation is None:
                continue

            other_point = (other_translation[0], other_translation[1])
            if self.distance_between(other_point, stop_point) <= self.INTERSECTION_CLEAR_RADIUS:
                return True

        return False

    def vehicle_should_stop_for_safe_distance(self, vehicle, index: int) -> bool:
        translation = self.read_vec3_field(vehicle, "translation")
        if translation is None:
            return False

        heading = self.get_current_route_heading(index)
        if heading is None:
            return False

        current_point = (translation[0], translation[1])
        safety_distance = self.get_vehicle_safety_distance(vehicle)
        vehicle_state = self.get_vehicle_route_state(index, vehicle)

        for other_index, other_vehicle in enumerate(self.vehicle_nodes):
            if other_index == index:
                continue

            other_state = self.get_vehicle_route_state(other_index, other_vehicle)
            if other_state["route_index"] != vehicle_state["route_index"]:
                continue

            other_translation = self.read_vec3_field(other_vehicle, "translation")
            if other_translation is None:
                continue

            other_point = (other_translation[0], other_translation[1])
            distance = self.distance_between(current_point, other_point)
            if distance > safety_distance:
                continue

            relative_x = other_point[0] - current_point[0]
            relative_y = other_point[1] - current_point[1]
            forward_distance = (relative_x * heading[0]) + (relative_y * heading[1])
            if 0.0 < forward_distance <= safety_distance:
                return True

        return False

    def get_vehicle_safety_distance(self, vehicle) -> float:
        node_type = self.get_node_type_name(vehicle)
        if node_type in ("truck", "bussimple"):
            return self.HEAVY_VEHICLE_SAFETY_DISTANCE
        return self.SAFETY_DISTANCE

    def is_vehicle_near_next_stop(self, index: int, vehicle) -> bool:
        stop_info = self.get_next_stop_info(index, vehicle)
        if stop_info is None:
            return False

        stop_distance, _ = stop_info
        return stop_distance <= self.STOP_ZONE_DISTANCE

    def get_next_stop_info(self, index: int, vehicle) -> tuple[float, tuple[float, float]] | None:
        if not self.traffic_stop_points or not self.route_paths:
            return None

        translation = self.read_vec3_field(vehicle, "translation")
        if translation is None:
            return None

        current_point = (translation[0], translation[1])
        return self.get_distance_and_point_to_next_stop(index, current_point)

    def distance_to_next_stop_point(self, index: int, current_point: tuple[float, float]) -> float | None:
        stop_info = self.get_distance_and_point_to_next_stop(index, current_point)
        if stop_info is None:
            return None
        return stop_info[0]

    def get_distance_and_point_to_next_stop(
        self,
        index: int,
        current_point: tuple[float, float],
    ) -> tuple[float, tuple[float, float]] | None:
        state = self.get_vehicle_route_state(index)
        route = self.route_paths[state["route_index"]]
        if len(route) < 2:
            return None

        best_distance: float | None = None
        best_stop_point: tuple[float, float] | None = None
        traveled = 0.0
        segment_start = current_point
        point_index = state["point_index"]

        for _ in range(len(route)):
            next_index = (point_index + 1) % len(route)
            segment_end = route[next_index]
            segment_length = self.distance_between(segment_start, segment_end)

            if segment_length > 0.01:
                for stop_point in self.traffic_stop_points:
                    stop_distance = self.distance_to_point_on_segment(segment_start, segment_end, stop_point)
                    if stop_distance is None:
                        continue

                    path_distance = traveled + stop_distance
                    if best_distance is None or path_distance < best_distance:
                        best_distance = path_distance
                        best_stop_point = stop_point

                traveled += segment_length
                if traveled > self.STOP_LOOKAHEAD_DISTANCE:
                    break

            point_index = next_index
            segment_start = segment_end

        if best_distance is None or best_stop_point is None:
            return None
        return best_distance, best_stop_point

    def distance_to_point_on_segment(
        self,
        segment_start: tuple[float, float],
        segment_end: tuple[float, float],
        point: tuple[float, float],
    ) -> float | None:
        start_x, start_y = segment_start
        end_x, end_y = segment_end
        point_x, point_y = point
        delta_x = end_x - start_x
        delta_y = end_y - start_y
        segment_length_squared = (delta_x * delta_x) + (delta_y * delta_y)

        if segment_length_squared <= 0.0001:
            return None

        projection = ((point_x - start_x) * delta_x + (point_y - start_y) * delta_y) / segment_length_squared
        if projection < 0.0 or projection > 1.0:
            return None

        closest_x = start_x + projection * delta_x
        closest_y = start_y + projection * delta_y
        lateral_distance = self.distance_between((closest_x, closest_y), point)
        if lateral_distance > self.STOP_POINT_RADIUS:
            return None

        return math.sqrt(segment_length_squared) * projection

    def project_point_to_segment(
        self,
        point: tuple[float, float],
        segment_start: tuple[float, float],
        segment_end: tuple[float, float],
    ) -> tuple[tuple[float, float], float, tuple[float, float]] | None:
        start_x, start_y = segment_start
        end_x, end_y = segment_end
        point_x, point_y = point
        delta_x = end_x - start_x
        delta_y = end_y - start_y
        segment_length_squared = (delta_x * delta_x) + (delta_y * delta_y)

        if segment_length_squared <= 0.0001:
            return None

        projection = ((point_x - start_x) * delta_x + (point_y - start_y) * delta_y) / segment_length_squared
        projection = min(1.0, max(0.0, projection))
        closest = (start_x + projection * delta_x, start_y + projection * delta_y)
        segment_length = math.sqrt(segment_length_squared)
        heading = (delta_x / segment_length, delta_y / segment_length)
        distance = self.distance_between(point, closest)
        return closest, distance, heading

    def get_vehicle_route_phase(self, index: int) -> str | None:
        heading = self.get_current_route_heading(index)
        if heading is not None:
            if abs(heading[1]) >= abs(heading[0]):
                return "north_south"
            return "east_west"

        return None

    def get_current_route_heading(self, index: int) -> tuple[float, float] | None:
        if not self.route_paths:
            return None

        state = self.get_vehicle_route_state(index)
        route = self.route_paths[state["route_index"]]
        if len(route) < 2:
            return None

        current_index = min(state["point_index"], len(route) - 1)
        next_index = (current_index + 1) % len(route)
        current_point = route[current_index]
        next_point = route[next_index]
        delta_x = next_point[0] - current_point[0]
        delta_y = next_point[1] - current_point[1]
        segment_length = math.hypot(delta_x, delta_y)
        if segment_length <= 0.001:
            return None

        return delta_x / segment_length, delta_y / segment_length

    def get_node_phase(self, node, index: int) -> str:
        rotation = self.read_rotation_field(node, "rotation")
        if rotation and len(rotation) >= 4 and abs(rotation[2]) > 0.5:
            angle = self.normalize_angle(rotation[3])
            if math.pi / 4 <= angle <= (3 * math.pi) / 4:
                return "north_south"
            return "east_west"

        return "north_south" if index % 2 == 0 else "east_west"

    def normalize_angle(self, angle: float) -> float:
        return abs((angle + math.pi) % (2 * math.pi) - math.pi)

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
            return

    def normalize_light_state(self, state: Any) -> str:
        value = str(state).lower()
        if value in ("green", "red", "yellow"):
            return value
        return "red"

    def normalize_traffic_phase(self, phase: Any) -> str:
        value = str(phase).lower()
        phase_map = {
            "norte_sur": "north_south",
            "north-south": "north_south",
            "ns": "north_south",
            "este_oeste": "east_west",
            "east-west": "east_west",
            "ew": "east_west",
        }
        normalized = phase_map.get(value, value)
        if normalized in ("north_south", "east_west"):
            return normalized
        return "north_south"

    def normalize_vehicle_direction(self, direction: Any) -> str:
        value = str(direction).lower()
        direction_map = {
            "recto": "straight",
            "straight": "straight",
            "left": "left",
            "izquierda": "left",
            "right": "right",
            "derecha": "right",
        }
        return direction_map.get(value, "straight")

    def log_backend_state(self) -> None:
        if self.last_logged_backend_state == self.backend_available:
            return

        self.last_logged_backend_state = self.backend_available
        if self.backend_available:
            print("[TrafficSimulationManager] Backend conectado.")
        else:
            print(f"[TrafficSimulationManager] Error de conexion con backend: {self.last_backend_error}")

    def log_simulation_state(self) -> None:
        if self.last_logged_simulation_state == self.simulation_state:
            return

        self.last_logged_simulation_state = self.simulation_state
        print(f"[TrafficSimulationManager] Estado dashboard -> Webots: {self.simulation_state}.")

    def log_vehicle_detection(self) -> None:
        vehicle_count = len(self.vehicle_nodes)
        if self.last_logged_vehicle_count == vehicle_count:
            return

        self.last_logged_vehicle_count = vehicle_count
        print(f"[TrafficSimulationManager] Vehiculos detectados en Scene Tree: {vehicle_count}.")


if __name__ == "__main__":
    TrafficSimulationManager().run()
