"""Run a short Eco-Sim demonstration."""

from backend.ecosim.config import WorldConfig
from backend.ecosim.simulation import Simulation
from backend.ecosim.world import Terrain


def main() -> None:
    config = WorldConfig()
    simulation = Simulation.create(config)

    print("Eco-Sim initialized")
    print(f"World size: {config.width} x {config.height}")
    print(f"Random seed: {config.seed}")
    print(f"Initial grass: {simulation.world.count_terrain(Terrain.GRASS)}")
    print(f"Initial water: {simulation.world.count_terrain(Terrain.WATER)}")
    print(f"Initial dirt: {simulation.world.count_terrain(Terrain.DIRT)}")

    for _ in range(10):
        simulation.step()

    print(f"Simulation tick: {simulation.tick}")
    print(f"Grass after 10 ticks: {simulation.world.count_terrain(Terrain.GRASS)}")


if __name__ == "__main__":
    main()