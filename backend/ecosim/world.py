"""World generation and terrain representation."""

import random
from dataclasses import dataclass, field
from enum import Enum

from backend.ecosim.config import WorldConfig


class Terrain(str, Enum):
    DIRT = "dirt"
    GRASS = "grass"
    WATER = "water"


@dataclass
class Cell:
    terrain: Terrain


@dataclass
class World:
    width: int
    height: int
    cells: list[list[Cell]]
    rng: random.Random = field(repr=False)

    def count_terrain(self, terrain: Terrain) -> int:
        return sum(
            cell.terrain == terrain
            for row in self.cells
            for cell in row
        )


def generate_world(config: WorldConfig) -> World:
    """Generate a reproducible world from the supplied configuration."""
    rng = random.Random(config.seed)
    total = config.width * config.height

    grass_count = round(total * config.grass_coverage)
    water_count = round(total * config.water_coverage)
    dirt_count = total - grass_count - water_count

    terrain_types = (
        [Terrain.GRASS] * grass_count
        + [Terrain.WATER] * water_count
        + [Terrain.DIRT] * dirt_count
    )
    rng.shuffle(terrain_types)

    cells = [
        [
            Cell(terrain_types[y * config.width + x])
            for x in range(config.width)
        ]
        for y in range(config.height)
    ]

    return World(
        width=config.width,
        height=config.height,
        cells=cells,
        rng=rng,
    )