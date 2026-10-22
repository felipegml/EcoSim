
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Iterator

from backend.ecosim.config import WorldConfig


class Terrain(str, Enum):
    DIRT = "dirt"
    GRASS = "grass"
    WATER = "water"


@dataclass
class Cell:
    x: int
    y: int
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


def _neighbors(
    x: int, y: int, width: int, height: int
) -> Iterator[tuple[int, int]]:
    if x > 0:
        yield x - 1, y
    if x < width - 1:
        yield x + 1, y
    if y > 0:
        yield x, y - 1
    if y < height - 1:
        yield x, y + 1


def _grow_water(
    width: int,
    height: int,
    target: int,
    patch_count: int,
    rng: random.Random,
) -> set[tuple[int, int]]:
    if target == 0:
        return set()

    positions = [
        (x, y)
        for y in range(height)
        for x in range(width)
    ]

    water = set(
        rng.sample(positions, min(target, patch_count))
    )
    frontier: set[tuple[int, int]] = set()

    def add_frontier(x: int, y: int) -> None:
        for point in _neighbors(x, y, width, height):
            if point not in water:
                frontier.add(point)

    for x, y in sorted(water):
        add_frontier(x, y)

    while len(water) < target:
        if not frontier:
            remaining = [point for point in positions if point not in water]
            point = rng.choice(remaining)
        else:
            point = rng.choice(sorted(frontier))
            frontier.discard(point)

        water.add(point)
        add_frontier(*point)

    return water


def _grow_grass(
    width: int,
    height: int,
    target: int,
    water: set[tuple[int, int]],
    rng: random.Random,
) -> set[tuple[int, int]]:
    if target == 0:
        return set()

    land = {
        (x, y)
        for y in range(height)
        for x in range(width)
        if (x, y) not in water
    }

    if target >= len(land):
        return land

    # Precompute land tiles within Manhattan distance 2 of water.
    near_water: set[tuple[int, int]] = set()

    for wx, wy in water:
        for dy in range(-2, 3):
            remaining_x = 2 - abs(dy)
            for dx in range(-remaining_x, remaining_x + 1):
                point = (wx + dx, wy + dy)
                if point in land:
                    near_water.add(point)

    # Start several grass patches, with most seeds near water.
    seed_count = min(12, target)
    preferred_seeds = sorted(near_water)
    seed_near_count = min(
        len(preferred_seeds), max(1, seed_count * 2 // 3)
    )

    grass = set(
        rng.sample(preferred_seeds, seed_near_count)
    ) if seed_near_count else set()

    remaining_land = sorted(land - grass)
    extra_seeds = min(seed_count - len(grass), len(remaining_land))
    if extra_seeds:
        grass.update(rng.sample(remaining_land, extra_seeds))

    frontier: set[tuple[int, int]] = set()

    def add_frontier(x: int, y: int) -> None:
        for point in _neighbors(x, y, width, height):
            if point in land and point not in grass:
                frontier.add(point)

    for x, y in sorted(grass):
        add_frontier(x, y)

    while len(grass) < target:
        if not frontier:
            remaining = sorted(land - grass)
            point = rng.choice(remaining)
        else:
            candidates = sorted(frontier)
            weights = []

            for x, y in candidates:
                adjacent = list(
                    _neighbors(x, y, width, height)
                )
                nearby_grass = sum(
                    point in grass for point in adjacent
                )
                adjacent_to_water = any(
                    point in water for point in adjacent
                )

                weight = 1 + 2 * nearby_grass

                if (x, y) in near_water:
                    weight += 5

                if adjacent_to_water:
                    weight += 3

                weights.append(weight)

            point = rng.choices(
                candidates, weights=weights, k=1
            )[0]
            frontier.discard(point)

        grass.add(point)
        add_frontier(*point)

    return grass


def generate_world(config: WorldConfig) -> World:
    rng = random.Random(config.seed)
    width, height = config.width, config.height
    total = width * height

    grass_count = round(total * config.grass_coverage)
    water_count = round(total * config.water_coverage)

    water = _grow_water(
        width,
        height,
        water_count,
        config.water_patch_count,
        rng,
    )
    grass = _grow_grass(
        width, height, grass_count, water, rng
    )

    cells = []

    for y in range(height):
        row = []

        for x in range(width):
            point = (x, y)

            if point in water:
                terrain = Terrain.WATER
            elif point in grass:
                terrain = Terrain.GRASS
            else:
                terrain = Terrain.DIRT

            row.append(Cell(x=x, y=y, terrain=terrain))

        cells.append(row)

    return World(
        width=width,
        height=height,
        cells=cells,
        rng=rng,
    )
