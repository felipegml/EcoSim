
const canvas = document.getElementById("world-map");
const context = canvas.getContext("2d");

const worldSize = document.getElementById("world-size");
const worldStatus = document.getElementById("world-status");
const terrainStats = document.getElementById("terrain-stats");

const terrainColors = {
    grass: "#65a85c",
    dirt: "#b48a60",
    water: "#398bc4",
    stone: "#929a9a",
};

async function loadWorld() {
    try {
        const response = await fetch("/world.json");

        if (!response.ok) {
            throw new Error("Could not load world.json");
        }

        const world = await response.json();

        drawWorld(world);
        renderTerrainStats(world);
        worldSize.textContent = `${world.width} × ${world.height}`;
        worldStatus.textContent = "World loaded";
    } catch (error) {
        worldStatus.textContent = "Could not load world";
        console.error(error);
    }
}

function drawWorld(world) {
    const tileSize = 20;

    canvas.width = world.width * tileSize;
    canvas.height = world.height * tileSize;

    world.tiles.forEach((row, y) => {
        row.forEach((terrain, x) => {
            context.fillStyle = terrainColors[terrain] ?? "#ff00ff";

            context.fillRect(
                x * tileSize,
                y * tileSize,
                tileSize,
                tileSize
            );

            context.strokeStyle = "rgba(0, 0, 0, 0.12)";
            context.strokeRect(
                x * tileSize,
                y * tileSize,
                tileSize,
                tileSize
            );
        });
    });
}

function renderTerrainStats(world) {
    const counts = Object.fromEntries(
        Object.keys(terrainColors).map(terrain => [terrain, 0])
    );

    for (const row of world.tiles) {
        for (const terrain of row) {
            if (terrain in counts) {
                counts[terrain]++;
            }
        }
    }

    const total = world.width * world.height;
    terrainStats.replaceChildren();

    for (const [terrain, color] of Object.entries(terrainColors)) {
        const count = counts[terrain];
        const percentage = (count / total) * 100;

        const card = document.createElement("div");
        card.className = "terrain-stat";

        const label = document.createElement("div");
        label.className = "stat-label";

        const swatch = document.createElement("i");
        swatch.style.backgroundColor = color;

        const name = document.createElement("span");
        name.textContent =
            terrain.charAt(0).toUpperCase() + terrain.slice(1);

        label.append(swatch, name);

        const countElement = document.createElement("strong");
        countElement.className = "stat-count";
        countElement.textContent = count.toLocaleString();

        const percentElement = document.createElement("div");
        percentElement.className = "stat-percent";
        percentElement.textContent = `${percentage.toFixed(1)}% of world`;

        card.append(label, countElement, percentElement);
        terrainStats.append(card);
    }
}

loadWorld();
