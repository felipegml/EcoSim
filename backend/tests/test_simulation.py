"""Tests for the initial Eco-Sim implementation."""

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
    try:
        WorldConfig(width=0)
    except ValueError:
        pass
    else:
        raise AssertionError("Expected invalid dimensions to raise ValueError")