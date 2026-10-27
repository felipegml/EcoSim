
const canvas = document.getElementById("world-map");
const context = canvas.getContext("2d");

const mapContainer = canvas.parentElement;
mapContainer.style.position = "relative";

const rainOverlay = document.createElement("div");
rainOverlay.className = "rain-overlay";
rainOverlay.hidden = true;

mapContainer.appendChild(rainOverlay);

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

const generationSummary = document.getElementById("generation-summary");

const simulationStatus = document.getElementById("simulation-status");
const simulationHour = document.getElementById("simulation-hour");
const simulationDay = document.getElementById("simulation-day");
const simulationYear = document.getElementById("simulation-year");
const simulationSeason = document.getElementById("simulation-season");
const simulationStartButton = document.getElementById("simulation-start");
const simulationPauseButton = document.getElementById("simulation-pause");
const simulationRestartButton = document.getElementById("simulation-restart");

const moistureButton = document.getElementById("toggle-moisture");
const grassHealthButton = document.getElementById("toggle-grass-health");

const simulationSpeed = document.getElementById("simulation-speed");

const dayNightIndicator = document.getElementById("day-night-indicator");
const weatherStatus = document.getElementById("weather-status");


const terrainColors = {
    grass: "#65a85c",
    dirt: "#b48a60",
    water: "#398bc4",
    stone: "#929a9a",
};

let moistureVisible = false;
let moistureData = null;
let currentWorld = null;
let grassHealthVisible = false;
let grassHealthData = null;

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

        currentWorld = world;
        drawWorld(world);
        renderTerrainStats(world);
        updateGenerationSummary(world);
        worldSize.textContent = `${world.width} × ${world.height}`;
        worldStatus.textContent = "World loaded";
    } catch (error) {
        worldStatus.textContent = "Could not load world";
        console.error(error);
    }
}


async function loadTerrainData() {
    const response = await fetch(
        "/api/terrain/moisture",
        { cache: "no-store" }
    );

    if (!response.ok) {
        throw new Error("Could not load terrain data.");
    }

    const data = await response.json();

    if (data.error) {
        throw new Error(data.error);
    }

    // Update the world with the latest terrain tiles.
    currentWorld = {
        ...currentWorld,
        width: data.width,
        height: data.height,
        tiles: data.tiles
    };

    // Update the terrain overlays.
    moistureData = data.moisture;
    grassHealthData = data.grass_health;
}

async function loadGrassHealth() {
    const response = await fetch("/api/terrain/moisture", {
        cache: "no-store"
    });

    if (!response.ok) {
        throw new Error("Could not load terrain data.");
    }

    const data = await response.json();

    if (data.error) {
        throw new Error(data.error);
    }

    grassHealthData = data.grass_health;
}


async function refreshMoistureView() {
    if (!currentWorld) return;

    try {
        await loadTerrainData();
        drawWorld(currentWorld);
    } catch (error) {
        console.error("Terrain refresh failed:", error);
    }
}


