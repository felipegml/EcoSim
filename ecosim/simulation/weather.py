
import random
from dataclasses import dataclass, field


@dataclass
class WeatherSimulation:
    settings: dict = field(default_factory=dict)
    seed: int | None = None

    is_raining: bool = False
    intensity: str = "none"
    rain_ticks_remaining: int = 0

    rng: random.Random = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.rng = random.Random(self.seed)

    def tick(self, season: str) -> None:
        if self.is_raining:
            self.rain_ticks_remaining -= 1

            if self.rain_ticks_remaining <= 0:
                self.is_raining = False
                self.intensity = "none"

            return

        chances = self.settings.get(
            "rain_chance_per_tick", {}
        )
        chance = chances.get(season, 0.02)

        if self.rng.random() < chance:
            minimum = self.settings.get(
                "minimum_duration_ticks", 3
            )
            maximum = self.settings.get(
                "maximum_duration_ticks", 12
            )

            self.rain_ticks_remaining = self.rng.randint(
                minimum, maximum
            )
            self.is_raining = True
            self.intensity = self.rng.choice(
                ["light", "moderate", "heavy"]
            )

    @property
    def rain_amount(self) -> float:
        if not self.is_raining:
            return 0.0

        multipliers = {
            "light": 0.5,
            "moderate": 1.0,
            "heavy": 1.5,
        }

        base = self.settings.get(
            "moisture_per_tick", 0.025
        )
        return base * multipliers[self.intensity]

    def get_state(self) -> dict:
        return {
            "is_raining": self.is_raining,
            "intensity": self.intensity,
            "rain_ticks_remaining": self.rain_ticks_remaining,
            "rain_amount": self.rain_amount,
        }
