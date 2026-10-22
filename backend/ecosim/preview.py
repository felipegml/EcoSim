
"""Generate a browser-based preview of an Eco-Sim world."""

import argparse
import json
from pathlib import Path

from backend.ecosim.config import WorldConfig
from backend.ecosim.simulation import Simulation
from backend.ecosim.world import Terrain


COLORS = {
    Terrain.DIRT: "#9b7048",
    Terrain.GRASS: "#55a85f",
    Terrain.WATER: "#3998d6",
}


def create_html(seed: int) -> str:
    config = WorldConfig(seed=seed)
    simulation = Simulation.create(config)
    world = simulation.world

    terrain = [
        [cell.terrain.value for cell in row]
        for row in world.cells
    ]

    counts = {
        terrain_type.value: world.count_terrain(terrain_type)
        for terrain_type in Terrain
    }

    terrain_json = json.dumps(terrain)
    colors_json = json.dumps({
        terrain_type.value: color
        for terrain_type, color in COLORS.items()
    })
    counts_json = json.dumps(counts)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Eco-Sim World Preview</title>
<style>
body {{
    margin: 0;
    padding: 24px;
    background: #18211c;
    color: #f1f5f2;
    font-family: system-ui, sans-serif;
}}
main {{ max-width: 850px; margin: auto; }}
h1 {{ margin-bottom: 6px; }}
p {{ color: #bdc9c0; }}
canvas {{
    display: block;
    width: min(100%, 700px);
    height: auto;
    image-rendering: pixelated;
    border: 2px solid #657569;
    border-radius: 4px;
    margin: 20px 0;
}}
.stats, .legend {{
    display: flex;
    flex-wrap: wrap;
    gap: 18px;
    margin: 16px 0;
}}
.swatch {{
    display: inline-block;
    width: 12px;
    height: 12px;
    margin-right: 6px;
}}
</style>
</head>
<body>
<main>
<h1>Eco-Sim</h1>
<p>Generated world · Seed: {seed} ·
{config.width} × {config.height} cells</p>

<div class="legend">
<span><i class="swatch" style="background:#9b7048"></i>Dirt</span>
<span><i class="swatch" style="background:#55a85f"></i>Grass</span>
<span><i class="swatch" style="background:#3998d6"></i>Water</span>
</div>

<canvas id="world" width="700" height="700"
aria-label="Top-down ecosystem terrain map"></canvas>

<h2>Terrain statistics</h2>
<div class="stats" id="stats"></div>
<p>Static preview of the Python simulation world.
Animals and interactive controls will come later.</p>
</main>

<script>
const terrain = {terrain_json};
const colors = {colors_json};
const counts = {counts_json};
const canvas = document.getElementById("world");
const ctx = canvas.getContext("2d");
const cellSize = canvas.width / terrain[0].length;

for (let y = 0; y < terrain.length; y++) {{
    for (let x = 0; x < terrain[y].length; x++) {{
        ctx.fillStyle = colors[terrain[y][x]];
        ctx.fillRect(
            x * cellSize,
            y * cellSize,
            Math.ceil(cellSize),
            Math.ceil(cellSize)
        );
    }}
}}

document.getElementById("stats").innerHTML =
    Object.entries(counts).map(([name, count]) =>
        `<span><strong>${{name}}:</strong> ${{count}}
        (${{(count / terrain.length / terrain[0].length * 100).toFixed(1)}}%)</span>`
    ).join("");
</script>
</body>
</html>"""


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a visual preview of an Eco-Sim world."
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("map_preview.html"),
    )
    args = parser.parse_args()

    args.output.write_text(create_html(args.seed), encoding="utf-8")
    print(f"Map preview created: {args.output.resolve()}")
    print("Open this HTML file in your browser.")


if __name__ == "__main__":
    main()
