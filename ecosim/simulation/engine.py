
"""Coordinate the clock, climate, weather, and terrain systems."""

from dataclasses import dataclass, field

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

        simulation_seed = self.config["world"]["seed"]

        self.climate = ClimateSimulation(
            settings=self.config["climate"],
            seed=simulation_seed,
        )

        self.weather = WeatherSimulation(
            settings=self.config["weather"],
            seed=simulation_seed,
        )

        # Initialize climate for the first simulated hour.
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

    def load_world(
        self,
        tiles: list[list[str]],
        terrain_settings: dict | None = None,
        weather_settings: dict | None = None,
        seed: int | None = None,
    ) -> None:
        """Load terrain and optionally override weather settings."""

        effective_seed = (
            self.config["world"]["seed"]
            if seed is None
            else seed
        )

        # Terrain requires the complete configuration because it
        # reads terrain, grass, soil-climate, and seed settings.
        self.terrain = TerrainSimulation(
            tiles=tiles,
            settings=self.config,
            seed=effective_seed,
        )

        # Optional overrides allow callers to customize weather
        # without changing the main configuration file.
        effective_weather_settings = (
            weather_settings
            if weather_settings is not None
            else self.config["weather"]
        )

        self.weather = WeatherSimulation(
            settings=effective_weather_settings,
            seed=effective_seed,
        )

        # Keep the climate's random sequence reproducible as well.
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
        """Advance one simulated hour."""

        if not self.running:
            return self.get_state()

        current_season = self.clock.season
        current_day = self.clock.day
        current_hour = self.clock.hour

        # 1. Update weather for this hour.
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
