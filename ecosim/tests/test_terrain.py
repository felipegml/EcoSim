
from ecosim.simulation.terrain import TerrainSimulation
from ecosim.simulation.engine import SimulationEngine


def test_initial_moisture_matches_terrain():
    tiles = [
        ["water", "grass"],
        ["dirt", "stone"],
    ]

    terrain = TerrainSimulation(tiles)

    assert terrain.moisture == [
        [1.0, 0.5],
        [0.25, 0.0],
    ]


def test_moisture_grid_matches_world_size():
    tiles = [
        ["grass", "dirt", "water"],
        ["stone", "grass", "dirt"],
    ]

    terrain = TerrainSimulation(tiles)
    state = terrain.get_state()

    assert state["width"] == 3
    assert state["height"] == 2


def test_moisture_spreads_from_water():
    terrain = TerrainSimulation([
        ["water", "grass"],
    ])

    initial_moisture = terrain.moisture[0][1]

    terrain.tick()

    assert terrain.moisture[0][0] == 1.0
    assert terrain.moisture[0][1] > initial_moisture


def test_engine_updates_terrain_on_tick():
    engine = SimulationEngine()
    engine.load_world([["water", "grass"]])

    initial_moisture = engine.terrain.moisture[0][1]

    engine.tick()

    assert engine.clock.hour == 1
    assert engine.terrain.moisture[0][1] > initial_moisture


def test_grass_health_decreases_when_dry():
    terrain = TerrainSimulation(
        tiles=[["grass"]],
        settings={
            "grass_moisture": 0.0,
            "evaporation_rate": 0.0,
            "grass": {
                "minimum_moisture": 0.3,
                "health_loss": 0.1,
                "health_recovery": 0.01,
            },
        },
    )

    terrain.tick(season="spring")

    assert terrain.grass_health[0][0] == 0.9


def test_grass_health_recovers_when_moist():
    terrain = TerrainSimulation(
        tiles=[["grass"]],
        settings={
            "grass_moisture": 0.8,
            "evaporation_rate": 0.0,
            "grass": {
                "minimum_moisture": 0.3,
                "health_recovery": 0.02,
            },
        },
    )

    terrain.grass_health[0][0] = 0.5
    terrain.tick(season="spring")

    assert terrain.grass_health[0][0] > 0.5

def test_dead_grass_becomes_dirt():
    terrain = TerrainSimulation(
        tiles=[["grass"]],
        settings={
            "grass_moisture": 0.0,
            "evaporation_rate": 0.0,
            "grass": {
                "minimum_moisture": 0.3,
                "health_loss": 0.1,
            },
        },
    )

    terrain.grass_health[0][0] = 0.1
    terrain.tick(season="spring")

    assert terrain.tiles[0][0] == "dirt"
    assert terrain.grass_health[0][0] == 0.0


def test_grass_spreads_to_moist_dirt():
    terrain = TerrainSimulation(
        tiles=[["grass", "dirt"]],
        settings={
            "evaporation_rate": 0.0,
            "dirt_moisture": 0.8,
            "grass": {
                "minimum_moisture": 0.3,
                "spread_moisture": 0.4,
                "spread_source_health": 0.7,
                "spread_chance": 1.0,
            },
        },
    )

    terrain.tick(season="spring")

    assert terrain.tiles[0][1] == "grass"
    assert terrain.grass_health[0][1] == 0.5