import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def load_config(path: str = "config.json") -> dict:
    config_path = PROJECT_ROOT / path

    with config_path.open("r", encoding="utf-8") as file:
        return json.load(file)