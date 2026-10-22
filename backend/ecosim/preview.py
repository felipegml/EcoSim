
import argparse
import json
from pathlib import Path

from backend.ecosim.config import WorldConfig
from backend.ecosim.simulation import Simulation
from backend.ecosim.world import Terrain


TERRAIN_CODES = {
    Terrain.DIRT: "d",
    Terrain.GRASS: "g",
    Terrain.WATER: "w",
}


def take_snapshot(simulation: Simulation) -> dict:
    world = simulation.world

    terrain = "".join(
        TERRAIN_CODES[cell.terrain]
        for row in world.cells
        for cell in row
    )

    animals = [
        {
            "id": animal.id,
            "species": animal.species.value,
            "x": animal.x,
            "y": animal.y,
            "energy": round(animal.energy, 1),
        }
        for animal in simulation.animals
    ]

    return {
        "tick": simulation.tick,
        "terrain": terrain,
        "animals": animals,
    }


def create_html(seed: int = 42, ticks: int = 100) -> str:
    if ticks < 0:
        raise ValueError("Ticks cannot be negative.")

    config = WorldConfig(seed=seed)
    simulation = Simulation.create(config)
    snapshots = [take_snapshot(simulation)]

    for _ in range(ticks):
        simulation.step()
        snapshots.append(take_snapshot(simulation))

    template = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Eco-Sim Live Preview</title>
