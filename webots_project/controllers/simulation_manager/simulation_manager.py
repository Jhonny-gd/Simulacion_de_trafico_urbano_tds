import math
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree

import requests
from controller import Supervisor


BACKEND_URL = "http://127.0.0.1:8000/simulation"
YELLOW_TIME = 2.0
CLEAR_DISTANCE = 4.0
SAFE_GAP = 9.0
LIGHT_MATCH_DISTANCE = 8.0
CROSSWALK_SETBACK = 23.0
TRAFFIC_LIGHT_LOOKAHEAD = 58.0
STOP_LINE_BUFFER = 2.0
CROSSWALK_MATCH_DISTANCE = 11.0
CROSSWALK_LOOKAHEAD = 45.0
CROSSWALK_STOP_SETBACK = 8.5
INTERSECTION_MATCH_DISTANCE = 26.0
INTERSECTION_STOP_SETBACK = 10.0
SUMO_X_OFFSET = 105.11
SUMO_Y_OFFSET = 105.0
DEFAULT_SPEED = 8.0
CONFIG_POLL_INTERVAL = 0.5
KMH_TO_WEBOTS_SPEED = 0.12
STREAM_POST_INTERVAL = 0.16
STREAM_IMAGE_QUALITY = 95
MAP_FOCUS_HEIGHT = 55.0
MAP_FOCUS_BACK_DISTANCE = 28.0
ROUTE_CHANGE_SEARCH_RADIUS = 42.0
STRAIGHT_ANGLE_LIMIT = math.radians(32.0)
TURN_MIN_ANGLE = math.radians(28.0)
TURN_MAX_ANGLE = math.radians(150.0)
ROUTE_CONNECTION_DISTANCE = 16.0
ROUTE_CONNECTION_ANGLE = math.radians(80.0)
INTERSECTION_CONFLICT_RADIUS = 12.0
INTERSECTION_APPROACH_DISTANCE = 26.0
INTERSECTION_OCCUPIED_DISTANCE = 13.0
VIEWPOINT_ORIENTATION = [
    0.14435491317685756,
    0.8745652548154178,
    -0.4629225357566267,
    0.6849993669095598,
]

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SUMO_NET_FILE = PROJECT_ROOT / "worlds" / "city_net" / "sumo.net.xml"
SUMO_ROUTE_FILE = PROJECT_ROOT / "worlds" / "city_net" / "sumo.rou.xml"
STREAM_IMAGE_FILE = Path(__file__).with_name("dashboard_stream.jpg")

VEHICLE_TYPES = {
    "BmwX5",
    "MotorbikeSimple",
    "Bus",
    "Truck",
    "ToyotaPrius",
    "LincolnMKZ",
    "CitroenCZero",
    "RangeRoverSportSVR",
    "Scooter",
    "BusSimple",
    "ScooterSimple",
    "TruckSimple",
    "BmwX5Simple",
    "MercedesBenzSprinter",
}


@dataclass
class Route:
    name: str
    waypoints: list[tuple[float, float]]
    speed: float


@dataclass
class VehicleState:
    identifier: str
    node: object
    route: Route
    route_index: int
    segment_index: int
    segment_distance: float
    z: float
    length: float
    vehicle_type: str
    stopped: bool = False
    signal_fields: dict[str, list[object]] | None = None


@dataclass
class ControllerConfig:
    velocidad_global: float = 70.0
    velocidad_maxima_coche: float = 120.0
    velocidad_maxima_camion: float = 90.0
    velocidad_maxima_autobus: float = 100.0
    velocidad_maxima_moto: float = 120.0
    vehiculo_seleccionado: str = "veh_01"
    cambio_velocidad_individual: float = 70.0
    direccion_vehiculo: str = "straight"
    senales_vehiculo: dict[str, bool] | None = None
    map_focus_event_id: int = 0
    tiempo_luz_verde: float = 15.0
    tiempo_luz_roja: float = 15.0
    estado_semaforo: str = "red"
    fase_semaforo: str = "north_south"
    modo_automatico_semaforo: bool = True
    control_manual_semaforo: str | None = None

    @property
    def global_speed(self) -> float:
        return max(0.0, self.velocidad_global * KMH_TO_WEBOTS_SPEED)

    def max_speed_for(self, vehicle_type: str) -> float:
        limits = {
            "car": self.velocidad_maxima_coche,
            "truck": self.velocidad_maxima_camion,
            "bus": self.velocidad_maxima_autobus,
            "motorcycle": self.velocidad_maxima_moto,
        }
        return max(0.0, limits.get(vehicle_type, self.velocidad_global) * KMH_TO_WEBOTS_SPEED)

    def individual_speed(self) -> float:
        return max(0.0, self.cambio_velocidad_individual * KMH_TO_WEBOTS_SPEED)

    @property
    def signals(self) -> dict[str, bool]:
        defaults = {
            "luces": False,
            "direccional": False,
            "bocina": False,
            "emergencia": False,
        }
        return {**defaults, **(self.senales_vehiculo or {})}


@dataclass
class TrafficLightGroup:
    name: str
    x: float
    y: float


def lane_point(x: float, y: float) -> tuple[float, float]:
    return x - SUMO_X_OFFSET, y - SUMO_Y_OFFSET


def parse_shape(shape: str) -> list[tuple[float, float]]:
    points = []
    for raw_pair in shape.split():
        x_text, y_text = raw_pair.split(",")
        points.append(lane_point(float(x_text), float(y_text)))
    return points


