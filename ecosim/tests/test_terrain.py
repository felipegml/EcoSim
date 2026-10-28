
"""Tests for EcoSim terrain and soil simulation."""

from copy import deepcopy

import pytest

from ecosim.config.loader import load_config
from ecosim.simulation.engine import SimulationEngine
from ecosim.simulation.terrain import TerrainSimulation


@pytest.fixture
def config():
    """Return an independent copy of the project configuration."""
    return deepcopy(load_config())


def test_initial_moisture_matches_terrain(config):
    tiles = [
        ["water", "grass"],
        ["dirt", "stone"],
    ]

    terrain = TerrainSimulation(tiles, config)

    settings = config["terrain_simulation"]

    assert terrain.moisture == [
        [
            settings["water_moisture"],
            settings["grass_moisture"],
        ],
        [
            settings["dirt_moisture"],
            settings["stone_moisture"],
        ],
    ]


def test_moisture_grid_matches_world_size(config):
    tiles = [
        ["grass", "dirt", "water"],
        ["stone", "grass", "dirt"],
    ]

    terrain = TerrainSimulation(tiles, config)

    assert len(terrain.moisture) == 2
    assert all(len(row) == 3 for row in terrain.moisture)


def test_moisture_spreads_from_water(config):
    config["terrain_simulation"]["moisture_diffusion"] = 0.1
    config["soil_climate"]["base_evaporation_rate"] = 0.0

    terrain = TerrainSimulation(
        [["water", "dirt"]],
        config,
    )

    initial_moisture = terrain.moisture[0][1]

    terrain.tick(
        season="spring",
        temperature=15.0,
        humidity=60.0,
        wind_strength=0.0,
    )

    assert terrain.moisture[0][1] > initial_moisture


def test_engine_updates_terrain_on_tick():
    engine = SimulationEngine()
    engine.load_world([["water", "grass"]])

    initial_moisture = engine.terrain.moisture[0][1]
    initial_hour = engine.clock.hour

    engine.start()
    engine.tick()

    assert engine.clock.hour == (initial_hour + 1) % 24
    assert engine.terrain.moisture[0][1] != initial_moisture


def test_grass_health_decreases_when_dry(config):
    config["terrain_simulation"]["grass_moisture"] = 0.0
    config["soil_climate"]["base_evaporation_rate"] = 0.0
    config["terrain_simulation"]["moisture_diffusion"] = 0.0
    config["grass"]["minimum_moisture"] = 0.3
    config["grass"]["health_loss"] = 0.1
    config["grass"]["death_threshold"] = 0.001

    terrain = TerrainSimulation([["grass"]], config)
    initial_health = terrain.grass_health[0][0]

    terrain.tick(
        season="spring",
        temperature=15.0,
        humidity=60.0,
        wind_strength=0.0,
    )

    assert terrain.grass_health[0][0] < initial_health



def test_grass_health_recovers_when_moist(config):
    config["terrain_simulation"]["grass_moisture"] = 0.8
    config["soil_climate"]["base_evaporation_rate"] = 0.0
    config["terrain_simulation"]["moisture_diffusion"] = 0.0
    config["grass"]["minimum_moisture"] = 0.3
    config["grass"]["health_recovery"] = 0.02
    config["grass"]["initial_health"] = 0.5
    config["grass"]["health_temperature_range"] = [-5.0, 35.0]

    terrain = TerrainSimulation([["grass"]], config)
    initial_health = terrain.grass_health[0][0]

    terrain.tick(
        season="spring",
        temperature=15.0,
        humidity=60.0,
        wind_strength=0.0,
    )

    assert terrain.grass_health[0][0] > initial_health
    assert terrain.grass_health[0][0] == pytest.approx(0.52)


def test_dead_grass_becomes_dirt(config):
    config["terrain_simulation"]["grass_moisture"] = 0.0
    config["soil_climate"]["base_evaporation_rate"] = 0.0
    config["terrain_simulation"]["moisture_diffusion"] = 0.0
    config["grass"]["minimum_moisture"] = 0.3
    config["grass"]["health_loss"] = 1.0
    config["grass"]["death_threshold"] = 0.001

    terrain = TerrainSimulation([["grass"]], config)

    terrain.tick(
        season="spring",
        temperature=15.0,
        humidity=60.0,
        wind_strength=0.0,
    )

    assert terrain.tiles[0][0] == "dirt"
    assert terrain.grass_health[0][0] == 0.0


def test_grass_germinates_on_moist_dirt(config):
    config["terrain_simulation"]["dirt_moisture"] = 0.8
    config["soil_climate"]["base_evaporation_rate"] = 0.0
    config["terrain_simulation"]["moisture_diffusion"] = 0.0
    config["seeds"]["base_arrival_chance"] = 1.0
    config["seeds"]["wind_effect"] = 0.0
    config["seeds"]["maximum_arrival_chance"] = 1.0
    config["seeds"]["germination_chance"] = 1.0
    config["seeds"]["minimum_germination_moisture"] = 0.4
    config["seeds"]["germination_temperature_range"] = [5.0, 30.0]

    terrain = TerrainSimulation(
        [["dirt"]],
        config,
        seed=42,
    )

    terrain.tick(
        season="spring",
        temperature=15.0,
        humidity=60.0,
        wind_strength=0.0,
    )

    assert terrain.tiles[0][0] == "grass"
    assert terrain.grass_health[0][0] == config["grass"]["initial_health"]


def test_terrain_rejects_ragged_grid(config):
    with pytest.raises(ValueError, match="equal width"):
        TerrainSimulation(
            [["grass", "dirt"], ["water"]],
            config,
        )
