from ecosim.config.loader import load_config
from ecosim.world.generator import generate_world
from collections import Counter
from collections import deque

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

    
def test_different_seeds_create_different_worlds():
    config_a = load_config()
    config_b = load_config()

    config_a["world"] = config_a["world"].copy()
    config_b["world"] = config_b["world"].copy()

    config_a["world"]["seed"] = 12345
    config_b["world"]["seed"] = 67890

    world_a = generate_world(config_a)
    world_b = generate_world(config_b)

    assert world_a != world_b
