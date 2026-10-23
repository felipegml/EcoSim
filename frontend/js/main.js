
const canvas = document.getElementById("world-map");
const context = canvas.getContext("2d");

const worldSize = document.getElementById("world-size");
const worldStatus = document.getElementById("world-status");
const terrainStats = document.getElementById("terrain-stats");

const seedInput = document.getElementById("seed-input");
const waterSmoothingInput = document.getElementById("water-smoothing");
const generateButton = document.getElementById("generate-world");
const randomWorldButton = document.getElementById("generate-random-world");

const widthInput = document.getElementById("world-width");
const heightInput = document.getElementById("world-height");
const waterInput = document.getElementById("terrain-water");
const grassInput = document.getElementById("terrain-grass");
const stoneInput = document.getElementById("terrain-stone");
const dirtInput = document.getElementById("terrain-dirt");

const terrainColors = {
    grass: "#65a85c",
    dirt: "#b48a60",
    water: "#398bc4",
    stone: "#929a9a",
};

async function loadConfigIntoControls() {
    const response = await fetch("/api/config");

    if (!response.ok) {
        throw new Error("Could not load configuration.");
    }

    const config = await response.json();

    widthInput.value = config.world.width;
    heightInput.value = config.world.height;
    seedInput.value = config.world.seed ?? "";
    waterSmoothingInput.value =
        config.world.water_smoothing_passes ?? 10;

    waterInput.value = config.terrain_percentages.water;
    grassInput.value = config.terrain_percentages.grass;
    stoneInput.value = config.terrain_percentages.stone;

    updateDirtPercentage();
}

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

function updateDirtPercentage() {
    const water = Number(waterInput.value);
    const grass = Number(grassInput.value);
    const stone = Number(stoneInput.value);

    dirtInput.value = 100 - water - grass - stone;
}

[waterInput, grassInput, stoneInput].forEach(input => {
    input.addEventListener("input", updateDirtPercentage);
});

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

async function generateNewWorld() {
    generateButton.disabled = true;
    randomWorldButton.disabled = true;
    worldStatus.textContent = "Generating world...";

    try {
        const width = Number(widthInput.value);
        const height = Number(heightInput.value);
        const smoothing = Number(waterSmoothingInput.value);
        const rawSeed = seedInput.value.trim();

        const water = Number(waterInput.value);
        const grass = Number(grassInput.value);
        const stone = Number(stoneInput.value);

        const integersValid = [
            [width, 10, 300],
            [height, 10, 300],
            [smoothing, 1, 30],
        ].every(([value, min, max]) =>
            Number.isInteger(value) && value >= min && value <= max
        );

        const percentagesValid = [water, grass, stone].every(
            value => Number.isFinite(value) &&
                     value >= 0 && value <= 100
        );

        const dirt = 100 - water - grass - stone;

        if (!integersValid) {
            throw new Error(
                "Width and height must be 10–300; smoothing must be 1–30."
            );
        }

        if (!percentagesValid || dirt < 0) {
            throw new Error(
                "Terrain percentages must be valid and total no more than 100%."
            );
        }

        let seed = null;

        if (rawSeed !== "") {
            seed = Number(rawSeed);

            if (!Number.isSafeInteger(seed)) {
                throw new Error("Seed must be a valid integer.");
            }
        }

        const response = await fetch("/api/world", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                width,
                height,
                seed,
                water_smoothing_passes: smoothing,
                terrain_percentages: {
                    water,
                    grass,
                    stone,
                    dirt,
                },
            }),
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(
                result.detail
                    ? JSON.stringify(result.detail)
                    : "Python could not generate the world."
            );
        }

        drawWorld(result);
        renderTerrainStats(result);

        worldSize.textContent = `${result.width} × ${result.height}`;
        worldStatus.textContent = "World generated";
        seedInput.value = result.seed;
    } catch (error) {
        worldStatus.textContent = error.message;
        console.error(error);
    } finally {
        generateButton.disabled = false;
        randomWorldButton.disabled = false;
    }
}

generateButton.addEventListener("click", generateNewWorld);
randomWorldButton.addEventListener("click", () => {
    seedInput.value = "";
    generateNewWorld();
});

async function initializeFrontend() {
    try {
        await loadConfigIntoControls();
        await loadWorld();
    } catch (error) {
        worldStatus.textContent = "Could not initialize EcoSim";
        console.error(error);
    }
}

initializeFrontend();
