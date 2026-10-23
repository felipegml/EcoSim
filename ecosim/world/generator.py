import random

from ecosim.world.terrain import Terrain


def generate_world(config: dict) -> list[list[str]]:
    world_config = config["world"]
    terrain_percentages = config["terrain_percentages"]

    width = world_config["width"]
    height = world_config["height"]
    seed = world_config["seed"]

    rng = random.Random(seed)

    terrain_names = list(terrain_percentages.keys())
    terrain_weights = list(terrain_percentages.values())

    tiles = rng.choices(
        terrain_names,
        weights=terrain_weights,
        k=width * height,
    )

    return [
        tiles[row * width:(row + 1) * width]
        for row in range(height)
    ]
