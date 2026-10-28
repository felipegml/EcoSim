
"""Terrain, soil moisture, grass health, and seed germination."""

import random
from dataclasses import dataclass, field


@dataclass
class TerrainSimulation:
    tiles: list[list[str]]
    settings: dict
    seed: int | None = None

    moisture: list[list[float]] = field(init=False)
    grass_health: list[list[float]] = field(init=False)
    rng: random.Random = field(init=False, repr=False)

    def __post_init__(self) -> None:
        """Initialize terrain state from the world and configuration."""

        self.rng = random.Random(self.seed)

        terrain_settings = self.settings["terrain_simulation"]
        grass_settings = self.settings["grass"]

        self.moisture = []
        self.grass_health = []

        for row in self.tiles:
            moisture_row = []
            health_row = []

            for tile in row:
                if tile == "water":
                    moisture_row.append(
                        float(terrain_settings["water_moisture"])
                    )
                    health_row.append(0.0)
                elif tile == "grass":
                    moisture_row.append(
                        float(terrain_settings["grass_moisture"])
                    )
                    health_row.append(
                        float(grass_settings["initial_health"])
                    )
                elif tile == "dirt":
                    moisture_row.append(
                        float(terrain_settings["dirt_moisture"])
                    )
                    health_row.append(0.0)
                elif tile == "stone":
                    moisture_row.append(
                        float(terrain_settings["stone_moisture"])
                    )
                    health_row.append(0.0)
                else:
                    raise ValueError(
                        f"Unknown terrain type: {tile!r}"
                    )

            self.moisture.append(moisture_row)
            self.grass_health.append(health_row)

        self._validate_grid()

    def _validate_grid(self) -> None:
        """Ensure the terrain grid is rectangular and non-empty."""

        if not self.tiles or not self.tiles[0]:
            raise ValueError("The terrain grid cannot be empty.")

        width = len(self.tiles[0])

        if any(len(row) != width for row in self.tiles):
            raise ValueError("All terrain rows must have equal width.")

    def _neighbors(
        self, x: int, y: int
    ) -> list[tuple[int, int]]:
        """Return the valid orthogonal neighbors of a tile."""

        height = len(self.tiles)
        width = len(self.tiles[0])

        positions = (
            (x - 1, y),
            (x + 1, y),
            (x, y - 1),
            (x, y + 1),
        )

        return [
            (nx, ny)
            for nx, ny in positions
            if 0 <= nx < width and 0 <= ny < height
        ]

    def tick(
        self,
        season: str,
        rain_amount: float = 0.0,
        temperature: float = 15.0,
        humidity: float = 60.0,
        wind_strength: float = 0.0,
    ) -> None:
        """Advance moisture, grass, and seed processes by one hour."""

        self._update_moisture(
            season=season,
            rain_amount=rain_amount,
            temperature=temperature,
            humidity=humidity,
        )

        self._update_grass(temperature)
        self._disperse_and_germinate_seeds(
            temperature=temperature,
            wind_strength=wind_strength,
        )

    def _update_moisture(
        self,
        season: str,
        rain_amount: float,
        temperature: float,
        humidity: float,
    ) -> None:
        """Apply diffusion, evaporation, and rain to the soil."""

        terrain_settings = self.settings["terrain_simulation"]
        climate_settings = self.settings["soil_climate"]

        diffusion_rate = float(
            terrain_settings["moisture_diffusion"]
        )
        evaporation_rate = float(
            climate_settings["base_evaporation_rate"]
        )
        reference_temperature = float(
            climate_settings["reference_temperature"]
        )
        temperature_sensitivity = float(
            climate_settings["temperature_sensitivity"]
        )
        humidity_sensitivity = float(
            climate_settings["humidity_sensitivity"]
        )
        minimum_evaporation_factor = float(
            climate_settings["minimum_evaporation_factor"]
        )
        maximum_evaporation_factor = float(
            climate_settings["maximum_evaporation_factor"]
        )

        height = len(self.tiles)
        width = len(self.tiles[0])
        updated = [row[:] for row in self.moisture]

        for y in range(height):
            for x in range(width):
                tile = self.tiles[y][x]

                if tile in ("water", "stone"):
                    continue

                neighbor_positions = self._neighbors(x, y)

                # Use the previous moisture grid so results do not
                # depend on the order in which tiles are processed.
                diffusion = 0.0

                for nx, ny in neighbor_positions:
                    diffusion += (
                        self.moisture[ny][nx]
                        - self.moisture[y][x]
                    ) * diffusion_rate

                temperature_factor = max(
                    minimum_evaporation_factor,
                    min(
                        maximum_evaporation_factor,
                        1.0
                        + (
                            temperature - reference_temperature
                        ) * temperature_sensitivity,
                    ),
                )

                humidity_factor = max(
                    minimum_evaporation_factor,
                    min(
                        maximum_evaporation_factor,
                        1.0
                        - (
                            humidity / 100.0
                        ) * humidity_sensitivity,
                    ),
                )

                evaporation = (
                    evaporation_rate
                    * temperature_factor
                    * humidity_factor
                )

                rain = max(0.0, rain_amount)

                updated[y][x] = max(
                    0.0,
                    min(
                        1.0,
                        self.moisture[y][x]
                        + diffusion
                        - evaporation
                        + rain,
                    ),
                )

        self.moisture = updated

    def _update_grass(self, temperature: float) -> None:
        """Update grass health based on moisture and temperature."""

        grass_settings = self.settings["grass"]

        minimum_moisture = float(
            grass_settings["minimum_moisture"]
        )
        health_loss = float(
            grass_settings["health_loss"]
        )
        health_recovery = float(
            grass_settings["health_recovery"]
        )
        death_threshold = float(
            grass_settings["death_threshold"]
        )

        temperature_range = grass_settings["health_temperature_range"]
        minimum_temperature = float(temperature_range[0])
        maximum_temperature = float(temperature_range[1])

        for y, row in enumerate(self.tiles):
            for x, tile in enumerate(row):
                if tile != "grass":
                    continue

                moisture = self.moisture[y][x]
                health = self.grass_health[y][x]

                temperature_suitable = (
                    minimum_temperature
                    <= temperature
                    <= maximum_temperature
                )

                if (
                    moisture < minimum_moisture
                    or not temperature_suitable
                ):
                    health -= health_loss
                else:
                    health += health_recovery

                health = max(0.0, min(1.0, health))
                self.grass_health[y][x] = health

                if health <= death_threshold:
                    self.tiles[y][x] = "dirt"
                    self.grass_health[y][x] = 0.0

    def _disperse_and_germinate_seeds(
        self,
        temperature: float,
        wind_strength: float,
    ) -> None:
        """Allow external seeds to arrive and germinate on suitable dirt."""

        seed_settings = self.settings["seeds"]
        grass_settings = self.settings["grass"]

        base_arrival_chance = float(
            seed_settings["base_arrival_chance"]
        )
        wind_effect = float(seed_settings["wind_effect"])
        maximum_arrival_chance = float(
            seed_settings["maximum_arrival_chance"]
        )

        germination_chance = float(
            seed_settings["germination_chance"]
        )
        minimum_moisture = float(
            seed_settings["minimum_germination_moisture"]
        )

        temperature_range = seed_settings[
            "germination_temperature_range"
        ]
        minimum_temperature = float(temperature_range[0])
        maximum_temperature = float(temperature_range[1])

        if not (
            minimum_temperature
            <= temperature
            <= maximum_temperature
        ):
            return

        arrival_chance = min(
            maximum_arrival_chance,
            max(
                0.0,
                base_arrival_chance
                + max(0.0, wind_strength) * wind_effect,
            ),
        )

        for y, row in enumerate(self.tiles):
            for x, tile in enumerate(row):
                if tile != "dirt":
                    continue

                if self.moisture[y][x] < minimum_moisture:
                    continue

                # A seed source outside the world can introduce
                # seeds anywhere, independently of nearby grass.
                if self.rng.random() >= arrival_chance:
                    continue

                if self.rng.random() >= germination_chance:
                    continue

                self.tiles[y][x] = "grass"
                self.grass_health[y][x] = float(
                    grass_settings["initial_health"]
                )

    def get_state(self) -> dict:
        """Return terrain state for the API and frontend."""

        return {
            "width": len(self.tiles[0]),
            "height": len(self.tiles),
            "tiles": self.tiles,
            "moisture": [
                [round(value, 4) for value in row]
                for row in self.moisture
            ],
            "grass_health": [
                [round(value, 4) for value in row]
                for row in self.grass_health
            ],
        }
