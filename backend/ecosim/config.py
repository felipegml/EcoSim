"""Configuration for the Eco-Sim world."""

from dataclasses import dataclass


@dataclass(frozen=True)
class WorldConfig:
    width: int = 100
    height: int = 100
    seed: int = 42
    grass_coverage: float = 0.45
    water_coverage: float = 0.10
    grass_regrowth_chance: float = 0.01

    def __post_init__(self) -> None:
        if self.width < 1 or self.height < 1:
            raise ValueError("World dimensions must be positive.")

        if not 0 <= self.grass_coverage <= 1:
            raise ValueError("Grass coverage must be between 0 and 1.")

        if not 0 <= self.water_coverage <= 1:
            raise ValueError("Water coverage must be between 0 and 1.")

        if self.grass_coverage + self.water_coverage > 1:
            raise ValueError("Grass and water coverage cannot exceed 100%.")

        if not 0 <= self.grass_regrowth_chance <= 1:
            raise ValueError("Regrowth chance must be between 0 and 1.")