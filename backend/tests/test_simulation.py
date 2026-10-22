
"""Tests for the Eco-Sim world generator and simulation."""

import pytest

from backend.ecosim.config import WorldConfig
from backend.ecosim.simulation import Simulation
from backend.ecosim.world import Terrain, generate_world


def terrain_layout(world):
    return [
        [cell.terrain for cell in row]
        for row in world.cells
    ]


def test_default_world_terrain_counts():
    world = generate_world(WorldConfig())

    assert world.width == 100
    assert world.height == 100
    assert world.count_terrain(Terrain.GRASS) == 4500
    assert world.count_terrain(Terrain.WATER) == 1000
    assert world.count_terrain(Terrain.DIRT) == 4500


def test_same_seed_generates_same_world():
    first = generate_world(WorldConfig(seed=123))
    second = generate_world(WorldConfig(seed=123))

    assert terrain_layout(first) == terrain_layout(second)


def test_different_seeds_can_generate_different_worlds():
    first = generate_world(WorldConfig(seed=123))
    second = generate_world(WorldConfig(seed=456))

    assert terrain_layout(first) != terrain_layout(second)


def test_water_is_clustered():
    world = generate_world(WorldConfig())
    same_water_neighbors = 0

    for y in range(world.height):
        for x in range(world.width):
            if world.cells[y][x].terrain != Terrain.WATER:
                continue

            if x + 1 < world.width:
                same_water_neighbors += (
                    world.cells[y][x + 1].terrain == Terrain.WATER
                )

            if y + 1 < world.height:
                same_water_neighbors += (
                    world.cells[y + 1][x].terrain == Terrain.WATER
                )

    # Clustered water should have many shared edges.
    assert same_water_neighbors > 1000



def test_grass_is_more_common_near_water():
    world = generate_world(WorldConfig())

    near_water = []
    far_from_water = []

    water_positions = {
        (x, y)
        for y in range(world.height)
        for x in range(world.width)
        if world.cells[y][x].terrain == Terrain.WATER
    }

    for y in range(world.height):
        for x in range(world.width):
            terrain = world.cells[y][x].terrain

            # Compare land only; water itself cannot be grass.
            if terrain == Terrain.WATER:
                continue

            nearby = any(
                abs(wx - x) + abs(wy - y) <= 2
                for wx, wy in water_positions
            )

            is_grass = terrain == Terrain.GRASS

            if nearby:
                near_water.append(is_grass)
            else:
                far_from_water.append(is_grass)

    assert near_water
    assert far_from_water

    near_rate = sum(near_water) / len(near_water)
    far_rate = sum(far_from_water) / len(far_from_water)

    assert near_rate > far_rate, (
        f"Expected more grass near water: "
        f"near={near_rate:.3f}, far={far_rate:.3f}"
    )



def test_simulation_tick_advances():
    simulation = Simulation.create(WorldConfig())

    simulation.step()

    assert simulation.tick == 1


def test_grass_regrows_when_chance_is_one():
    config = WorldConfig(
        width=10,
        height=10,
        grass_coverage=0.0,
        water_coverage=0.0,
        grass_regrowth_chance=1.0,
    )
    simulation = Simulation.create(config)

    simulation.step()

    assert simulation.world.count_terrain(Terrain.GRASS) == 100
    assert simulation.tick == 1


def test_invalid_world_dimensions_are_rejected():
    with pytest.raises(ValueError):
        WorldConfig(width=0)


def test_terrain_coverages_cannot_exceed_world():
    with pytest.raises(ValueError):
        WorldConfig(grass_coverage=0.8, water_coverage=0.3)


def test_water_patch_count_must_be_positive():
    with pytest.raises(ValueError):
        WorldConfig(water_patch_count=0)
