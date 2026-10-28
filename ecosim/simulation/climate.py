
"""Generate daily climate profiles and smooth hourly changes."""

import math
import random
from dataclasses import dataclass, field


@dataclass
class ClimateSimulation:
    settings: dict
    seed: int | None = None

    day: int = 0
    season: str | None = None

    daily_min_temperature: float = 0.0
    daily_max_temperature: float = 0.0
    daily_humidity: float = 0.0

    temperature: float = 0.0
    humidity: float = 0.0

    rng: random.Random = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.rng = random.Random(self.seed)

    def update(
        self,
        day: int,
        hour: int,
        season: str,
        is_raining: bool = False,
    ) -> None:
        """Update climate for the current simulated hour."""

        if day != self.day or season != self.season:
            self._generate_daily_profile(season)
            self.day = day
            self.season = season

        season_settings = self.settings["seasons"][season]
        minimum_hour = float(
            season_settings["temperature_minimum_hour"]
        )

        # Temperature reaches its daily minimum at the configured hour
        # and its maximum approximately 12 hours later.
        phase = 2.0 * math.pi * (
            (hour - minimum_hour) / 24.0
        )

        midpoint = (
            self.daily_min_temperature
            + self.daily_max_temperature
        ) / 2.0

        amplitude = (
            self.daily_max_temperature
            - self.daily_min_temperature
        ) / 2.0

        self.temperature = midpoint - amplitude * math.cos(phase)

        temperature_range = (
            self.daily_max_temperature
            - self.daily_min_temperature
        )

        warmth = (
            (self.temperature - self.daily_min_temperature)
            / temperature_range
            if temperature_range > 0
            else 0.5
        )

        humidity_swing = float(
            self.settings["temperature_humidity_swing"]
        )

        humidity = self.daily_humidity + (
            0.5 - warmth
        ) * humidity_swing

        if is_raining:
            humidity += float(
                self.settings["rain_humidity_boost"]
            )

        self.humidity = max(0.0, min(100.0, humidity))

    def _generate_daily_profile(self, season: str) -> None:
        """Generate the temperature range and humidity baseline."""

        season_settings = self.settings["seasons"][season]

        min_range = season_settings["temperature_min_range"]
        max_range = season_settings["temperature_max_range"]
        humidity_range = season_settings["humidity_range"]

        self.daily_min_temperature = self.rng.uniform(
            float(min_range[0]),
            float(min_range[1]),
        )

        self.daily_max_temperature = self.rng.uniform(
            float(max_range[0]),
            float(max_range[1]),
        )

        if self.daily_max_temperature < self.daily_min_temperature:
            raise ValueError(
                f"Climate configuration for {season!r} allows "
                "daily maximum temperatures below daily minimums."
            )

        self.daily_humidity = self.rng.uniform(
            float(humidity_range[0]),
            float(humidity_range[1]),
        )

    def get_state(self) -> dict:
        """Return climate information for the API and frontend."""

        return {
            "temperature": round(self.temperature, 2),
            "humidity": round(self.humidity, 2),
            "daily_min_temperature": round(
                self.daily_min_temperature, 2
            ),
            "daily_max_temperature": round(
                self.daily_max_temperature, 2
            ),
        }
