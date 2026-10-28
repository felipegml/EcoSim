
"""Load and validate EcoSim configuration."""

import json
from pathlib import Path
from typing import Any

from ecosim.config.validator import validate_config


def load_config(
    path: str | Path | None = None,
) -> dict[str, Any]:
    """Load configuration from JSON and validate its structure.

    Args:
        path: Optional path to a configuration file.
              If omitted, the project's root config.json is used.

    Returns:
        The validated configuration dictionary.

    Raises:
        FileNotFoundError: If the configuration file does not exist.
        ValueError: If the JSON is invalid or configuration validation fails.
    """

    if path is None:
        config_path = (
            Path(__file__).resolve().parents[2] / "config.json"
        )
    else:
        config_path = Path(path).expanduser().resolve()

    if not config_path.is_file():
        raise FileNotFoundError(
            f"Configuration file not found: {config_path}"
        )

    try:
        with config_path.open("r", encoding="utf-8") as config_file:
            config = json.load(config_file)
    except json.JSONDecodeError as error:
        raise ValueError(
            f"Invalid JSON in configuration file "
            f"{config_path} at line {error.lineno}, "
            f"column {error.colno}: {error.msg}"
        ) from error

    if not isinstance(config, dict):
        raise ValueError(
            f"Configuration root must be a JSON object: {config_path}"
        )

    validate_config(config)

    return config