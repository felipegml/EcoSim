
from ecosim.config.loader import load_config
from ecosim.world.generator import generate_world


def test_world_dimensions():
    config = load_config()
    world = generate_world(config)

    assert len(world) == 25
    assert all(len(row) == 40 for row in world)


def test_world_is_reproducible():
    config = load_config()

    world_a = generate_world(config)
    world_b = generate_world(config)

    assert world_a == world_b


def test_world_contains_valid_terrain():
    config = load_config()
    world = generate_world(config)

    valid_terrain = set(config["terrain_percentages"])
    actual_terrain = {
        tile
        for row in world
        for tile in row
    }

    assert actual_terrain <= valid_terrain
