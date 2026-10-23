from ecosim.config.loader import load_config
from ecosim.world.generator import generate_world
from collections import Counter


def test_terrain_counts_match_config():
    config = load_config()
    world = generate_world(config)

    actual_counts = Counter(
        tile
        for row in world
        for tile in row
    )

    total_tiles = config["world"]["width"] * config["world"]["height"]

    for terrain, percentage in config["terrain_percentages"].items():
        expected = round(total_tiles * percentage / 100)
        assert actual_counts[terrain] == expected

