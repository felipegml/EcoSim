
import json
import random
from pathlib import Path

from ecosim.config.loader import load_config
from ecosim.config.validator import validate_config
from ecosim.world.generator import generate_world


def main() -> None:
    config = load_config()
    validate_config(config)

    if config["world"]["seed"] is None:
        config["world"]["seed"] = random.SystemRandom().randrange(
            0, 2**32
        )

    print(f"World seed: {config['world']['seed']}")

    world = generate_world(config)

    project_root = Path(__file__).resolve().parents[1]
    output_path = project_root / "frontend" / "world.json"

    world_data = {
        "width": len(world[0]),
        "height": len(world),
        "seed": config["world"]["seed"],
        "tiles": world,
    }

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(world_data, file)

    print(f"World exported to {output_path}")

    print("EcoSim world generated!")
    print(f"World size: {len(world[0])} x {len(world)}")
    print()

if __name__ == "__main__":
    main()
