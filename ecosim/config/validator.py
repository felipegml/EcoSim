
"""Validate EcoSim configuration before the simulation starts."""

from collections.abc import Mapping
from typing import Any


def _require_section(
    config: Mapping[str, Any],
    section_name: str,
) -> Mapping[str, Any]:
    """Return a required configuration section."""

    section = config.get(section_name)

    if not isinstance(section, Mapping):
        raise ValueError(
            f"Configuration section '{section_name}' "
            "must be an object."
        )

    return section


def _require_number(
    section: Mapping[str, Any],
    key: str,
    *,
    minimum: float | None = None,
    maximum: float | None = None,
) -> float:
    """Validate a numeric setting and return it as a float."""

    value = section.get(key)

    # bool is a subclass of int in Python, so reject it explicitly.
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(
            f"Configuration value '{key}' must be a number."
        )

    number = float(value)

    if minimum is not None and number < minimum:
        raise ValueError(
            f"Configuration value '{key}' must be at least {minimum}."
        )

    if maximum is not None and number > maximum:
        raise ValueError(
            f"Configuration value '{key}' must be at most {maximum}."
        )

    return number


def _require_integer(
    section: Mapping[str, Any],
    key: str,
    *,
    minimum: int | None = None,
) -> int:
    """Validate an integer setting."""

    value = section.get(key)

    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(
            f"Configuration value '{key}' must be an integer."
        )

    if minimum is not None and value < minimum:
        raise ValueError(
            f"Configuration value '{key}' must be at least {minimum}."
        )

    return value


def _require_range(
    section: Mapping[str, Any],
    key: str,
    *,
    minimum: float | None = None,
    maximum: float | None = None,
) -> tuple[float, float]:
    """Validate a two-number range."""

    value = section.get(key)

    if not isinstance(value, list) or len(value) != 2:
        raise ValueError(
            f"Configuration value '{key}' must contain "
            "exactly two numbers: [minimum, maximum]."
        )

    lower, upper = value

    for endpoint in (lower, upper):
        if isinstance(endpoint, bool) or not isinstance(
            endpoint, (int, float)
        ):
            raise ValueError(
                f"Both values in '{key}' must be numbers."
            )

    lower = float(lower)
    upper = float(upper)

    if lower > upper:
        raise ValueError(
            f"Configuration range '{key}' has its minimum "
            "greater than its maximum."
        )

    if minimum is not None and lower < minimum:
        raise ValueError(
            f"The minimum of '{key}' must be at least {minimum}."
        )

    if maximum is not None and upper > maximum:
        raise ValueError(
            f"The maximum of '{key}' must be at most {maximum}."
        )

    return lower, upper


