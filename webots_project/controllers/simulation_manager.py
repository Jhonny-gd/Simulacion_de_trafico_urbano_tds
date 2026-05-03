from __future__ import annotations

import importlib.util
from pathlib import Path


def load_controller_class():
    controller_path = Path(__file__).with_name("simulation_manager") / "simulation_manager.py"
    spec = importlib.util.spec_from_file_location("traffic_simulation_manager", controller_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"No se pudo cargar el controller desde {controller_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.TrafficSimulationManager


TrafficSimulationManager = load_controller_class()


if __name__ == "__main__":
    TrafficSimulationManager().run()