def append_points(target: list[tuple[float, float]], points: list[tuple[float, float]]) -> None:
    for point in points:
        if not target or distance(target[-1], point) > 0.15:
            target.append(point)


def load_sumo_network() -> tuple[dict[str, list[tuple[float, float]]], list[TrafficLightGroup]]:
    tree = ElementTree.parse(SUMO_NET_FILE)
    root = tree.getroot()

    edges: dict[str, list[tuple[float, float]]] = {}
    for edge in root.findall("edge"):
        edge_id = edge.attrib.get("id", "")
        if not edge_id or edge_id.startswith(":"):
            continue

        lane = edge.find("lane")
        if lane is None or not lane.attrib.get("shape"):
            continue
        edges[edge_id] = parse_shape(lane.attrib["shape"])

    junctions = []
    for junction in root.findall("junction"):
        junction_id = junction.attrib.get("id", "")
        if junction_id.startswith(":"):
            continue
        if junction.attrib.get("type") not in {"priority", "traffic_light"}:
            continue
        x = float(junction.attrib.get("x", "0"))
        y = float(junction.attrib.get("y", "0"))
        junctions.append(TrafficLightGroup(f"Junction {junction_id}", *lane_point(x, y)))

    return edges, junctions


def load_sumo_routes(edge_shapes: dict[str, list[tuple[float, float]]]) -> list[Route]:
    tree = ElementTree.parse(SUMO_ROUTE_FILE)
    root = tree.getroot()
    routes = []

    for vehicle in root.findall("vehicle"):
        route_node = vehicle.find("route")
        if route_node is None:
            continue

        waypoints: list[tuple[float, float]] = []
        for edge_id in route_node.attrib.get("edges", "").split():
            shape = edge_shapes.get(edge_id)
            if shape:
                append_points(waypoints, shape)

        if len(waypoints) < 2:
            continue

        route_id = vehicle.attrib.get("id", str(len(routes)))
        routes.append(Route(f"sumo_route_{route_id}", waypoints, DEFAULT_SPEED))
        if len(routes) >= 80:
            break

    return routes


def fetch_controller_config(current_config: ControllerConfig) -> ControllerConfig:
    try:
        response = requests.get(f"{BACKEND_URL}/config", timeout=0.25)
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException:
        return current_config

    signals_payload = payload.get("senales_vehiculo", current_config.signals)
    if not isinstance(signals_payload, dict):
        signals_payload = current_config.signals

    return ControllerConfig(
        velocidad_global=float(payload.get("velocidad_global", current_config.velocidad_global) or 0.0),
        velocidad_maxima_coche=float(
            payload.get("velocidad_maxima_coche", current_config.velocidad_maxima_coche) or 0.0
        ),
        velocidad_maxima_camion=float(
            payload.get("velocidad_maxima_camion", current_config.velocidad_maxima_camion) or 0.0
        ),
        velocidad_maxima_autobus=float(
            payload.get("velocidad_maxima_autobus", current_config.velocidad_maxima_autobus) or 0.0
        ),
        velocidad_maxima_moto=float(
            payload.get("velocidad_maxima_moto", current_config.velocidad_maxima_moto) or 0.0
        ),
        vehiculo_seleccionado=str(
            payload.get("vehiculo_seleccionado", current_config.vehiculo_seleccionado) or "veh_01"
        ),
        cambio_velocidad_individual=float(
            payload.get("cambio_velocidad_individual", current_config.cambio_velocidad_individual) or 0.0
        ),
        direccion_vehiculo=str(
            payload.get("direccion_vehiculo", current_config.direccion_vehiculo) or "straight"
        ),
        senales_vehiculo={key: bool(value) for key, value in signals_payload.items()},
        map_focus_event_id=int(payload.get("map_focus_event_id", current_config.map_focus_event_id) or 0),
        tiempo_luz_verde=float(payload.get("tiempo_luz_verde", current_config.tiempo_luz_verde) or 15.0),
        tiempo_luz_roja=float(payload.get("tiempo_luz_roja", current_config.tiempo_luz_roja) or 15.0),
        estado_semaforo=str(payload.get("estado_semaforo", current_config.estado_semaforo) or "red"),
        fase_semaforo=str(payload.get("fase_semaforo", current_config.fase_semaforo) or "north_south"),
        modo_automatico_semaforo=bool(
            payload.get("modo_automatico_semaforo", current_config.modo_automatico_semaforo)
        ),
        control_manual_semaforo=payload.get(
            "control_manual_semaforo",
            current_config.control_manual_semaforo,
        ),
    )


def initialize_dashboard_stream() -> None:
    print("Stream Webots usando captura del Supervisor.")


def post_dashboard_frame(supervisor: Supervisor) -> None:
    try:
        supervisor.exportImage(str(STREAM_IMAGE_FILE), STREAM_IMAGE_QUALITY)
        frame = STREAM_IMAGE_FILE.read_bytes()
        requests.post(
            f"{BACKEND_URL}/stream/frame",
            data=frame,
            headers={"Content-Type": "image/jpeg"},
            timeout=0.15,
        )
    except Exception:
        pass