def validate_config(config: dict[str, Any]) -> None:
    """Validate all required EcoSim configuration sections.

    Raises:
        ValueError: If a required setting is missing or invalid.
    """

    if not isinstance(config, dict):
        raise ValueError("Configuration root must be an object.")

    # World dimensions and generation settings.
    world = _require_section(config, "world")
    _require_integer(world, "width", minimum=1)
    _require_integer(world, "height", minimum=1)
    _require_integer(world, "water_smoothing_passes", minimum=0)

    world_seed = world.get("seed")
    if world_seed is not None and (
        isinstance(world_seed, bool)
        or not isinstance(world_seed, int)
    ):
        raise ValueError(
            "Configuration value 'world.seed' must be an "
            "integer or null."
        )

    simulation = _require_section(config, "simulation")
    _require_number(
        simulation, "ticks_per_second", minimum=0.000001
    )

    # Terrain-generation percentages must total 100.
    percentages = _require_section(config, "terrain_percentages")
    terrain_types = {"grass", "dirt", "water", "stone"}

    if set(percentages) != terrain_types:
        raise ValueError(
            "terrain_percentages must contain exactly: "
            "grass, dirt, water, and stone."
        )

    total_percentage = 0.0
    for key in terrain_types:
        total_percentage += _require_number(
            percentages, key, minimum=0.0, maximum=100.0
        )

    if abs(total_percentage - 100.0) > 1e-6:
        raise ValueError(
            "Terrain percentages must add up to 100."
        )

    # Season lengths and daylight settings.
    seasons = _require_section(config, "seasons")

    expected_seasons = {"spring", "summer", "autumn", "winter"}
    if set(seasons) != expected_seasons:
        raise ValueError(
            "seasons must contain spring, summer, autumn, and winter."
        )

    for name, duration in seasons.items():
        if (
            isinstance(duration, bool)
            or not isinstance(duration, int)
            or duration < 1
        ):
            raise ValueError(
                f"Season duration '{name}' must be a positive integer."
            )

    day_night = _require_section(config, "day_night")
    if set(day_night) != expected_seasons:
        raise ValueError(
            "day_night must contain all four seasons."
        )

    for season_name, settings in day_night.items():
        if not isinstance(settings, Mapping):
            raise ValueError(
                f"day_night.{season_name} must be an object."
            )

        sunrise = _require_integer(
            settings, "sunrise", minimum=0
        )
        sunset = _require_integer(
            settings, "sunset", minimum=0
        )

        if sunrise > 23 or sunset > 24 or sunrise >= sunset:
            raise ValueError(
                f"Invalid sunrise/sunset settings for {season_name}."
            )

    # Climate profiles.
    climate = _require_section(config, "climate")
    _require_number(
        climate, "temperature_humidity_swing", minimum=0.0
    )
    _require_number(
        climate, "rain_humidity_boost", minimum=0.0
    )

    climate_seasons = _require_section(climate, "seasons")
    if set(climate_seasons) != expected_seasons:
        raise ValueError(
            "climate.seasons must contain all four seasons."
        )

    for season_name, settings in climate_seasons.items():
        if not isinstance(settings, Mapping):
            raise ValueError(
                f"climate.seasons.{season_name} must be an object."
            )

        min_range = _require_range(
            settings, "temperature_min_range"
        )
        max_range = _require_range(
            settings, "temperature_max_range"
        )
        _require_range(
            settings, "humidity_range", minimum=0.0, maximum=100.0
        )

        if min_range[1] > max_range[0]:
            raise ValueError(
                f"Climate ranges for {season_name} can generate "
                "a daily minimum above the daily maximum."
            )

        _require_integer(
            settings, "temperature_minimum_hour", minimum=0
        )

        if settings["temperature_minimum_hour"] > 23:
            raise ValueError(
                f"temperature_minimum_hour for {season_name} "
                "must not exceed 23."
            )

    # Weather: rain and wind.
    weather = _require_section(config, "weather")
    rain_chances = _require_section(weather, "rain_chance_per_tick")

    if set(rain_chances) != expected_seasons:
        raise ValueError(
            "weather.rain_chance_per_tick must contain all four seasons."
        )

    for season_name, chance in rain_chances.items():
        _require_number(
            {"chance": chance},
            "chance",
            minimum=0.0,
            maximum=1.0,
        )

    minimum_duration = _require_integer(
        weather, "minimum_duration_ticks", minimum=1
    )
    maximum_duration = _require_integer(
        weather, "maximum_duration_ticks", minimum=1
    )

    if minimum_duration > maximum_duration:
        raise ValueError(
            "minimum_duration_ticks cannot exceed "
            "maximum_duration_ticks."
        )

    _require_number(weather, "moisture_per_tick", minimum=0.0)

    multipliers = _require_section(
        weather, "rain_intensity_multipliers"
    )

    if set(multipliers) != {"light", "moderate", "heavy"}:
        raise ValueError(
            "rain_intensity_multipliers must contain light, "
            "moderate, and heavy."
        )

    for intensity, multiplier in multipliers.items():
        _require_number(
            {"multiplier": multiplier},
            "multiplier",
            minimum=0.0,
        )

    wind = _require_section(weather, "wind")

    wind_minimum = _require_number(
        wind, "minimum_strength", minimum=0.0, maximum=1.0
    )
    wind_maximum = _require_number(
        wind, "maximum_strength", minimum=0.0, maximum=1.0
    )

    if wind_minimum > wind_maximum:
        raise ValueError(
            "Wind minimum_strength cannot exceed maximum_strength."
        )

    for key in ("initial_strength", "default_strength"):
        value = _require_number(
            wind, key, minimum=wind_minimum, maximum=wind_maximum
        )

    _require_number(
        wind, "hourly_variation", minimum=0.0
    )
    _require_number(
        wind, "adaptation_rate", minimum=0.0, maximum=1.0
    )

    seasonal_wind = _require_section(wind, "seasonal_strength")
    if set(seasonal_wind) != expected_seasons:
        raise ValueError(
            "wind.seasonal_strength must contain all four seasons."
        )

    for season_name, strength in seasonal_wind.items():
        _require_number(
            {"strength": strength},
            "strength",
            minimum=wind_minimum,
            maximum=wind_maximum,
        )

    # Terrain moisture values.
    terrain = _require_section(config, "terrain_simulation")
    _require_number(
        terrain, "moisture_diffusion", minimum=0.0, maximum=1.0
    )

    for key in (
        "water_moisture",
        "grass_moisture",
        "dirt_moisture",
        "stone_moisture",
    ):
        _require_number(terrain, key, minimum=0.0, maximum=1.0)

    # Temperature- and humidity-dependent soil evaporation.
    soil = _require_section(config, "soil_climate")

    _require_number(soil, "base_evaporation_rate", minimum=0.0)
    _require_number(soil, "reference_temperature")
    _require_number(soil, "temperature_sensitivity")
    _require_number(soil, "humidity_sensitivity", minimum=0.0)

    evaporation_minimum = _require_number(
        soil, "minimum_evaporation_factor", minimum=0.0
    )
    evaporation_maximum = _require_number(
        soil, "maximum_evaporation_factor", minimum=0.0
    )

    if evaporation_minimum > evaporation_maximum:
        raise ValueError(
            "minimum_evaporation_factor cannot exceed "
            "maximum_evaporation_factor."
        )

    # Grass health.
    grass = _require_section(config, "grass")

    _require_number(grass, "minimum_moisture", minimum=0.0, maximum=1.0)
    _require_number(grass, "health_loss", minimum=0.0, maximum=1.0)
    _require_number(grass, "health_recovery", minimum=0.0, maximum=1.0)
    _require_number(grass, "death_threshold", minimum=0.0, maximum=1.0)
    _require_number(grass, "initial_health", minimum=0.0, maximum=1.0)
    _require_range(grass, "health_temperature_range")

    # External seed arrival and germination.
    seeds = _require_section(config, "seeds")

    _require_number(
        seeds, "base_arrival_chance", minimum=0.0, maximum=1.0
    )
    _require_number(seeds, "wind_effect", minimum=0.0)
    _require_number(
        seeds, "maximum_arrival_chance", minimum=0.0, maximum=1.0
    )
    _require_number(
        seeds, "germination_chance", minimum=0.0, maximum=1.0
    )
    _require_number(
        seeds,
        "minimum_germination_moisture",
        minimum=0.0,
        maximum=1.0,
    )
    _require_range(seeds, "germination_temperature_range")

    if seeds["base_arrival_chance"] > seeds["maximum_arrival_chance"]:
        raise ValueError(
            "base_arrival_chance cannot exceed maximum_arrival_chance."
        )
