
"""Tests for EcoSim configuration loading and validation."""

import json

import pytest

from ecosim.config.loader import load_config
from ecosim.config.validator import validate_config


def test_load_config_from_default_path():
    """The project's default configuration should load successfully."""
    config = load_config()

    assert isinstance(config, dict)
    assert "world" in config
    assert "climate" in config
    assert "weather" in config
    assert "terrain_simulation" in config
    assert "grass" in config
    assert "seeds" in config


def test_load_config_from_custom_path(tmp_path):
    """The loader should read a supplied configuration path."""
    config_path = tmp_path / "config.json"

    # Use the real project configuration as a valid starting point.
    config = load_config()
    config_path.write_text(
        json.dumps(config),
        encoding="utf-8",
    )

    loaded_config = load_config(config_path)

    assert loaded_config == config


def test_load_config_missing_file(tmp_path):
    """A missing configuration file should raise FileNotFoundError."""
    missing_path = tmp_path / "missing.json"

    with pytest.raises(FileNotFoundError):
        load_config(missing_path)


def test_load_config_invalid_json(tmp_path):
    """Malformed JSON should raise a useful ValueError."""
    config_path = tmp_path / "invalid.json"
    config_path.write_text(
        '{"world": ',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Invalid JSON"):
        load_config(config_path)


def test_load_config_root_must_be_object(tmp_path):
    """The JSON root must be an object, not a list or scalar."""
    config_path = tmp_path / "root.json"
    config_path.write_text(
        json.dumps([]),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="root must be a JSON object"):
        load_config(config_path)


def test_validator_accepts_valid_config():
    """The validator should accept the project's valid configuration."""
    config = load_config()

    validate_config(config)


def test_validator_rejects_missing_required_section():
    """Removing a required section should invalidate the configuration."""
    config = load_config()
    config.pop("climate")

    with pytest.raises(ValueError):
        validate_config(config)


def test_validator_rejects_invalid_world_dimensions():
    """World dimensions must satisfy the validator's constraints."""
    config = load_config()
    config["world"]["width"] = 0

    with pytest.raises(ValueError):
        validate_config(config)


def test_validator_rejects_invalid_moisture():
    """Initial soil moisture must remain within its permitted range."""
    config = load_config()
    config["terrain_simulation"]["grass_moisture"] = 1.5

    with pytest.raises(ValueError):
        validate_config(config)


def test_validator_rejects_invalid_rain_chance():
    """Rain probabilities must be between zero and one."""
    config = load_config()
    config["weather"]["rain_chance_per_tick"]["summer"] = 1.5

    with pytest.raises(ValueError):
        validate_config(config)
