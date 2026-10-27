
import random

from dataclasses import dataclass, field
from ecosim.simulation.weather import WeatherSimulation


@dataclass
class TerrainSimulation:
    tiles: list[list[str]]
    settings: dict = field(default_factory=dict)
    moisture: list[list[float]] = field(init=False)
    grass_health: list[list[float]] = field(init=False)
    weather: WeatherSimulation = field(default_factory=WeatherSimulation)
    rng: random.Random = field(init=False, repr=False)

    def __post_init__(self) -> None:
        defaults = {
            "water_moisture": 1.0,
            "grass_moisture": 0.5,
            "dirt_moisture": 0.25,
            "stone_moisture": 0.0,
        }

        values = {**defaults, **self.settings}
        moisture_by_terrain = {
            "water": values["water_moisture"],
            "grass": values["grass_moisture"],
            "dirt": values["dirt_moisture"],
            "stone": values["stone_moisture"],
        }

        self.moisture = [
            [moisture_by_terrain.get(tile, 0.0) for tile in row]
            for row in self.tiles
        ]

        self.grass_health = [
            [1.0 if tile == "grass" else 0.0 for tile in row]
            for row in self.tiles
        ]

        grass_settings = self.settings.get("grass", {})
        self.rng = random.Random(grass_settings.get("random_seed"))

    
    def get_state(self) -> dict:
        return {
            "width": len(self.tiles[0]) if self.tiles else 0,
            "height": len(self.tiles),
            "tiles": self.tiles,
            "moisture": self.moisture,
            "grass_health": self.grass_health,
        }


    def tick(
        self,
        season: str = "spring",
        rain_amount: float = 0.0,
    ) -> None:
        height = len(self.tiles)
        width = len(self.tiles[0]) if height else 0

        diffusion = self.settings.get("moisture_diffusion", 0.05)

        grass_settings = self.settings.get("grass", {})
        minimum_moisture = grass_settings.get("minimum_moisture", 0.3)
        health_loss = grass_settings.get("health_loss", 0.01)
        health_recovery = grass_settings.get("health_recovery", 0.005)
        winter_health_loss = grass_settings.get("winter_health_loss", 0.015)

        death_threshold = grass_settings.get("death_threshold", 0.0)
        spread_chance = grass_settings.get("spread_chance", 0.05)
        spread_moisture = grass_settings.get("spread_moisture", 0.4)
        source_health = grass_settings.get("spread_source_health", 0.7)

        seasonal_evaporation = self.settings.get(
            "seasonal_evaporation", {}
        )
        evaporation = seasonal_evaporation.get(
            season,
            self.settings.get("evaporation_rate", 0.001),
        )

        # 1. Update soil moisture.
        updated_moisture = [row[:] for row in self.moisture]

        for y in range(height):
            for x in range(width):
                terrain = self.tiles[y][x]

                if terrain == "water":
                    updated_moisture[y][x] = self.settings.get(
                        "water_moisture", 1.0
                    )
                    continue

                if terrain == "stone":
                    updated_moisture[y][x] = self.settings.get(
                        "stone_moisture", 0.0
                    )
                    continue

                neighbors = [
                    self.moisture[ny][nx]
                    for nx, ny in (
                        (x - 1, y),
                        (x + 1, y),
                        (x, y - 1),
                        (x, y + 1),
                    )
                    if 0 <= nx < width and 0 <= ny < height
                ]

                current = self.moisture[y][x]

                if neighbors:
                    average = sum(neighbors) / len(neighbors)
                    current += (average - current) * diffusion

                current -= evaporation

                if terrain in ("grass", "dirt"):
                    current += rain_amount

                updated_moisture[y][x] = max(0.0, min(1.0, current))

        self.moisture = updated_moisture

        # 2. Update existing grass health.
        health_updated = [row[:] for row in self.grass_health]

        for y in range(height):
            for x in range(width):
                if self.tiles[y][x] != "grass":
                    health_updated[y][x] = 0.0
                    continue

                moisture = self.moisture[y][x]
                health = self.grass_health[y][x]

                if season == "winter":
                    health -= winter_health_loss
                elif moisture < minimum_moisture:
                    health -= health_loss
                else:
                    health += health_recovery

                health = max(0.0, min(1.0, health))

                if health <= death_threshold + 1e-9:
                    health = 0.0

                health_updated[y][x] = health

        # 3. Work on copies so new grass cannot spread again this tick.
        updated_tiles = [row[:] for row in self.tiles]
        updated_health = [row[:] for row in health_updated]

        # 4. Dead grass becomes dirt.
        for y in range(height):
            for x in range(width):
                if (
                    self.tiles[y][x] == "grass"
                    and health_updated[y][x] <= death_threshold + 1e-9
                ):
                    updated_tiles[y][x] = "dirt"
                    updated_health[y][x] = 0.0

        # 5. Healthy grass spreads to neighboring, moist dirt.
        for y in range(height):
            for x in range(width):
                if self.tiles[y][x] != "dirt":
                    continue

                if self.moisture[y][x] < spread_moisture:
                    continue

                neighbors = [
                    (nx, ny)
                    for nx, ny in (
                        (x - 1, y),
                        (x + 1, y),
                        (x, y - 1),
                        (x, y + 1),
                    )
                    if 0 <= nx < width and 0 <= ny < height
                ]

                has_healthy_grass = any(
                    self.tiles[ny][nx] == "grass"
                    and health_updated[ny][nx] >= source_health
                    for nx, ny in neighbors
                )

                if has_healthy_grass and self.rng.random() < spread_chance:
                    updated_tiles[y][x] = "grass"
                    updated_health[y][x] = 0.5

        # 6. Save the updated world.
        self.tiles = updated_tiles
        self.grass_health = updated_health
