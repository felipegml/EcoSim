
"""Expose EcoSim simulation controls through a FastAPI application."""

from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from ecosim.simulation.engine import SimulationEngine


app = FastAPI(
    title="EcoSim API",
    description="API for controlling and observing the EcoSim simulation.",
    version="1.0.0",
)

engine = SimulationEngine()


class WorldRequest(BaseModel):
    """Request body used to load a terrain grid."""

    tiles: list[list[Literal["grass", "dirt", "water", "stone"]]] = Field(
        min_length=1,
        description="A non-empty rectangular grid of terrain tiles.",
    )


class SpeedRequest(BaseModel):
    """Request body used to configure simulation speed."""

    ticks_per_second: float = Field(gt=0)


@app.get("/api/config")
def get_config() -> dict:
    """Return the current simulation configuration."""
    return engine.config


@app.get("/api/simulation")
def get_simulation_state() -> dict:
    """Return the current state of all simulation systems."""
    return engine.get_state()


@app.post("/api/simulation/start")
def start_simulation() -> dict:
    """Start or resume the simulation."""
    engine.start()
    return engine.get_state()


@app.post("/api/simulation/pause")
def pause_simulation() -> dict:
    """Pause the simulation."""
    engine.pause()
    return engine.get_state()


@app.post("/api/simulation/restart")
def restart_simulation() -> dict:
    """Reset the simulation clock and environmental systems."""
    engine.reset()
    return engine.get_state()


@app.post("/api/simulation/tick")
def advance_simulation() -> dict:
    """Advance by one simulated hour when the engine is running."""
    return engine.tick()


@app.post("/api/world")
def load_world(request: WorldRequest) -> dict:
    """Load a supplied terrain grid into the simulation."""

    if not request.tiles or not request.tiles[0]:
        raise HTTPException(
            status_code=422,
            detail="The terrain grid cannot be empty.",
        )

    width = len(request.tiles[0])

    if any(len(row) != width for row in request.tiles):
        raise HTTPException(
            status_code=422,
            detail="Every terrain row must have the same width.",
        )

    try:
        engine.load_world(tiles=request.tiles)
    except (ValueError, KeyError) as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    return engine.get_state()


@app.get("/api/world")
def get_world() -> dict:
    """Return the loaded world and its terrain data."""

    state = engine.get_state()

    if not state["world_loaded"]:
        raise HTTPException(
            status_code=404,
            detail="No world is loaded. Send a terrain grid to POST /api/world.",
        )

    return state["terrain"]


@app.get("/api/terrain/moisture")
def get_soil_moisture() -> dict:
    """Return the current soil moisture grid."""

    state = engine.get_state()

    if not state["world_loaded"]:
        raise HTTPException(
            status_code=404,
            detail="No world is loaded.",
        )

    return {
        "width": state["terrain"]["width"],
        "height": state["terrain"]["height"],
        "moisture": state["terrain"]["moisture"],
    }


@app.post("/api/simulation/speed")
def set_simulation_speed(request: SpeedRequest) -> dict:
    """Update the configured tick rate for the API client."""

    engine.config["simulation"]["ticks_per_second"] = (
        request.ticks_per_second
    )

    return {
        "ticks_per_second": engine.config["simulation"]["ticks_per_second"]
    }


@app.get("/health")
def health_check() -> dict:
    """Report whether the API process is responding."""
    return {"status": "ok"}
