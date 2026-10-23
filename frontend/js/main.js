
const canvas = document.getElementById("world-map");
const context = canvas.getContext("2d");

const worldSize = document.getElementById("world-size");
const worldStatus = document.getElementById("world-status");

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

loadWorld();
