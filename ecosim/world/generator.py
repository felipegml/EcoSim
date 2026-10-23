
import random


def smooth_noise(
    scores: list[list[float]],
    passes: int,
) -> list[list[float]]:
    """Smooth random scores to create larger terrain regions."""
    height = len(scores)
    width = len(scores[0])

    for _ in range(passes):
        smoothed = []

        for y in range(height):
            row = []

            for x in range(width):
                neighbors = [
                    scores[ny][nx]
                    for ny in range(max(0, y - 1), min(height, y + 2))
                    for nx in range(max(0, x - 1), min(width, x + 2))
                ]

                row.append(sum(neighbors) / len(neighbors))

            smoothed.append(row)

        scores = smoothed

    return scores


def generate_world(config: dict) -> list[list[str]]:
    world_config = config["world"]
    terrain_percentages = config["terrain_percentages"]

    width = world_config["width"]
    height = world_config["height"]
    seed = world_config["seed"]

    rng = random.Random(seed)

    water_noise = [
        [rng.random() for _ in range(width)]
        for _ in range(height)
    ]

    water_noise = smooth_noise(
        water_noise,
        passes=world_config.get("water_smoothing_passes", 10),
    )

    # Step 1: Generate broad landscape shapes.
    broad_noise = [
        [rng.random() for _ in range(width)]
        for _ in range(height)
    ]

    broad_noise = smooth_noise(broad_noise, passes=8)

    # Make water scores depend partly on the surrounding landscape.
    water_noise = [
        [
            water_noise[y][x] * 0.7
            + broad_noise[y][x] * 0.3
            for x in range(width)
        ]
        for y in range(height)
    ]

    # Step 2: Generate smaller details.
    detail_noise = [
        [rng.random() for _ in range(width)]
        for _ in range(height)
    ]

    detail_noise = smooth_noise(detail_noise, passes=2)

    # Step 3: Combine broad shapes and fine details.
    scores = [
        [
            broad_noise[y][x] * 0.8
            + detail_noise[y][x] * 0.2
            for x in range(width)
        ]
        for y in range(height)
    ]

    # Create separate patterns for dirt and stone.
    dirt_noise = [
        [rng.random() for _ in range(width)]
        for _ in range(height)
    ]

    stone_noise = [
        [rng.random() for _ in range(width)]
        for _ in range(height)
    ]

    dirt_noise = smooth_noise(dirt_noise, passes=5)
    stone_noise = smooth_noise(stone_noise, passes=5)
    
    # Step 4: Rank tiles using the landscape and water scores.
    ranked_tiles = sorted(
        (
            (scores[y][x], x, y)
            for y in range(height)
            for x in range(width)
        )
    )

    ranked_water = sorted(
        (
            (water_noise[y][x], x, y)
            for y in range(height)
            for x in range(width)
        )
    )

    # Step 5: Calculate the exact number of tiles per terrain.
    total_tiles = width * height

    counts = {
        name: int(total_tiles * percentage / 100)
        for name, percentage in terrain_percentages.items()
    }

    # Distribute leftover tiles caused by rounding.
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

    # Step 6: Place water using its own smoothed noise map.
    tiles = [[""] * width for _ in range(height)]

    water_count = counts.get("water", 0)
    water_positions = {
        (x, y)
        for _, x, y in ranked_water[:water_count]
    }

    for x, y in water_positions:
        tiles[y][x] = "water"

    # Step 7: Fill the remaining tiles with other terrain types.
    land_tiles = [
        (x, y)
        for _, x, y in ranked_tiles
        if (x, y) not in water_positions
    ]

    # Rank land separately for each terrain type.
    land_by_dirt = sorted(
        land_tiles,
        key=lambda pos: dirt_noise[pos[1]][pos[0]],
    )

    land_by_stone = sorted(
        land_tiles,
        key=lambda pos: stone_noise[pos[1]][pos[0]],
    )

    terrain_order = [
        name
        for name in ("grass", "dirt", "stone")
        if name in counts
    ]

    terrain_order.extend(
        name
        for name in counts
        if name not in terrain_order and name != "water"
    )

    remaining_land = set(land_tiles)

    for terrain_name in terrain_order:
        terrain_count = counts[terrain_name]

        if terrain_name == "dirt":
            ranked_land = land_by_dirt
        elif terrain_name == "stone":
            ranked_land = land_by_stone
        else:
            ranked_land = sorted(
                land_tiles,
                key=lambda pos: scores[pos[1]][pos[0]],
            )

        selected = [
            pos for pos in ranked_land
            if pos in remaining_land
        ][:terrain_count]

        for x, y in selected:
            tiles[y][x] = terrain_name

        remaining_land.difference_update(selected)

    return tiles