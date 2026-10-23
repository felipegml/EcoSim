
import random

from ecosim.world.terrain import Terrain


def generate_world(config: dict) -> list[list[str]]:
    world_config = config["world"]
    terrain_percentages = config["terrain_percentages"]

    width = world_config["width"]
    height = world_config["height"]
    seed = world_config["seed"]

    rng = random.Random(seed)

    # Step 1: Create a random noise map.
    scores = [
        [rng.random() for _ in range(width)]
        for _ in range(height)
    ]

    # Step 2: Smooth the noise so nearby tiles become similar.
    for _ in range(6):
        smoothed = []

        for y in range(height):
            row = []

            for x in range(width):
                neighbors = [
                    scores[ny][nx]
                    for ny in range(max(0, y - 1), min(height, y + 2))
                    for nx in range(max(0, x - 1), min(width, x + 2))
                ]

                # Give the current tile extra influence.
                value = (
                    sum(neighbors) + scores[y][x]
                ) / (len(neighbors) + 1)

                row.append(value)

            smoothed.append(row)

        scores = smoothed

    # Step 3: Flatten the map and sort tiles by their scores.
    ranked_tiles = sorted(
        (
            (scores[y][x], x, y)
            for y in range(height)
            for x in range(width)
        )
    )

    # Step 4: Allocate exact terrain counts.
    total_tiles = width * height
    counts = {
        name: int(total_tiles * percentage / 100)
        for name, percentage in terrain_percentages.items()
    }

    # Distribute any leftover tiles caused by rounding.
    remaining = total_tiles - sum(counts.values())

    fractions = sorted(
        terrain_percentages,
        key=lambda name: (
            -(total_tiles * terrain_percentages[name] / 100
              - counts[name]),
            name,
        ),
    )

    for name in fractions[:remaining]:
        counts[name] += 1

    # Lower scores become water; higher scores become rocky terrain.
    terrain_order = [
        name for name in ("water", "grass", "dirt", "stone")
        if name in counts
    ]
    terrain_order.extend(
        name for name in counts if name not in terrain_order
    )

    tiles = [
        [""] * width
        for _ in range(height)
    ]

    position = 0

    for terrain_name in terrain_order:
        for _, x, y in ranked_tiles[position:position + counts[terrain_name]]:
            tiles[y][x] = terrain_name

        position += counts[terrain_name]

    return tiles