
import json
import random
import asyncio

from pathlib import Path

from contextlib import asynccontextmanager, suppress
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from ecosim.config.loader import load_config
from ecosim.config.validator import validate_config
from ecosim.world.generator import generate_world

from contextlib import suppress
from ecosim.simulation.engine import SimulationEngine

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIR = PROJECT_ROOT / "frontend"

simulation_engine = SimulationEngine()
simulation_speed = load_config().get(
    "simulation", {}
).get("ticks_per_second", 1)
simulation_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    world_path = FRONTEND_DIR / "world.json"

    if world_path.exists():
        with world_path.open("r", encoding="utf-8") as file:
            world_data = json.load(file)

        simulation_engine.load_world(world_data["tiles"])

    task = asyncio.create_task(simulation_loop())

    try:
        yield
    finally:
        task.cancel()

        with suppress(asyncio.CancelledError):
            await task


app = FastAPI(title="EcoSim API", lifespan=lifespan)


async def simulation_loop():
    while True:
        if simulation_engine.running:
            await asyncio.sleep(1 / simulation_speed)

            # A pause during the wait must prevent the next tick.
            if simulation_engine.running:
                simulation_engine.tick()
        else:
            await asyncio.sleep(0.1)


class WorldSettings(BaseModel):
    width: int = Field(default=100, ge=10, le=300)
    height: int = Field(default=100, ge=10, le=300)
    seed: int | None = None
    water_smoothing_passes: int = Field(default=10, ge=1, le=30)
    terrain_percentages: dict[str, float] = Field(
        default_factory=lambda: {
            "grass": 45,
            "dirt": 25,
            "water": 15,
            "stone": 15,
        }
    )


class SimulationSpeed(BaseModel):
    ticks_per_second: float = Field(gt=0, le=100)


@app.get("/api/config")
def get_config() -> dict:
    return load_config()


@app.post("/api/world")
def create_world(settings: WorldSettings) -> dict:
    config = load_config()

    # Apply the settings sent by the browser.
    seed = settings.seed
    if seed is None:
        seed = random.SystemRandom().randrange(0, 2**32)

    config["world"]["width"] = settings.width
    config["world"]["height"] = settings.height
    config["world"]["seed"] = seed
    config["world"]["water_smoothing_passes"] = (
        settings.water_smoothing_passes
    )
    config["terrain_percentages"] = settings.terrain_percentages

    validate_config(config)
    world = generate_world(config)
    simulation_engine.load_world(world)

    world_data = {
        "width": len(world[0]),
        "height": len(world),
        "seed": seed,
        "tiles": world,
    }

    output_path = FRONTEND_DIR / "world.json"
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(world_data, file)

    return world_data


async def simulation_loop():
    config = load_config()
    speed = config.get("simulation", {}).get(
        "ticks_per_second", 1
    )

    while True:
        if simulation_engine.running:
            await asyncio.sleep(1 / speed)

            if simulation_engine.running:
                simulation_engine.tick()
        else:
            await asyncio.sleep(0.1)

async def simulation_loop():
    while True:
        if simulation_engine.running:
            current_speed = simulation_speed
            await asyncio.sleep(1 / current_speed)

            if simulation_engine.running:
                simulation_engine.tick()
        else:
            await asyncio.sleep(0.1)


@app.get("/api/simulation")
def get_simulation_state():
    return simulation_engine.get_state()


@app.post("/api/simulation/start")
def start_simulation():
    simulation_engine.start()
    return simulation_engine.get_state()


@app.post("/api/simulation/pause")
def pause_simulation():
    simulation_engine.pause()
    return simulation_engine.get_state()


@app.post("/api/simulation/restart")
def restart_simulation():
    global simulation_speed

    config = load_config()
    validate_config(config)

    simulation_speed = config.get(
        "simulation", {}
    ).get("ticks_per_second", 1)

    simulation_engine.reset()

    return {
        **simulation_engine.get_state(),
        "ticks_per_second": simulation_speed,
    }


@app.get("/api/terrain/moisture")
def get_terrain_moisture():
    if simulation_engine.terrain is None:
        return {"error": "No world loaded"}

    return simulation_engine.terrain.get_state()


@app.post("/api/simulation/speed")
def set_simulation_speed(settings: SimulationSpeed):
    global simulation_speed

    simulation_speed = settings.ticks_per_second

    return {
        "ticks_per_second": simulation_speed
    }


app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
