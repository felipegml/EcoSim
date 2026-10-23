def validate_config(config: dict) -> None:
    world = config.get("world", {})
    terrain = config.get("terrain_percentages", {})

    width = world.get("width")
    height = world.get("height")
    seed = world.get("seed")

    if not isinstance(width, int) or isinstance(width, bool) or width <= 0:
        raise ValueError("World width must be a positive integer.")

    if not isinstance(height, int) or isinstance(height, bool) or height <= 0:
        raise ValueError("World height must be a positive integer.")

    if not isinstance(seed, int) or isinstance(seed, bool):
        raise ValueError("World seed must be an integer.")

    if not terrain:
        raise ValueError("Terrain percentages cannot be empty.")

    if any(
        not isinstance(value, (int, float))
        or isinstance(value, bool)
        or value < 0
        for value in terrain.values()
    ):
        raise ValueError("Terrain percentages must be non-negative numbers.")

    if not all(isinstance(name, str) and name for name in terrain):
        raise ValueError("Terrain names must be non-empty strings.")

    if not abs(sum(terrain.values()) - 100) < 1e-9:
        raise ValueError("Terrain percentages must total 100.")