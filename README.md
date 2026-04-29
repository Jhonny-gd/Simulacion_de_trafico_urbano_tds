# Simulacion de Trafico Urbano TDS

Sistema de simulacion de trafico urbano integrado con Webots, un backend REST en FastAPI y un frontend web en Vue 3 + Vuetify.

## Descripcion

El proyecto permite monitorear y controlar variables de una simulacion urbana:

- Conteo de vehiculos.
- Densidad de trafico.
- Velocidad promedio.
- Flujo vehicular.
- Nivel de congestion.
- Estado y tiempos de semaforos.
- Control basico de la simulacion desde una interfaz web.

## Tecnologias

- Python
- FastAPI
- Webots Supervisor API
- Vue 3 Composition API
- Vuetify
- Axios
- Vite

## Estructura

```text
.
+-- backend/
|   +-- main.py
|   +-- models/
|   +-- routes/
|   +-- services/
+-- frontend/
|   +-- src/
|   |   +-- components/
|   |   +-- services/
|   |   +-- views/
|   +-- package.json
+-- webots_project/
    +-- controllers/
    |   +-- simulation_manager.py
    +-- worlds/
        +-- urban_city.wbt
```

## Backend

El backend expone una API REST para leer configuracion, actualizar parametros y controlar la simulacion.

### Endpoints principales

```text
GET  /simulation/status
POST /simulation/status
GET  /simulation/config
POST /simulation/config
POST /simulation/control/start
POST /simulation/control/pause
POST /simulation/control/reset
```

### Ejecutar backend

Desde la carpeta `backend`:

```powershell
pip install -r requirements.txt
```

```powershell
python -m uvicorn main:app --reload
```

La API queda disponible en:

```text
http://127.0.0.1:8000
```

Documentacion interactiva:

```text
http://127.0.0.1:8000/docs
```

## Frontend

El frontend contiene un login, dashboard, tarjetas de metricas y paneles flotantes para controlar vehiculos, semaforos y monitoreo.

### Instalar dependencias

Desde la carpeta `frontend`:

```powershell
npm install
```

### Ejecutar frontend

```powershell
npm run dev
```

La aplicacion queda disponible en:

```text
http://127.0.0.1:5173
```

### Validar build

```powershell
npm run build
```

## Webots

El controller principal es:

```text
webots_project/controllers/simulation_manager.py
```

Este controller:

- Usa `Supervisor`.
- Consulta configuracion desde `GET /simulation/config`.
- Envia metricas hacia `POST /simulation/status`.
- Mantiene valores locales si el backend no esta disponible.
- Calcula conteo de vehiculos, densidad, velocidad promedio, flujo y congestion.
- Controla semaforos con parametros provenientes del backend.

## Flujo de ejecucion recomendado

1. Iniciar el backend:

```powershell
cd backend
python -m uvicorn main:app --reload
```

2. Iniciar el frontend:

```powershell
cd frontend
npm run dev
```

3. Abrir Webots y ejecutar el mundo:

```text
webots_project/worlds/urban_city.wbt
```

4. Abrir la interfaz web:

```text
http://127.0.0.1:5173
```

## Estado actual

El proyecto mantiene los datos en memoria. No usa base de datos todavia.

## Requisitos pendientes posibles

- Persistencia con base de datos.
- Autenticacion real.
- Stream o captura de Webots dentro del dashboard.
- Mas controles por vehiculo y rutas.
- Despliegue en entorno productivo.
