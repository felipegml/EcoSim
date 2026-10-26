
from dataclasses import dataclass, field
from ecosim.simulation.weather import WeatherSimulation


@dataclass
class TerrainSimulation:
    tiles: list[list[str]]
    settings: dict = field(default_factory=dict)
    moisture: list[list[float]] = field(init=False)
    weather: WeatherSimulation = field(default_factory=WeatherSimulation)

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

    def get_state(self) -> dict:
        return {
            "width": len(self.tiles[0]) if self.tiles else 0,
            "height": len(self.tiles),
            "moisture": self.moisture,
        }

    def tick(
        self,
        season: str = "spring",
        rain_amount: float = 0.0,
    ) -> None:
        height = len(self.tiles)
        width = len(self.tiles[0]) if height else 0

        diffusion = self.settings.get("moisture_diffusion", 0.05)
        seasonal_evaporation = self.settings.get(
            "seasonal_evaporation", {}
        )

        evaporation = seasonal_evaporation.get(
            season,
            self.settings.get("evaporation_rate", 0.001),
        )

        updated = [row[:] for row in self.moisture]

        for y in range(height):
            for x in range(width):
                terrain = self.tiles[y][x]

                if terrain == "water":
                    updated[y][x] = self.settings.get("water_moisture", 1.0)
                    continue

                if terrain == "stone":
                    updated[y][x] = self.settings.get("stone_moisture", 0.0)
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

                updated[y][x] = max(0.0, min(1.0, current))

        self.moisture = updated
