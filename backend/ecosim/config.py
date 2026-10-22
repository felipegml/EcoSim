
from dataclasses import dataclass


@dataclass(frozen=True)
class WorldConfig:
    width: int = 100
    height: int = 100
    seed: int = 42

    grass_coverage: float = 0.45
    water_coverage: float = 0.10
    grass_regrowth_chance: float = 0.01
    water_patch_count: int = 5

    herbivore_count: int = 30
    predator_count: int = 5

    def __post_init__(self) -> None:
        if self.width <= 0 or self.height <= 0:
            raise ValueError("World dimensions must be positive.")

        if not 0 <= self.grass_coverage <= 1:
            raise ValueError("Grass coverage must be between 0 and 1.")

        if not 0 <= self.water_coverage <= 1:
            raise ValueError("Water coverage must be between 0 and 1.")

        if self.grass_coverage + self.water_coverage > 1:
            raise ValueError(
                "Grass and water coverage cannot exceed 100%."
            )

        if not 0 <= self.grass_regrowth_chance <= 1:
            raise ValueError(
                "Grass regrowth chance must be between 0 and 1."
            )

        if self.water_patch_count <= 0:
            raise ValueError("Water patch count must be positive.")

        if self.herbivore_count < 0 or self.predator_count < 0:
            raise ValueError("Animal counts cannot be negative.")

        total_animals = self.herbivore_count + self.predator_count
        total_water = round(
            self.width * self.height * self.water_coverage
        )

        if total_animals > self.width * self.height - total_water:
            raise ValueError(
                "There must be enough land tiles for all animals."
            )
