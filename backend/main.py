from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.simulation_routes import router as simulation_router


app = FastAPI(
    title="Traffic Simulation Backend",
    description="API REST para controlar y consultar la simulacion de trafico urbano.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(simulation_router)


@app.get("/")
def health_check() -> dict[str, str]:
    return {"message": "Traffic Simulation Backend funcionando"}