function drawWorld(world) {
    const tileSize = 20;

    canvas.width = world.width * tileSize;
    canvas.height = world.height * tileSize;

    world.tiles.forEach((row, y) => {
        row.forEach((terrain, x) => {
            const terrainColor = terrainColors[terrain] ?? "#ff00ff";

            let tileColor = terrainColor;

            if (
                grassHealthVisible &&
                terrain === "grass" &&
                grassHealthData?.[y]?.[x] !== undefined
            ) {
                const health = grassHealthData[y][x];

                // Healthy grass is bright green; weak grass is brownish.
                const red = Math.round(139 * (1 - health));
                const green = Math.round(168 * health + 90 * (1 - health));
                const blue = Math.round(70 * health + 45 * (1 - health));

                tileColor = `rgb(${red}, ${green}, ${blue})`;
            } else if (
                moistureVisible &&
                moistureData?.[y]?.[x] !== undefined
            ) {
                const moisture = moistureData[y][x];
                const blue = Math.round(120 + moisture * 135);

                tileColor = `rgb(30, 120, ${blue})`;
            }

            context.fillStyle = tileColor;
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

function updateGenerationSummary(world) {
    const totalTiles = world.width * world.height;
    const counts = {};

    for (const row of world.tiles) {
        for (const terrain of row) {
            counts[terrain] = (counts[terrain] || 0) + 1;
        }
    }

    const distribution = Object.entries(counts)
        .map(([terrain, count]) => {
            const percentage = (count / totalTiles) * 100;
            return `${terrain}: ${percentage.toFixed(1)}%`;
        })
        .join(" · ");

    generationSummary.textContent =
        `Seed: ${world.seed} | Tiles: ${totalTiles.toLocaleString()} | ${distribution}`;
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

        currentWorld = result;
        moistureData = null;

        drawWorld(result);
        renderTerrainStats(result);
        updateGenerationSummary(result);

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

async function refreshSimulationState() {
    try {
        const response = await fetch("/api/simulation");

        if (!response.ok) {
            throw new Error("Could not load simulation state.");
        }

        const state = await response.json();

        simulationHour.textContent =
            `${String(state.hour).padStart(2, "0")}:00`;

        simulationDay.textContent = state.day;
        simulationYear.textContent = state.year;

        if (dayNightIndicator) {
            dayNightIndicator.textContent = state.is_daytime
                ? "☀️ Day"
                : "🌙 Night";
        }

        simulationSeason.textContent =
            state.season.charAt(0).toUpperCase()
            + state.season.slice(1);

        simulationStatus.textContent =
            state.running ? "Running" : "Paused";

        if (state.is_raining) {
            weatherStatus.textContent =
                `🌧 Raining — ${state.intensity}`;
        } else {
            weatherStatus.textContent = "☀ Clear";
        }

        rainOverlay.hidden = !state.is_raining;

    } catch (error) {
        simulationStatus.textContent = "Connection error";
        console.error(error);
    }
}

async function controlSimulation(action) {
    try {
        const response = await fetch(
            `/api/simulation/${action}`,
            { method: "POST" }
        );

        if (!response.ok) {
            throw new Error(`Could not ${action} simulation.`);
        }

        await refreshSimulationState();
    } catch (error) {
        simulationStatus.textContent = "Connection error";
        console.error(error);
    }
}

generateButton.addEventListener("click", generateNewWorld);
randomWorldButton.addEventListener("click", () => {
    seedInput.value = "";
    generateNewWorld();
});

simulationStartButton.addEventListener("click", () => {
    controlSimulation("start");
});

simulationPauseButton.addEventListener("click", () => {
    controlSimulation("pause");
});

simulationRestartButton.addEventListener("click", () => {
    controlSimulation("restart");
});

moistureButton.addEventListener("click", async () => {
    try {
        if (!moistureVisible) {
            await loadTerrainData();
            moistureVisible = true;
            moistureButton.textContent = "🗺️";
            moistureButton.title = "Show terrain";
        } else {
            moistureVisible = false;
            moistureButton.textContent = "💧";
            moistureButton.title = "Show moisture";
        }

        if (currentWorld) {
            drawWorld(currentWorld);
        }
    } catch (error) {
        console.error(error);
        worldStatus.textContent = "Could not load moisture data";
    }
});

simulationSpeed.addEventListener("change", async () => {
    try {
        const response = await fetch("/api/simulation/speed", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                ticks_per_second: Number(simulationSpeed.value),
            }),
        });

        if (!response.ok) {
            throw new Error("Could not update simulation speed.");
        }

        //const data = await response.json();
        //console.log("Speed API response:", data);

    } catch (error) {
        console.error(error);
        worldStatus.textContent = "Could not update simulation speed";
    }
});

grassHealthButton.addEventListener("click", async () => {
    try {
        if (!grassHealthVisible) {
            await loadGrassHealth();
            grassHealthVisible = true;

            // Turn off the other overlay.
            moistureVisible = false;
            moistureButton.textContent = "💧";
            moistureButton.title = "Show moisture";

            grassHealthButton.textContent = "🌿";
            grassHealthButton.title = "Show terrain";
        } else {
            grassHealthVisible = false;
            grassHealthButton.textContent = "🌱";
            grassHealthButton.title = "Show grass health";
        }

        if (currentWorld) {
            drawWorld(currentWorld);
        }
    } catch (error) {
        console.error(error);
        worldStatus.textContent = "Could not load grass health";
    }
});

async function initializeFrontend() {
    try {
        await loadConfigIntoControls();
        await loadWorld();

        await refreshSimulationState();

        setInterval(refreshSimulationState, 1000);
        setInterval(refreshMoistureView, 1000);
    } catch (error) {
        worldStatus.textContent = "Could not initialize EcoSim";
        console.error(error);
    }
}

initializeFrontend();
