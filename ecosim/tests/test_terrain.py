
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