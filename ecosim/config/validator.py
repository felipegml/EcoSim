from ecosim import simulation


def validate_config(config: dict) -> None:
    world = config.get("world", {})
    terrain = config.get("terrain_percentages", {})

    width = world.get("width")
    height = world.get("height")
    seed = world.get("seed")
    passes = world.get("water_smoothing_passes", 10)

    simulation = config.get("simulation", {})
    speed = simulation.get("ticks_per_second", 1)


    if not isinstance(width, int) or isinstance(width, bool) or width <= 0:
        raise ValueError("World width must be a positive integer.")

    if not isinstance(height, int) or isinstance(height, bool) or height <= 0:
        raise ValueError("World height must be a positive integer.")

    if seed is not None and (
        not isinstance(seed, int) or isinstance(seed, bool)
    ):
        raise ValueError("world.seed must be an integer or null.")

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
    
    if not isinstance(passes, int) or isinstance(passes, bool) or passes < 1:
        raise ValueError(
            "world.water_smoothing_passes must be a positive integer."
        )
    if (
        not isinstance(speed, (int, float))
        or isinstance(speed, bool)
        or speed <= 0
    ):
        raise ValueError(
            "simulation.ticks_per_second must be a positive number."
        )