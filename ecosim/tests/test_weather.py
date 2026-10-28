
"""Tests for EcoSim weather simulation."""

from copy import deepcopy

import pytest

from ecosim.config.loader import load_config
from ecosim.simulation.terrain import TerrainSimulation
from ecosim.simulation.weather import WeatherSimulation


@pytest.fixture
def config():
    """Return an independent copy of the project configuration."""
    return deepcopy(load_config())


def test_weather_starts_clear(config):
    weather = WeatherSimulation(
        settings=config["weather"],
        seed=42,
    )

    assert weather.is_raining is False
    assert weather.intensity == "none"
    assert weather.rain_ticks_remaining == 0


def test_rain_starts_when_chance_is_certain(config):
    settings = config["weather"]

    settings["rain_chance_per_tick"]["spring"] = 1.0
    settings["minimum_duration_ticks"] = 3
    settings["maximum_duration_ticks"] = 3

    weather = WeatherSimulation(
        settings=settings,
        seed=42,
    )

    weather.tick("spring")

    assert weather.is_raining is True
    assert weather.intensity in {"light", "moderate", "heavy"}
    assert weather.rain_ticks_remaining == 3


def test_rain_increases_soil_moisture(config):
    config["terrain_simulation"]["grass_moisture"] = 0.5
    config["terrain_simulation"]["moisture_diffusion"] = 0.0
    config["soil_climate"]["base_evaporation_rate"] = 0.0

    terrain = TerrainSimulation(
        [["grass"]],
        config,
        seed=42,
    )

    initial_moisture = terrain.moisture[0][0]

    terrain.tick(
        season="spring",
        rain_amount=0.1,
        temperature=15.0,
        humidity=60.0,
        wind_strength=0.0,
    )

    assert terrain.moisture[0][0] > initial_moisture
    assert terrain.moisture[0][0] == pytest.approx(0.6)


def test_rain_amount_depends_on_intensity(config):
    settings = config["weather"]
    weather = WeatherSimulation(settings=settings, seed=42)

    weather.is_raining = True

    weather.intensity = "light"
    light_amount = weather.rain_amount

    weather.intensity = "moderate"
    moderate_amount = weather.rain_amount

    weather.intensity = "heavy"
    heavy_amount = weather.rain_amount

    assert light_amount < moderate_amount < heavy_amount


def test_wind_stays_within_configured_limits(config):
    settings = config["weather"]

    weather = WeatherSimulation(
        settings=settings,
        seed=42,
    )

    for _ in range(100):
        weather.tick("spring")

        assert (
            settings["wind"]["minimum_strength"]
            <= weather.wind_strength
            <= settings["wind"]["maximum_strength"]
        )


def test_rain_stops_after_duration(config):
    settings = config["weather"]
    settings["rain_chance_per_tick"]["spring"] = 1.0
    settings["minimum_duration_ticks"] = 2
    settings["maximum_duration_ticks"] = 2

    weather = WeatherSimulation(
        settings=settings,
        seed=42,
    )

    weather.tick("spring")
    assert weather.is_raining is True

    weather.tick("spring")
    assert weather.is_raining is True

    weather.tick("spring")
    assert weather.is_raining is False
    assert weather.intensity == "none"