def effective_vehicle_speed(vehicle: VehicleState, controller_config: ControllerConfig) -> float:
    base_speed = min(controller_config.global_speed, controller_config.max_speed_for(vehicle.vehicle_type))
    if vehicle.identifier == controller_config.vehiculo_seleccionado:
        return min(controller_config.individual_speed(), controller_config.max_speed_for(vehicle.vehicle_type))
    return base_speed


def distance(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot(b[0] - a[0], b[1] - a[1])


def normalize_angle(angle: float) -> float:
    while angle > math.pi:
        angle -= math.tau
    while angle < -math.pi:
        angle += math.tau
    return angle


def route_heading(route: Route, segment_index_value: int) -> float:
    start = route.waypoints[segment_index_value]
    end = route.waypoints[segment_index_value + 1]
    return math.atan2(end[1] - start[1], end[0] - start[0])


def route_segment_count(route: Route) -> int:
    return max(len(route.waypoints) - 1, 0)


def segment_length(route: Route, index: int) -> float:
    start = route.waypoints[index]
    end = route.waypoints[index + 1]
    return max(distance(start, end), 0.001)


def interpolate(route: Route, index: int, segment_distance_value: float) -> tuple[float, float, float]:
    start = route.waypoints[index]
    end = route.waypoints[index + 1]
    length = segment_length(route, index)
    t = max(0.0, min(segment_distance_value / length, 1.0))
    x = start[0] + (end[0] - start[0]) * t
    y = start[1] + (end[1] - start[1]) * t
    yaw = route_heading(route, index)
    return x, y, yaw


def current_vehicle_pose(vehicle: VehicleState) -> tuple[float, float, float]:
    return interpolate(vehicle.route, vehicle.segment_index, vehicle.segment_distance)


def matches_direction(angle_delta: float, direction: str) -> bool:
    if direction == "left":
        return TURN_MIN_ANGLE <= angle_delta <= TURN_MAX_ANGLE
    if direction == "right":
        return -TURN_MAX_ANGLE <= angle_delta <= -TURN_MIN_ANGLE
    return abs(angle_delta) <= STRAIGHT_ANGLE_LIMIT


def route_direction_penalty(angle_delta: float, direction: str) -> float:
    if direction == "left":
        return abs(angle_delta - math.radians(82.0))
    if direction == "right":
        return abs(angle_delta + math.radians(82.0))
    return abs(angle_delta)


def find_route_for_direction(
    vehicle: VehicleState,
    routes: list[Route],
    direction: str,
) -> tuple[int, int, float] | None:
    direction = direction if direction in {"left", "right", "straight"} else "straight"
    current_x, current_y, current_yaw = current_vehicle_pose(vehicle)
    current_point = (current_x, current_y)
    best_candidate = None
    best_score = None

    for route_index, route in enumerate(routes):
        for segment_index_value in range(route_segment_count(route)):
            start = route.waypoints[segment_index_value]
            end = route.waypoints[segment_index_value + 1]
            projected_distance, lateral_error = projection_on_segment(start, end, current_point)
            if lateral_error > ROUTE_CHANGE_SEARCH_RADIUS:
                continue

            candidate_yaw = route_heading(route, segment_index_value)
            angle_delta = normalize_angle(candidate_yaw - current_yaw)
            if not matches_direction(angle_delta, direction):
                continue

            score = lateral_error + route_direction_penalty(angle_delta, direction) * 8.0
            if best_score is None or score < best_score:
                best_score = score
                best_candidate = (route_index, segment_index_value, projected_distance)

    return best_candidate


def apply_vehicle_direction(vehicle: VehicleState, routes: list[Route], direction: str) -> bool:
    candidate = find_route_for_direction(vehicle, routes, direction)
    if candidate is None:
        return False

    route_index, segment_index_value, projected_distance = candidate
    vehicle.route_index = route_index
    vehicle.route = routes[route_index]
    vehicle.segment_index = segment_index_value
    vehicle.segment_distance = min(projected_distance, segment_length(vehicle.route, segment_index_value) - 0.1)
    vehicle.stopped = False
    return True


def traffic_state_for_time(simulation_time: float, config: ControllerConfig) -> tuple[str, str, float]:
    green_time = max(float(config.tiempo_luz_verde), YELLOW_TIME + 1.0)
    red_time = max(float(config.tiempo_luz_roja), 1.0)

    if not config.modo_automatico_semaforo:
        active_light = config.control_manual_semaforo or config.estado_semaforo or "red"
        if active_light not in {"green", "yellow", "red"}:
            active_light = "red"
        active_phase = config.fase_semaforo if config.fase_semaforo in {"north_south", "east_west"} else "north_south"
        remaining = green_time if active_light == "green" else red_time
        return active_phase, active_light, remaining

    cycle_duration = (green_time + red_time) * 2.0
    cycle_time = simulation_time % cycle_duration
    north_south_duration = green_time + red_time
    active_phase = "north_south" if cycle_time < north_south_duration else "east_west"
    phase_time = cycle_time if active_phase == "north_south" else cycle_time - north_south_duration

    if phase_time < green_time:
        remaining = green_time - phase_time
        active_light = "yellow" if remaining <= YELLOW_TIME else "green"
    else:
        active_light = "red"
        remaining = north_south_duration - phase_time

    return active_phase, active_light, max(0.0, remaining)


def direction_phase(start: tuple[float, float], end: tuple[float, float]) -> str:
    dx = abs(end[0] - start[0])
    dy = abs(end[1] - start[1])
    return "east_west" if dx >= dy else "north_south"


def projection_on_segment(
    start: tuple[float, float],
    end: tuple[float, float],
    point: tuple[float, float],
) -> tuple[float, float]:
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    length_squared = dx * dx + dy * dy
    if length_squared <= 0.001:
        return 0.0, distance(start, point)

    t = ((point[0] - start[0]) * dx + (point[1] - start[1]) * dy) / length_squared
    t = max(0.0, min(t, 1.0))
    projected = (start[0] + dx * t, start[1] + dy * t)
    return math.sqrt(length_squared) * t, distance(projected, point)


def is_red_for_vehicle(route: Route, segment_index_value: int, active_phase: str, active_light: str) -> bool:
    start = route.waypoints[segment_index_value]
    end = route.waypoints[segment_index_value + 1]
    vehicle_phase = direction_phase(start, end)
    return vehicle_phase != active_phase or active_light != "green"


def distance_to_light_on_segment(
    route: Route,
    segment_index_value: int,
    segment_distance_value: float,
    light: TrafficLightGroup,
) -> float | None:
    start = route.waypoints[segment_index_value]
    end = route.waypoints[segment_index_value + 1]
    light_distance, light_error = projection_on_segment(start, end, (light.x, light.y))
    if light_error > LIGHT_MATCH_DISTANCE:
        return None

    remaining = light_distance - segment_distance_value
    if remaining < -CLEAR_DISTANCE or light_distance > segment_length(route, segment_index_value) + 0.5:
        return None
    return remaining


def collect_pedestrian_crossings(supervisor: Supervisor) -> list[TrafficLightGroup]:
    root = supervisor.getRoot()
    children = root.getField("children")
    crossings = []

    for index in range(children.getCount()):
        node = children.getMFNode(index)
        if not node or node.getTypeName() != "PedestrianCrossing":
            continue

        translation = node.getField("translation")
        if not translation:
            continue

        x, y, _ = translation.getSFVec3f()
        name_field = node.getField("name")
        name = name_field.getSFString() if name_field else f"pedestrian crossing {len(crossings) + 1}"
        crossings.append(TrafficLightGroup(name, x, y))

    return crossings


def stop_line_from_crosswalks(vehicle: VehicleState, crosswalks: list[TrafficLightGroup]) -> float | None:
    closest_stop_line = None
    start = vehicle.route.waypoints[vehicle.segment_index]
    end = vehicle.route.waypoints[vehicle.segment_index + 1]

    for crossing in crosswalks:
        crossing_distance, crossing_error = projection_on_segment(start, end, (crossing.x, crossing.y))
        if crossing_error > CROSSWALK_MATCH_DISTANCE:
            continue

        remaining = crossing_distance - vehicle.segment_distance
        if remaining < 0.0 or remaining > CROSSWALK_LOOKAHEAD:
            continue

        stop_line = crossing_distance - CROSSWALK_STOP_SETBACK - (vehicle.length / 2.0)
        if stop_line <= vehicle.segment_distance + 0.2:
            continue

        if closest_stop_line is None or stop_line < closest_stop_line:
            closest_stop_line = stop_line

    return closest_stop_line


def stop_line_before_intersection(
    vehicle: VehicleState,
    traffic_lights: list[TrafficLightGroup],
    crosswalks: list[TrafficLightGroup],
) -> float | None:
    segment_end = vehicle.route.waypoints[vehicle.segment_index + 1]
    landmarks = traffic_lights + crosswalks
    if not any(distance(segment_end, (landmark.x, landmark.y)) <= INTERSECTION_MATCH_DISTANCE for landmark in landmarks):
        return None

    current_length = segment_length(vehicle.route, vehicle.segment_index)
    stop_line = current_length - INTERSECTION_STOP_SETBACK - (vehicle.length / 2.0)
    if stop_line <= vehicle.segment_distance + 0.2:
        return None

    if stop_line - vehicle.segment_distance > TRAFFIC_LIGHT_LOOKAHEAD:
        return None

    return max(0.0, stop_line)


def stop_line_for_vehicle(
    vehicle: VehicleState,
    active_phase: str,
    active_light: str,
    traffic_lights: list[TrafficLightGroup],
    crosswalks: list[TrafficLightGroup],
) -> float | None:
    if not is_red_for_vehicle(vehicle.route, vehicle.segment_index, active_phase, active_light):
        return None

    crosswalk_stop_line = stop_line_from_crosswalks(vehicle, crosswalks)
    if crosswalk_stop_line is not None:
        return crosswalk_stop_line

    closest_stop_line = None
    for light in traffic_lights:
        remaining = distance_to_light_on_segment(
            vehicle.route,
            vehicle.segment_index,
            vehicle.segment_distance,
            light,
        )
        if remaining is None or remaining > TRAFFIC_LIGHT_LOOKAHEAD:
            continue

        start = vehicle.route.waypoints[vehicle.segment_index]
        end = vehicle.route.waypoints[vehicle.segment_index + 1]
        light_distance, _ = projection_on_segment(start, end, (light.x, light.y))
        stop_line_distance = CROSSWALK_SETBACK + STOP_LINE_BUFFER + (vehicle.length / 2.0)
        stop_line = max(0.0, light_distance - stop_line_distance)
        if stop_line <= vehicle.segment_distance + 0.2:
            continue

        if closest_stop_line is None or stop_line < closest_stop_line:
            closest_stop_line = stop_line

    if closest_stop_line is not None:
        return closest_stop_line

    return stop_line_before_intersection(vehicle, traffic_lights, crosswalks)


def should_stop_for_vehicle(vehicle: VehicleState, vehicles: list[VehicleState]) -> bool:
    vehicle_x, vehicle_y, vehicle_yaw = current_vehicle_pose(vehicle)
    vehicle_point = (vehicle_x, vehicle_y)

    for other in vehicles:
        if other is vehicle:
            continue

        if other.route.name == vehicle.route.name and other.segment_index == vehicle.segment_index:
            gap = other.segment_distance - vehicle.segment_distance
            if 0.0 < gap < SAFE_GAP:
                return True

        other_x, other_y, other_yaw = current_vehicle_pose(other)
        if distance(vehicle_point, (other_x, other_y)) > INTERSECTION_CONFLICT_RADIUS:
            continue

        if direction_phase(
            vehicle.route.waypoints[vehicle.segment_index],
            vehicle.route.waypoints[vehicle.segment_index + 1],
        ) == direction_phase(
            other.route.waypoints[other.segment_index],
            other.route.waypoints[other.segment_index + 1],
        ):
            continue

        relative_x = other_x - vehicle_x
        relative_y = other_y - vehicle_y
        vehicle_approaches_other = math.cos(vehicle_yaw) * relative_x + math.sin(vehicle_yaw) * relative_y > 0
        other_approaches_vehicle = math.cos(other_yaw) * -relative_x + math.sin(other_yaw) * -relative_y > 0
        if not vehicle_approaches_other or not other_approaches_vehicle:
            continue

        if vehicle.identifier > other.identifier:
            return True

    return False


def next_intersection_for_vehicle(
    vehicle: VehicleState,
    traffic_lights: list[TrafficLightGroup],
) -> tuple[TrafficLightGroup, float] | None:
    start = vehicle.route.waypoints[vehicle.segment_index]
    end = vehicle.route.waypoints[vehicle.segment_index + 1]
    best = None

    for light in traffic_lights:
        light_distance, light_error = projection_on_segment(start, end, (light.x, light.y))
        if light_error > LIGHT_MATCH_DISTANCE:
            continue

        remaining = light_distance - vehicle.segment_distance
        if remaining < 0.0 or remaining > INTERSECTION_APPROACH_DISTANCE:
            continue

        if best is None or remaining < best[1]:
            best = (light, remaining)

    return best


def should_wait_for_intersection(
    vehicle: VehicleState,
    vehicles: list[VehicleState],
    traffic_lights: list[TrafficLightGroup],
) -> bool:
    target = next_intersection_for_vehicle(vehicle, traffic_lights)
    if target is None:
        return False

    target_light, vehicle_remaining = target
    vehicle_phase = direction_phase(
        vehicle.route.waypoints[vehicle.segment_index],
        vehicle.route.waypoints[vehicle.segment_index + 1],
    )

    for other in vehicles:
        if other is vehicle:
            continue

        other_target = next_intersection_for_vehicle(other, traffic_lights)
        other_x, other_y, _ = current_vehicle_pose(other)
        other_near_target = distance((other_x, other_y), (target_light.x, target_light.y)) <= INTERSECTION_OCCUPIED_DISTANCE
        same_target = (
            other_target is not None
            and distance((other_target[0].x, other_target[0].y), (target_light.x, target_light.y)) <= INTERSECTION_OCCUPIED_DISTANCE
        )
        if not same_target and not other_near_target:
            continue

        other_phase = direction_phase(
            other.route.waypoints[other.segment_index],
            other.route.waypoints[other.segment_index + 1],
        )
        if other_phase == vehicle_phase:
            continue

        other_remaining = other_target[1] if other_target is not None else 0.0
        if other.identifier < vehicle.identifier or other_remaining < vehicle_remaining:
            return True

    return False


def assign_next_route(vehicle: VehicleState, routes: list[Route]) -> None:
    current_end = vehicle.route.waypoints[-1]
    current_heading = route_heading(vehicle.route, route_segment_count(vehicle.route) - 1)
    best_route_index = vehicle.route_index
    best_score = None

    for route_index, route in enumerate(routes):
        start = route.waypoints[0]
        start_heading = route_heading(route, 0)
        connection_distance = distance(current_end, start)
        if connection_distance > ROUTE_CONNECTION_DISTANCE:
            continue

        heading_delta = abs(normalize_angle(start_heading - current_heading))
        if heading_delta > ROUTE_CONNECTION_ANGLE:
            continue

        score = connection_distance + heading_delta * 5.0
        if best_score is None or score < best_score:
            best_score = score
            best_route_index = route_index

    vehicle.route_index = best_route_index
    vehicle.route = routes[vehicle.route_index]
    vehicle.segment_index = 0
    vehicle.segment_distance = 0.0


def advance_vehicle(vehicle: VehicleState, dt: float, routes: list[Route], speed: float) -> None:
    vehicle.segment_distance += speed * dt

    while vehicle.segment_index < route_segment_count(vehicle.route):
        current_length = segment_length(vehicle.route, vehicle.segment_index)
        if vehicle.segment_distance < current_length:
            return
        vehicle.segment_distance -= current_length
        vehicle.segment_index += 1

    assign_next_route(vehicle, routes)
    vehicle.segment_distance = 0.0


def advance_vehicle_until(
    vehicle: VehicleState,
    max_segment_distance: float,
    dt: float,
    routes: list[Route],
    speed: float,
) -> bool:
    next_distance = vehicle.segment_distance + speed * dt
    if next_distance >= max_segment_distance:
        vehicle.segment_distance = max_segment_distance
        return True

    advance_vehicle(vehicle, dt, routes, speed)
    return False


def apply_vehicle_transform(vehicle: VehicleState) -> None:
    x, y, yaw = interpolate(vehicle.route, vehicle.segment_index, vehicle.segment_distance)
    translation = vehicle.node.getField("translation")
    rotation = vehicle.node.getField("rotation")

    if translation:
        translation.setSFVec3f([x, y, vehicle.z])
    if rotation:
        rotation.setSFRotation([0, 0, 1, yaw])
    vehicle.node.resetPhysics()


def is_vehicle_node(node) -> bool:
    type_name = node.getTypeName()
    name_field = node.getField("name")
    node_name = name_field.getSFString().lower() if name_field else ""
    return type_name in VEHICLE_TYPES or "vehicle" in node_name or "motor" in node_name


def estimate_vehicle_length(node) -> float:
    type_name = node.getTypeName()
    if type_name in {"Truck", "TruckSimple", "Bus", "BusSimple", "MercedesBenzSprinter"}:
        return 17.0
    if type_name in {"MotorbikeSimple", "Scooter", "ScooterSimple"}:
        return 3.5
    return 5.2


def classify_vehicle(node) -> str:
    type_name = node.getTypeName()
    if type_name in {"Truck", "TruckSimple", "MercedesBenzSprinter"}:
        return "truck"
    if type_name in {"Bus", "BusSimple"}:
        return "bus"
    if type_name in {"MotorbikeSimple", "Scooter", "ScooterSimple"}:
        return "motorcycle"
    return "car"


def collect_vehicles(supervisor: Supervisor, routes: list[Route]) -> list[VehicleState]:
    root = supervisor.getRoot()
    children = root.getField("children")
    vehicles = []

    for index in range(children.getCount()):
        node = children.getMFNode(index)
        if not node or not is_vehicle_node(node):
            continue

        translation = node.getField("translation")
        if not translation:
            continue

        _, _, z = translation.getSFVec3f()
        route_index = len(vehicles) % len(routes)
        route = routes[route_index]
        identifier = f"veh_{len(vehicles) + 1:02d}"
        vehicles.append(
            VehicleState(
                identifier=identifier,
                node=node,
                route=route,
                route_index=route_index,
                segment_index=0,
                segment_distance=(len(vehicles) * 14.0) % max(total_route_length(route), 1.0),
                z=z,
                length=estimate_vehicle_length(node),
                vehicle_type=classify_vehicle(node),
            )
        )

    for vehicle in vehicles:
        normalize_vehicle_position(vehicle, routes)

    return vehicles


def total_route_length(route: Route) -> float:
    return sum(segment_length(route, index) for index in range(route_segment_count(route)))


def normalize_vehicle_position(vehicle: VehicleState, routes: list[Route]) -> None:
    while vehicle.segment_index < route_segment_count(vehicle.route):
        current_length = segment_length(vehicle.route, vehicle.segment_index)
        if vehicle.segment_distance < current_length:
            return
        vehicle.segment_distance -= current_length
        vehicle.segment_index += 1
    assign_next_route(vehicle, routes)


def count_stopped(vehicles: list[VehicleState]) -> int:
    return sum(1 for vehicle in vehicles if vehicle.stopped)


def is_visual_traffic_light_node(node) -> bool:
    type_name = node.getTypeName()
    name_field = node.getField("name")
    node_name = name_field.getSFString().lower() if name_field else ""
    return (
        type_name in {"GenericTrafficLight", "CrossRoadsTrafficLight"}
        or "traffic light" in node_name
    )


def collect_visual_traffic_lights(supervisor: Supervisor) -> list[object]:
    root = supervisor.getRoot()
    children = root.getField("children")
    lights = []

    for index in range(children.getCount()):
        node = children.getMFNode(index)
        if node and is_visual_traffic_light_node(node):
            lights.append(node)

    return lights


def set_string_field_if_available(node, field_name: str, value: str) -> None:
    field = node.getField(field_name)
    if not field:
        return

    try:
        field.setSFString(value)
    except Exception:
        pass


def set_float_field_if_available(node, field_name: str, value: float) -> None:
    field = node.getField(field_name)
    if not field:
        return

    try:
        field.setSFFloat(float(value))
    except Exception:
        pass


def visual_light_phase(node) -> str:
    translation = node.getField("translation")
    rotation = node.getField("rotation")
    if not translation:
        return "north_south"

    yaw = rotation.getSFRotation()[3] if rotation else 0.0
    return "east_west" if abs(math.cos(yaw)) >= abs(math.sin(yaw)) else "north_south"


def apply_visual_traffic_lights(
    visual_lights: list[object],
    active_phase: str,
    active_light: str,
    config: ControllerConfig,
) -> None:
    for node in visual_lights:
        node_phase = visual_light_phase(node)
        node_state = active_light if node_phase == active_phase else "red"
        set_string_field_if_available(node, "state", node_state)
        set_float_field_if_available(node, "greenTime", max(config.tiempo_luz_verde, 1.0))
        set_float_field_if_available(node, "redTime", max(config.tiempo_luz_roja, 1.0))


def selected_vehicle(vehicles: list[VehicleState], identifier: str) -> VehicleState | None:
    for vehicle in vehicles:
        if vehicle.identifier == identifier:
            return vehicle
    return vehicles[0] if vehicles else None


def collect_signal_fields(node) -> dict[str, list[object]]:
    candidates = {
        "luces": ["frontLights", "frontLight", "headlights", "headLights", "lights"],
        "direccional": ["indicator", "indicators", "turnSignals", "turnSignal"],
        "emergencia": ["hazardLights", "hazardLight", "emergencyLights"],
    }
    fields: dict[str, list[object]] = {}

    for signal, field_names in candidates.items():
        fields[signal] = []
        for field_name in field_names:
            field = node.getField(field_name)
            if field:
                fields[signal].append(field)

    return fields


def apply_signal_fields(vehicle: VehicleState, signals: dict[str, bool]) -> None:
    if vehicle.signal_fields is None:
        vehicle.signal_fields = collect_signal_fields(vehicle.node)

    for signal, fields in vehicle.signal_fields.items():
        value = bool(signals.get(signal, False))
        for field in fields:
            try:
                field.setSFBool(value)
            except Exception:
                pass


def signal_summary(signals: dict[str, bool]) -> str:
    labels = {
        "luces": "Luces",
        "direccional": "Direccional",
        "bocina": "Bocina",
        "emergencia": "Emergencia",
    }
    active = [label for key, label in labels.items() if signals.get(key)]
    return " | ".join(active) if active else "Sin senales"


def empty_signals() -> dict[str, bool]:
    return {
        "luces": False,
        "direccional": False,
        "bocina": False,
        "emergencia": False,
    }


def update_vehicle_overlay(supervisor: Supervisor, vehicle: VehicleState | None, config: ControllerConfig) -> None:
    if vehicle is None:
        supervisor.setLabel(10, "", 0.0, 0.0, 0.0, 0xFFFFFF, 1.0, "Arial")
        return

    signals = config.signals
    text = (
        f"{vehicle.identifier.upper()}  "
        f"{config.direccion_vehiculo.upper()}  "
        f"{config.cambio_velocidad_individual:.0f} km/h  "
        f"{signal_summary(signals)}"
    )
    color = 0xFF244F if signals.get("emergencia") else 0x12C8FF
    supervisor.setLabel(10, text, 0.02, 0.92, 0.065, color, 0.0, "Arial")


def focus_viewpoint_on_vehicle(supervisor: Supervisor, vehicle: VehicleState | None) -> bool:
    if vehicle is None:
        return False

    root = supervisor.getRoot()
    children = root.getField("children")
    viewpoint = None
    for index in range(children.getCount()):
        node = children.getMFNode(index)
        if node and node.getTypeName() == "Viewpoint":
            viewpoint = node
            break

    if viewpoint is None:
        return False

    x, y, yaw = current_vehicle_pose(vehicle)
    position = viewpoint.getField("position")
    orientation = viewpoint.getField("orientation")
    if position:
        position.setSFVec3f([
            x - math.cos(yaw) * MAP_FOCUS_BACK_DISTANCE,
            y - math.sin(yaw) * MAP_FOCUS_BACK_DISTANCE,
            vehicle.z + MAP_FOCUS_HEIGHT,
        ])
    if orientation:
        orientation.setSFRotation(VIEWPOINT_ORIENTATION)
    return True


def send_metrics(
    supervisor: Supervisor,
    vehicles: list[VehicleState],
    traffic_lights: list[TrafficLightGroup],
    active_phase: str,
    active_light: str,
    remaining_time: float,
    controller_config: ControllerConfig,
) -> None:
    vehicle_count = len(vehicles)
    stopped_count = count_stopped(vehicles)
    moving_speeds = [
        effective_vehicle_speed(vehicle, controller_config)
        for vehicle in vehicles
        if not vehicle.stopped
    ]
    average_speed = sum(moving_speeds) / len(moving_speeds) if moving_speeds else 0.0
    congestion = round((stopped_count / vehicle_count) * 100.0, 2) if vehicle_count else 0.0

    payload = {
        "vehiculos_activos": vehicle_count,
        "conteo_vehiculos": vehicle_count,
        "velocidad_promedio": round(average_speed, 2),
        "densidad_trafico": round(vehicle_count / max(len(traffic_lights), 1), 2),
        "flujo_vehicular": round(max(vehicle_count - stopped_count, 0) * average_speed, 2),
        "nivel_congestion": congestion,
        "tiempo_simulacion": supervisor.getTime(),
        "estado_semaforo": active_light,
        "fase_semaforo": active_phase,
        "tiempo_restante_semaforo": round(remaining_time, 2),
        "semaforos_detectados": len(traffic_lights),
        "zona_semaforo": "Red SUMO urbana",
    }

    try:
        requests.post(f"{BACKEND_URL}/status", json=payload, timeout=0.1)
    except requests.RequestException:
        pass


def iniciar_simulacion() -> None:
    edge_shapes, traffic_lights = load_sumo_network()
    routes = load_sumo_routes(edge_shapes)
    if not routes:
        raise RuntimeError("No se pudieron cargar rutas desde sumo.rou.xml")

    supervisor = Supervisor()
    time_step = int(supervisor.getBasicTimeStep())
    dt = time_step / 1000.0
    initialize_dashboard_stream()
    vehicles = collect_vehicles(supervisor, routes)
    visual_traffic_lights = collect_visual_traffic_lights(supervisor)
    pedestrian_crossings = collect_pedestrian_crossings(supervisor)
    controller_config = ControllerConfig()
    last_config_poll = -CONFIG_POLL_INTERVAL
    last_stream_post = -STREAM_POST_INTERVAL
    last_reported_speed = None
    last_reported_vehicle_config = None
    last_applied_direction_config = None
    last_map_focus_event_id = 0
    last_signal_config = None
    step_count = 0

    print(f"Controlador urbano SUMO iniciado con {len(vehicles)} vehiculos.")
    print(
        f"Rutas cargadas: {len(routes)} | Semaforos logicos: {len(traffic_lights)} | "
        f"Semaforos visuales: {len(visual_traffic_lights)} | "
        f"Pasos peatonales: {len(pedestrian_crossings)}"
    )

    while supervisor.step(time_step) != -1:
        step_count += 1
        simulation_time = supervisor.getTime()
        if simulation_time - last_stream_post >= STREAM_POST_INTERVAL:
            post_dashboard_frame(supervisor)
            last_stream_post = simulation_time

        if simulation_time - last_config_poll >= CONFIG_POLL_INTERVAL:
            controller_config = fetch_controller_config(controller_config)
            last_config_poll = simulation_time

        current_speed = controller_config.global_speed
        if controller_config.velocidad_global != last_reported_speed:
            print(
                f"Velocidad global recibida: {controller_config.velocidad_global:.0f} km/h "
                f"-> {current_speed:.2f} Webots"
            )
            last_reported_speed = controller_config.velocidad_global
        vehicle_config = (
            controller_config.vehiculo_seleccionado,
            controller_config.cambio_velocidad_individual,
            controller_config.direccion_vehiculo,
        )
        if vehicle_config != last_reported_vehicle_config:
            print(
                f"Vehiculo seleccionado: {controller_config.vehiculo_seleccionado} | "
                f"velocidad individual: {controller_config.cambio_velocidad_individual:.0f} km/h | "
                f"direccion: {controller_config.direccion_vehiculo}"
            )
            last_reported_vehicle_config = vehicle_config
        active_vehicle = selected_vehicle(vehicles, controller_config.vehiculo_seleccionado)
        direction_config = (
            controller_config.vehiculo_seleccionado,
            controller_config.direccion_vehiculo,
        )
        if active_vehicle and direction_config != last_applied_direction_config:
            if apply_vehicle_direction(active_vehicle, routes, controller_config.direccion_vehiculo):
                print(
                    f"Ruta aplicada a {active_vehicle.identifier}: "
                    f"{controller_config.direccion_vehiculo}"
                )
            else:
                print(
                    f"No se encontro ruta cercana para {active_vehicle.identifier}: "
                    f"{controller_config.direccion_vehiculo}"
                )
            last_applied_direction_config = direction_config
        signal_config = (
            controller_config.vehiculo_seleccionado,
            tuple(sorted(controller_config.signals.items())),
        )
        if active_vehicle:
            for vehicle in vehicles:
                if vehicle is not active_vehicle:
                    apply_signal_fields(vehicle, empty_signals())
            apply_signal_fields(active_vehicle, controller_config.signals)
            update_vehicle_overlay(supervisor, active_vehicle, controller_config)
        if signal_config != last_signal_config:
            print(
                f"Senales {controller_config.vehiculo_seleccionado}: "
                f"{signal_summary(controller_config.signals)}"
            )
            last_signal_config = signal_config
        if controller_config.map_focus_event_id != last_map_focus_event_id:
            if controller_config.map_focus_event_id > 0:
                if focus_viewpoint_on_vehicle(supervisor, active_vehicle):
                    print(f"Vista enfocada en {controller_config.vehiculo_seleccionado}")
                else:
                    print(f"No se pudo enfocar {controller_config.vehiculo_seleccionado}")
            last_map_focus_event_id = controller_config.map_focus_event_id
        active_phase, active_light, remaining_time = traffic_state_for_time(simulation_time, controller_config)
        apply_visual_traffic_lights(visual_traffic_lights, active_phase, active_light, controller_config)

        for vehicle in vehicles:
            vehicle_speed = effective_vehicle_speed(vehicle, controller_config)
            stop_line = stop_line_for_vehicle(
                vehicle,
                active_phase,
                active_light,
                traffic_lights,
                pedestrian_crossings,
            )
            stop_for_vehicle = should_stop_for_vehicle(vehicle, vehicles)
            wait_for_intersection = should_wait_for_intersection(vehicle, vehicles, traffic_lights)

            if stop_for_vehicle or wait_for_intersection:
                vehicle.stopped = True
            elif stop_line is not None:
                if vehicle.segment_distance >= stop_line:
                    vehicle.segment_distance = stop_line
                    vehicle.stopped = True
                else:
                    vehicle.stopped = advance_vehicle_until(vehicle, stop_line, dt, routes, vehicle_speed)
            else:
                vehicle.stopped = False
                advance_vehicle(vehicle, dt, routes, vehicle_speed)

            apply_vehicle_transform(vehicle)

        if step_count % 10 == 0:
            send_metrics(supervisor, vehicles, traffic_lights, active_phase, active_light, remaining_time, controller_config)


if __name__ == "__main__":
    iniciar_simulacion()
