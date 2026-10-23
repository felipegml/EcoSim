
import json
import random
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from ecosim.config.loader import load_config
from ecosim.config.validator import validate_config
from ecosim.world.generator import generate_world


PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIR = PROJECT_ROOT / "frontend"

app = FastAPI(title="EcoSim API")


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
    config["world"]["seed"] = (
        settings.seed
        if settings.seed is not None
        else random.SystemRandom().randrange(0, 2**32)
    )
    config["world"]["water_smoothing_passes"] = (
        settings.water_smoothing_passes
    )
    config["terrain_percentages"] = settings.terrain_percentages

    validate_config(config)
    world = generate_world(config)

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


app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