<style>
body {
    font-family: Arial, sans-serif;
    background: #f2f3ee;
    color: #263328;
    margin: 24px;
}
.layout {
    display: flex;
    flex-wrap: wrap;
    gap: 24px;
    align-items: flex-start;
}
canvas {
    width: min(700px, 90vw);
    height: min(700px, 90vw);
    border: 2px solid #394a38;
    image-rendering: pixelated;
}
.panel {
    background: white;
    padding: 16px;
    border-radius: 8px;
    min-width: 220px;
}
button {
    padding: 9px 12px;
    margin: 4px 2px;
    cursor: pointer;
}
input[type="range"] { width: 100%; }
.stat { margin: 12px 0; }
.swatch, .animal-dot {
    display: inline-block;
    width: 13px;
    height: 13px;
    margin-right: 8px;
    vertical-align: middle;
    border-radius: 3px;
}
.animal-dot { border-radius: 50%; }
.muted { color: #657065; font-size: 13px; }
</style>
</head>
<body>
<h1>Eco-Sim World</h1>
<p>Seed: __SEED__ · __WIDTH__ × __HEIGHT__ tiles</p>

<div class="layout">
    <div>
        <canvas id="map" width="700" height="700"></canvas>
        <p id="tick-label">Tick 0</p>
        <input id="tick-slider" type="range" min="0"
               max="__MAX_TICK__" value="0">
        <div>
            <button id="previous">◀ Previous Tick</button>
            <button id="play">▶ Play</button>
            <button id="next">Next Tick ▶</button>
        </div>
        <p class="muted">Snapshots are precomputed by Python.</p>
    </div>

    <section class="panel">
        <h2>Terrain</h2>
        <div class="stat">
            <span class="swatch" style="background:#9b7048"></span>
            Dirt: <strong id="dirt-count"></strong>
        </div>
        <div class="stat">
            <span class="swatch" style="background:#55a85f"></span>
            Grass: <strong id="grass-count"></strong>
        </div>
        <div class="stat">
            <span class="swatch" style="background:#3998d6"></span>
            Water: <strong id="water-count"></strong>
        </div>
        <h2>Animals</h2>
        <div class="stat">
            <span class="animal-dot" style="background:#146b35"></span>
            Herbivores: <strong id="herbivore-count"></strong>
        </div>
        <div class="stat">
            <span class="animal-dot" style="background:#d93636"></span>
            Predators: <strong id="predator-count"></strong>
        </div>
        <div class="stat">
            Average herbivore energy:
            <strong id="average-energy"></strong>
        </div>
    </section>
</div>

<script>
const WIDTH = __WIDTH__;
const HEIGHT = __HEIGHT__;
const snapshots = __SNAPSHOTS__;

const canvas = document.getElementById("map");
const ctx = canvas.getContext("2d");
const slider = document.getElementById("tick-slider");
const playButton = document.getElementById("play");

const colors = {
    d: "#9b7048",
    g: "#55a85f",
    w: "#3998d6"
};

let currentTick = 0;
let playing = false;
let timer = null;

function render(tick) {
    currentTick = Math.max(0, Math.min(tick, snapshots.length - 1));
    const snapshot = snapshots[currentTick];

    slider.value = currentTick;
    document.getElementById("tick-label").textContent =
        `Tick ${snapshot.tick} / ${snapshots.length - 1}`;

    const tileWidth = canvas.width / WIDTH;
    const tileHeight = canvas.height / HEIGHT;

    for (let y = 0; y < HEIGHT; y++) {
        for (let x = 0; x < WIDTH; x++) {
            ctx.fillStyle = colors[snapshot.terrain[y * WIDTH + x]];
            ctx.fillRect(
                x * tileWidth, y * tileHeight,
                tileWidth + 0.2, tileHeight + 0.2
            );
        }
    }

    for (const animal of snapshot.animals) {
        const cx = (animal.x + 0.5) * tileWidth;
        const cy = (animal.y + 0.5) * tileHeight;
        const radius = Math.max(2, Math.min(tileWidth, tileHeight) * 0.42);

        ctx.beginPath();
        ctx.arc(cx, cy, radius, 0, Math.PI * 2);
        ctx.fillStyle = animal.species === "herbivore"
            ? "#146b35" : "#d93636";
        ctx.fill();
        ctx.lineWidth = 1;
        ctx.strokeStyle = "#ffffff";
        ctx.stroke();
    }

    const counts = {d: 0, g: 0, w: 0};
    for (const code of snapshot.terrain) counts[code]++;

    document.getElementById("dirt-count").textContent = counts.d;
    document.getElementById("grass-count").textContent = counts.g;
    document.getElementById("water-count").textContent = counts.w;

    const herbivores = snapshot.animals.filter(
        a => a.species === "herbivore"
    );
    const predators = snapshot.animals.filter(
        a => a.species === "predator"
    );

    document.getElementById("herbivore-count").textContent = herbivores.length;
    document.getElementById("predator-count").textContent = predators.length;

    const energy = herbivores.length
        ? herbivores.reduce((sum, a) => sum + a.energy, 0) / herbivores.length
        : 0;

    document.getElementById("average-energy").textContent = energy.toFixed(1);
}

function stopPlaying() {
    playing = false;
    if (timer !== null) clearInterval(timer);
    timer = null;
    playButton.textContent = "▶ Play";
}

function startPlaying() {
    if (currentTick >= snapshots.length - 1) render(0);

    playing = true;
    playButton.textContent = "⏸ Pause";

    timer = setInterval(() => {
        if (currentTick >= snapshots.length - 1) {
            stopPlaying();
            return;
        }
        render(currentTick + 1);
    }, 250);
}

playButton.addEventListener("click", () => {
    if (playing) stopPlaying();
    else startPlaying();
});

document.getElementById("previous").addEventListener("click", () => {
    stopPlaying();
    render(currentTick - 1);
});

document.getElementById("next").addEventListener("click", () => {
    stopPlaying();
    render(currentTick + 1);
});

slider.addEventListener("input", () => {
    stopPlaying();
    render(Number(slider.value));
});

render(0);
</script>
</body>
</html>"""

    replacements = {
        "__SEED__": str(seed),
        "__WIDTH__": str(config.width),
        "__HEIGHT__": str(config.height),
        "__MAX_TICK__": str(ticks),
        "__SNAPSHOTS__": json.dumps(snapshots, separators=(",", ":")),
    }

    for placeholder, value in replacements.items():
        template = template.replace(placeholder, value)

    return template


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a playable Eco-Sim HTML preview."
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--ticks", type=int, default=100)
    parser.add_argument("--output", default="map_preview.html")
    args = parser.parse_args()

    output_path = Path(args.output)
    output_path.write_text(
        create_html(seed=args.seed, ticks=args.ticks),
        encoding="utf-8",
    )

    print(f"Preview saved to: {output_path.resolve()}")
    print(f"Precomputed ticks: 0 to {args.ticks}")


if __name__ == "__main__":
    main()
