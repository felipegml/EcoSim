import pytest

from ecosim.config.validator import validate_config


def test_valid_config():
    config = {
        "world": {"width": 40, "height": 25, "seed": 12345},
        "terrain_percentages": {
            "grass": 45,
            "dirt": 25,
            "water": 15,
            "stone": 15,
        },
    }

    validate_config(config)


def test_invalid_terrain_percentages():
    config = {
        "world": {"width": 40, "height": 25, "seed": 12345},
        "terrain_percentages": {"grass": 60, "water": 30},
    }

    with pytest.raises(ValueError):
        validate_config(config)