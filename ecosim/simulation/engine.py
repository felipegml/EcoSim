
from dataclasses import dataclass, field

from ecosim.simulation.clock import SimulationClock
from ecosim.simulation.terrain import TerrainSimulation


@dataclass
class SimulationEngine:
    clock: SimulationClock = field(default_factory=SimulationClock)
    running: bool = False
    terrain: TerrainSimulation | None = None

    def start(self) -> None:
        self.running = True

    def pause(self) -> None:
        self.running = False

    def reset(self) -> None:
        self.clock = SimulationClock()
        self.running = False

    def load_world(self, tiles: list[list[str]]) -> None:
        self.terrain = TerrainSimulation(tiles)

    def tick(self) -> dict:
        self.clock.tick()

        if self.terrain is not None:
            self.terrain.tick()

        return self.get_state()

    def get_state(self) -> dict:
        return {
            **self.clock.to_dict(),
            "running": self.running,
            "world_loaded": self.terrain is not None,
        }
