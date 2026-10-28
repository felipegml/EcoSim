
"""Simulate rain and wind."""

import random
from dataclasses import dataclass, field


@dataclass
class WeatherSimulation:
    settings: dict
    seed: int | None = None

    is_raining: bool = False
    intensity: str = "none"
    rain_ticks_remaining: int = 0
    wind_strength: float = 0.0

    rng: random.Random = field(init=False, repr=False)

    def __post_init__(self) -> None:
        """Initialize random state and configured wind strength."""

        self.rng = random.Random(self.seed)
        wind_settings = self.settings["wind"]

        self.wind_strength = float(
            wind_settings["initial_strength"]
        )

    def tick(self, season: str) -> None:
        """Advance rain and wind by one simulated hour."""

        self._update_wind(season)

        if self.is_raining:
            self.rain_ticks_remaining -= 1

            if self.rain_ticks_remaining <= 0:
                self.is_raining = False
                self.intensity = "none"
                self.rain_ticks_remaining = 0

            return

        chance = float(
            self.settings["rain_chance_per_tick"][season]
        )
        chance = max(0.0, min(1.0, chance))

        if self.rng.random() < chance:
            minimum = int(
                self.settings["minimum_duration_ticks"]
            )
            maximum = int(
                self.settings["maximum_duration_ticks"]
            )

            if minimum < 1 or maximum < minimum:
                raise ValueError(
                    "Rain duration configuration must satisfy "
                    "1 <= minimum_duration_ticks <= "
                    "maximum_duration_ticks."
                )

            self.rain_ticks_remaining = self.rng.randint(
                minimum, maximum
            )
            self.is_raining = True
            self.intensity = self.rng.choice(
                ["light", "moderate", "heavy"]
            )

    def _update_wind(self, season: str) -> None:
        """Gradually adjust wind toward its seasonal target."""

        wind_settings = self.settings["wind"]

        target = float(
            wind_settings["seasonal_strength"].get(
                season,
                wind_settings["default_strength"],
            )
        )

        variation = float(wind_settings["hourly_variation"])
        minimum = float(wind_settings["minimum_strength"])
        maximum = float(wind_settings["maximum_strength"])
        adaptation_rate = float(wind_settings["adaptation_rate"])

        if minimum > maximum:
            raise ValueError(
                "Wind minimum_strength cannot exceed maximum_strength."
            )

        if variation < 0:
            raise ValueError("Wind hourly_variation cannot be negative.")

        if not 0.0 <= adaptation_rate <= 1.0:
            raise ValueError(
                "Wind adaptation_rate must be between 0 and 1."
            )

        if not minimum <= target <= maximum:
            raise ValueError(
                "Seasonal wind target must be within wind limits."
            )

        self.wind_strength += (
            target - self.wind_strength
        ) * adaptation_rate

        self.wind_strength += self.rng.uniform(
            -variation, variation
        )

        self.wind_strength = max(
            minimum,
            min(maximum, self.wind_strength),
        )

    @property
    def rain_amount(self) -> float:
        """Calculate moisture supplied by rain this hour."""

        if not self.is_raining:
            return 0.0

        multipliers = self.settings["rain_intensity_multipliers"]

        if self.intensity not in multipliers:
            raise ValueError(
                f"Missing rain intensity multiplier: {self.intensity}"
            )

        base_amount = float(self.settings["moisture_per_tick"])
        multiplier = float(multipliers[self.intensity])

        return base_amount * multiplier

    def get_state(self) -> dict:
        """Return weather data for the API and frontend."""

        return {
            "is_raining": self.is_raining,
            "intensity": self.intensity,
            "rain_ticks_remaining": self.rain_ticks_remaining,
            "rain_amount": round(self.rain_amount, 4),
            "wind_strength": round(self.wind_strength, 3),
        }
