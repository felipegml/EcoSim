
from ecosim.simulation.clock import SimulationClock


def test_clock_advances_one_hour():
    clock = SimulationClock()

    clock.tick()

    assert clock.hour == 1
    assert clock.day == 1
    assert clock.year == 1


def test_clock_advances_day():
    clock = SimulationClock(hour=23, day=1, year=1)

    clock.tick()

    assert clock.hour == 0
    assert clock.day == 2


def test_clock_advances_year():
    clock = SimulationClock(hour=23, day=365, year=1)

    clock.tick()

    assert clock.hour == 0
    assert clock.day == 1
    assert clock.year == 2


def test_season_boundaries():
    assert SimulationClock(day=1).season == "spring"
    assert SimulationClock(day=92).season == "summer"
    assert SimulationClock(day=184).season == "autumn"
    assert SimulationClock(day=275).season == "winter"
    assert SimulationClock(day=365).season == "winter"


def test_day_night_cycle():
    assert SimulationClock(hour=6).is_daytime
    assert not SimulationClock(hour=18).is_daytime
