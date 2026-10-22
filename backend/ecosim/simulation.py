"""Basic simulation clock and grass regrowth."""

from dataclasses import dataclass

from backend.ecosim.config import WorldConfig
from backend.ecosim.world import Terrain, World, generate_world


@dataclass
class Simulation:
    config: WorldConfig
    world: World
    tick: int = 0

    @classmethod
    def create(cls, config: WorldConfig) -> "Simulation":
        return cls(config=config, world=generate_world(config))

    def step(self) -> None:
        """Advance the simulation by one tick."""
        for row in self.world.cells:
            for cell in row:
                if cell.terrain == Terrain.DIRT:
                    if (
                        self.world.rng.random()
                        < self.config.grass_regrowth_chance
                    ):
                        cell.terrain = Terrain.GRASS

        self.tick += 1