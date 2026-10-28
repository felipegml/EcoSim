
"""Coordinate the clock, climate, weather, and terrain systems."""

from dataclasses import dataclass, field
import math

from ecosim.config.loader import load_config
from ecosim.simulation.clock import SimulationClock
from ecosim.simulation.climate import ClimateSimulation
from ecosim.simulation.terrain import TerrainSimulation
from ecosim.simulation.weather import WeatherSimulation


@dataclass
class SimulationEngine:
    clock: SimulationClock = field(init=False)
    climate: ClimateSimulation = field(init=False)
    weather: WeatherSimulation = field(init=False)
    terrain: TerrainSimulation | None = None

    running: bool = False
    config: dict = field(init=False, repr=False)

    def __post_init__(self) -> None:
        """Load configuration and initialize simulation systems."""
        self.config = load_config()
        self._initialize_systems()

    def _initialize_systems(self) -> None:
        """Create the clock, climate, and weather systems."""
        self.clock = SimulationClock(
            seasons=self.config["seasons"],
            day_night=self.config["day_night"],
        )

        simulation_seed = self.config["world"].get("seed")

        self.climate = ClimateSimulation(
            settings=self.config["climate"],
            seed=simulation_seed,
        )

        self.weather = WeatherSimulation(
            settings=self.config["weather"],
            seed=simulation_seed,
        )

        self.climate.update(
            day=self.clock.day,
            hour=self.clock.hour,
            season=self.clock.season,
            is_raining=False,
        )

    def start(self) -> None:
        """Allow the simulation to run."""
        self.running = True

    def pause(self) -> None:
        """Pause the simulation."""
        self.running = False

    def reset(self) -> None:
        """Reset the clock and environmental systems."""
        self.running = False
        self.terrain = None
        self._initialize_systems()

    def set_speed(self, ticks_per_second: float) -> None:
        """Update the configured simulation tick rate."""
        if (
            isinstance(ticks_per_second, bool)
            or not isinstance(ticks_per_second, (int, float))
            or not math.isfinite(ticks_per_second)
            or ticks_per_second <= 0
        ):
            raise ValueError("Simulation speed must be a finite number greater than zero.")

        self.config["simulation"]["ticks_per_second"] = float(
            ticks_per_second
        )

    def load_world(
        self,
        tiles: list[list[str]],
        terrain_settings: dict | None = None,
        weather_settings: dict | None = None,
        seed: int | None = None,
    ) -> None:
        """Load terrain and optionally override weather settings."""
        if not tiles or not tiles[0]:
            raise ValueError("The terrain grid cannot be empty.")

        width = len(tiles[0])

        if any(len(row) != width for row in tiles):
            raise ValueError("Every terrain row must have the same width.")

        effective_seed = (
            self.config["world"].get("seed")
            if seed is None
            else seed
        )

        effective_terrain_settings = (
            self.config
            if terrain_settings is None
            else terrain_settings
        )

        self.terrain = TerrainSimulation(
            tiles=tiles,
            settings=effective_terrain_settings,
            seed=effective_seed,
        )

        effective_weather_settings = (
            weather_settings
            if weather_settings is not None
            else self.config["weather"]
        )

        self.weather = WeatherSimulation(
            settings=effective_weather_settings,
            seed=effective_seed,
        )

        self.climate = ClimateSimulation(
            settings=self.config["climate"],
            seed=effective_seed,
        )

        self.climate.update(
            day=self.clock.day,
            hour=self.clock.hour,
            season=self.clock.season,
            is_raining=False,
        )

    def tick(self) -> dict:
        """Advance one simulated hour if the simulation is running."""
        if not self.running:
            return self.get_state()

        current_season = self.clock.season
        current_day = self.clock.day
        current_hour = self.clock.hour

        # 1. Update weather for this simulated hour.
        self.weather.tick(current_season)

        # 2. Calculate the climate for this hour.
        self.climate.update(
            day=current_day,
            hour=current_hour,
            season=current_season,
            is_raining=self.weather.is_raining,
        )

        # 3. Apply environmental conditions to the terrain.
        if self.terrain is not None:
            self.terrain.tick(
                season=current_season,
                rain_amount=self.weather.rain_amount,
                temperature=self.climate.temperature,
                humidity=self.climate.humidity,
                wind_strength=self.weather.wind_strength,
            )

        # 4. Advance the clock after processing the current hour.
        self.clock.tick()

        return self.get_state()

    def get_state(self) -> dict:
        """Return the combined simulation state."""
        state = {
            **self.clock.to_dict(),
            **self.climate.get_state(),
            **self.weather.get_state(),
            "running": self.running,
            "world_loaded": self.terrain is not None,
        }

        if self.terrain is not None:
            state["terrain"] = self.terrain.get_state()

        return state
