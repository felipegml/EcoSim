
"""Tests for the EcoSim simulation clock."""

import pytest

from ecosim.config.loader import load_config
from ecosim.simulation.clock import SimulationClock


@pytest.fixture
def clock_settings():
    """Load season and daylight settings from the project config."""
    config = load_config()

    return {
        "seasons": config["seasons"],
        "day_night": config["day_night"],
    }


def make_clock(clock_settings, **kwargs):
    """Create a clock using the current project configuration."""
    return SimulationClock(
        seasons=clock_settings["seasons"],
        day_night=clock_settings["day_night"],
        **kwargs,
    )


def test_clock_advances_one_hour(clock_settings):
    clock = make_clock(clock_settings)

    clock.tick()

    assert clock.hour == 1
    assert clock.day == 1
    assert clock.year == 1


def test_clock_advances_day(clock_settings):
    clock = make_clock(
        clock_settings,
        hour=23,
        day=1,
        year=1,
    )

    clock.tick()

    assert clock.hour == 0
    assert clock.day == 2
    assert clock.year == 1


def test_clock_advances_year(clock_settings):
    days_per_year = sum(clock_settings["seasons"].values())

    clock = make_clock(
        clock_settings,
        hour=23,
        day=days_per_year,
        year=1,
    )

    clock.tick()

    assert clock.hour == 0
    assert clock.day == 1
    assert clock.year == 2


def test_season_boundaries(clock_settings):
    clock = make_clock(clock_settings)

    first_day = 1

    for season_name, duration in clock_settings["seasons"].items():
        clock.day = first_day
        assert clock.season == season_name

        clock.day = first_day + duration - 1
        assert clock.season == season_name

        first_day += duration

    # The next day after the final season starts a new year.
    clock.day = 1
    clock.year += 1
    assert clock.season == next(iter(clock_settings["seasons"]))


def test_day_night_cycle(clock_settings):
    clock = make_clock(clock_settings)

    season_settings = clock_settings["day_night"]["spring"]
    sunrise = season_settings["sunrise"]
    sunset = season_settings["sunset"]

    clock.day = 1
    clock.hour = sunrise - 1
    assert not clock.is_daytime

    clock.hour = sunrise
    assert clock.is_daytime

    clock.hour = sunset - 1
    assert clock.is_daytime

    clock.hour = sunset % 24
    assert not clock.is_daytime


def test_clock_rejects_invalid_hour(clock_settings):
    with pytest.raises(ValueError):
        make_clock(clock_settings, hour=24)


def test_clock_rejects_invalid_day(clock_settings):
    days_per_year = sum(clock_settings["seasons"].values())

    with pytest.raises(ValueError):
        make_clock(
            clock_settings,
            day=days_per_year + 1,
        )
