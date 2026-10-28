
"""Expose EcoSim simulation controls through a FastAPI application."""

import asyncio
import math
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, model_validator

from ecosim.config.loader import load_config
from ecosim.simulation.engine import SimulationEngine
from ecosim.world.generator import generate_world


engine = SimulationEngine()
simulation_task: asyncio.Task | None = None


async def simulation_loop() -> None:
    """Advance the simulation automatically at the configured rate."""
    while engine.running:
        ticks_per_second = engine.config["simulation"]["ticks_per_second"]

        await asyncio.sleep(1.0 / ticks_per_second)

        if engine.running:
            engine.tick()


async def stop_simulation_task() -> None:
    """Cancel the automatic tick loop if it is active."""
    global simulation_task

    task = simulation_task
    simulation_task = None

    if task is not None and not task.done():
        task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Clean up the background simulation task on shutdown."""
    yield
    engine.pause()
    await stop_simulation_task()


app = FastAPI(
    title="EcoSim API",
    description="API for controlling and observing the EcoSim simulation.",
    version="1.1.0",
    lifespan=lifespan,
)


TerrainType = Literal["grass", "dirt", "water", "stone"]


class WorldRequest(BaseModel):
    """Request to generate a world or load a supplied terrain grid."""

    width: int | None = Field(default=None, gt=0)
    height: int | None = Field(default=None, gt=0)
    seed: int | None = None
    water_smoothing_passes: int | None = Field(default=None, ge=0)
    terrain_percentages: dict[str, float] | None = None
    tiles: list[list[TerrainType]] | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def validate_request(self):
        """Require either terrain tiles or world-generation settings."""
        if self.tiles is not None:
            if not self.tiles[0]:
                raise ValueError("The terrain grid cannot be empty.")

            expected_width = len(self.tiles[0])

            if any(len(row) != expected_width for row in self.tiles):
                raise ValueError(
                    "Every terrain row must have the same width."
                )

        elif self.width is None or self.height is None:
            raise ValueError(
                "Provide tiles or both width and height to generate a world."
            )

        return self


class SpeedRequest(BaseModel):
    """Request body used to configure simulation speed."""

    ticks_per_second: float = Field(gt=0, allow_inf_nan=False)


@app.get("/api/config")
def get_config() -> dict:
    """Return the current simulation configuration."""
    return engine.config


@app.get("/api/simulation")
def get_simulation_state() -> dict:
    """Return the state of all simulation systems."""
    return engine.get_state()


@app.post("/api/simulation/start")
async def start_simulation() -> dict:
    """Start or resume the simulation's automatic tick loop."""
    global simulation_task

    engine.start()

    if simulation_task is None or simulation_task.done():
        simulation_task = asyncio.create_task(simulation_loop())

    return engine.get_state()


@app.post("/api/simulation/pause")
async def pause_simulation() -> dict:
    """Pause the simulation and stop its automatic tick loop."""
    engine.pause()
    await stop_simulation_task()
    return engine.get_state()


@app.post("/api/simulation/restart")
async def restart_simulation() -> dict:
    """Reset the clock and environmental systems."""
    engine.reset()
    await stop_simulation_task()
    return engine.get_state()


@app.post("/api/simulation/tick")
def advance_simulation() -> dict:
    """Advance one simulated hour when the engine is running."""
    return engine.tick()


@app.post("/api/world")
def load_world(request: WorldRequest) -> dict:
    """Generate a world from settings or load a supplied terrain grid."""
    if request.tiles is not None:
        tiles = request.tiles
        seed = request.seed
        terrain_percentages = None
    else:
        config = load_config()

        if request.width is not None:
            config["world"]["width"] = request.width

        if request.height is not None:
            config["world"]["height"] = request.height

        if request.seed is not None:
            config["world"]["seed"] = request.seed

        if request.water_smoothing_passes is not None:
            config["world"]["water_smoothing_passes"] = (
                request.water_smoothing_passes
            )

        if request.terrain_percentages is not None:
            config["terrain_percentages"] = request.terrain_percentages

        try:
            tiles = generate_world(config)
        except (KeyError, TypeError, ValueError) as error:
            raise HTTPException(
                status_code=422,
                detail=str(error),
            ) from error

        seed = config["world"].get("seed")
        terrain_percentages = config["terrain_percentages"]

        # Keep the active configuration aligned with the generated world.
        engine.config["world"] = config["world"].copy()
        engine.config["terrain_percentages"] = (
            config["terrain_percentages"].copy()
        )

    try:
        engine.load_world(tiles=tiles, seed=seed)
    except (ValueError, KeyError, TypeError) as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    height = len(tiles)
    width = len(tiles[0])

    terrain_counts = {
        name: sum(
            tile == name
            for row in tiles
            for tile in row
        )
        for name in ("grass", "dirt", "water", "stone")
    }

    if terrain_percentages is None:
        terrain_percentages = {
            name: count / (width * height) * 100
            for name, count in terrain_counts.items()
        }

    return {
        "width": width,
        "height": height,
        "seed": seed,
        "tiles": tiles,
        "terrain_counts": terrain_counts,
        "terrain_percentages": terrain_percentages,
    }


@app.get("/api/world")
def get_world() -> dict:
    """Return the loaded world's terrain data."""
    state = engine.get_state()

    if not state["world_loaded"]:
        raise HTTPException(
            status_code=404,
            detail="No world is loaded. Generate one or send terrain tiles to POST /api/world.",
        )

    return state["terrain"]


@app.get("/api/terrain/moisture")
def get_soil_moisture() -> dict:
    """Return soil moisture and grass health when available."""
    state = engine.get_state()

    if not state["world_loaded"]:
        raise HTTPException(
            status_code=404,
            detail="No world is loaded.",
        )

    terrain_state = state["terrain"]

    result = {
        "width": terrain_state["width"],
        "height": terrain_state["height"],
        "moisture": terrain_state["moisture"],
    }

    if "grass_health" in terrain_state:
        result["grass_health"] = terrain_state["grass_health"]

    return result


@app.post("/api/simulation/speed")
def set_simulation_speed(request: SpeedRequest) -> dict:
    """Update the automatic simulation tick rate."""
    try:
        engine.set_speed(request.ticks_per_second)
    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    return {
        "ticks_per_second": engine.config["simulation"]["ticks_per_second"]
    }


@app.get("/health")
def health_check() -> dict:
    """Report whether the API process is responding."""
    return {"status": "ok"}
