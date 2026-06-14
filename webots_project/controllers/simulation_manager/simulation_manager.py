import time
import requests
from controller import Supervisor

# La dirección de tu backend
BACKEND_URL = "http://127.0.0.1:8000/simulation"

def contar_vehiculos(supervisor):
    """
    Escanea la ciudad 3D de forma profunda buscando tanto por
    Tipo de Vehículo como por Nombre (DEF).
    """
    root = supervisor.getRoot()
    children = root.getField("children")
    num_nodes = children.getCount()
    
    contador = 0
    tipos_vehiculos = [
        "BmwX5", "MotorbikeSimple", "Bus", "Truck", 
        "ToyotaPrius", "LincolnMKZ", "CitroenCZero", 
        "RangeRoverSportSVR", "Scooter", "BusSimple", "ScooterSimple", "TruckSimple",  "BmwX5Simple",
         "MercedesBenzSprinter",
    ]
    
    for i in range(num_nodes):
        node = children.getMFNode(i)
        if node:
            tipo = node.getTypeName()
            # Obtenemos el nombre DEF (ej: "vehicle(1)")
            nombre_def = node.getDef() if node.getDef() else ""
            nombre_def = nombre_def.lower()
            
            # Condición 1: ¿Es un modelo 3D de nuestra lista?
            es_tipo_valido = tipo in tipos_vehiculos
            # Condición 2: ¿Tiene la palabra vehicle o motor en su nombre DEF?
            es_def_valido = "vehicle" in nombre_def or "motor" in nombre_def
            
            # Si cumple cualquiera de las dos, ¡es un vehículo!
            if es_tipo_valido or es_def_valido:
                contador += 1
                
    return contador

def iniciar_simulacion():
    supervisor = Supervisor()
    time_step = int(supervisor.getBasicTimeStep())
    
    print("Iniciando Supervisor Dinámico (Conteo Exacto)...")
    
    # Contador de pasos para no saturar el backend
    paso_actual = 0
    
    while supervisor.step(time_step) != -1:
        paso_actual += 1
        
        # Solo enviamos datos al dashboard cada ~10 pasos para que el reloj
        # y los datos se vean super fluidos en la página web sin trabarse.
        if paso_actual % 10 == 0:
            # 1. Leemos el reloj exacto de Webots
            tiempo_actual = supervisor.getTime()
            
            # 2. Contamos TODOS los vehículos de la calle
            cantidad_real = contar_vehiculos(supervisor)

            # 3. Enviamos el paquete de datos
            payload = {
                "vehiculos_activos": cantidad_real,
                "conteo_vehiculos": cantidad_real,
                "velocidad_promedio": 45.5,
                "densidad_trafico": 8.0,
                "flujo_vehicular": 12.0,
                "nivel_congestion": 25.0,
                "tiempo_simulacion": tiempo_actual, # Esto mantiene sincronizado el reloj
                "estado_semaforo": "green"
            }
            
            try:
                requests.post(f"{BACKEND_URL}/status", json=payload, timeout=0.1)
            except Exception as e:
                pass

if __name__ == "__main__":
    iniciar_simulacion()