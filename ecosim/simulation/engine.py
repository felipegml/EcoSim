
from dataclasses import dataclass, field

from ecosim.simulation.clock import SimulationClock


@dataclass
class SimulationEngine:
    clock: SimulationClock = field(default_factory=SimulationClock)
    running: bool = False

    def start(self) -> None:
        self.running = True

    def pause(self) -> None:
        self.running = False

    def tick(self) -> dict:
        self.clock.tick()
        return self.get_state()

    def get_state(self) -> dict:
        return {
            **self.clock.to_dict(),
            "running": self.running,
        }
    
    def reset(self) -> None:
        """Reset the simulation clock and pause the simulation."""
        self.clock = SimulationClock()
        self.running = False
        