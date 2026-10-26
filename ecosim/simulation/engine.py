
from dataclasses import dataclass, field

from ecosim.simulation.clock import SimulationClock
from ecosim.simulation.terrain import TerrainSimulation
from ecosim.simulation.weather import WeatherSimulation


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

    def load_world(
        self,
        tiles: list[list[str]],
        terrain_settings: dict | None = None,
        weather_settings: dict | None = None,
        seed: int | None = None,
    ) -> None:
        self.terrain = TerrainSimulation(
            tiles,
            settings=terrain_settings or {},
        )
        self.weather = WeatherSimulation(
            settings=weather_settings or {},
            seed=seed,
        )

    def tick(self) -> dict:
        season = self.clock.season
        self.weather.tick(season)

        self.clock.tick()

        if self.terrain is not None:
            self.terrain.tick(
                season,
                rain_amount=self.weather.rain_amount,
            )

        return self.get_state()

    def get_state(self) -> dict:
        return {
            **self.clock.to_dict(),
            **self.weather.get_state(),
            "running": self.running,
            "world_loaded": self.terrain is not None,
    }
