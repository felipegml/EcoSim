# EcoSimPy

EcoSimPy is a configurable, tile-based ecosystem simulation. The world
is a grid of terrain tiles, and simulation time advances one hour per
tick. Weather, seasons, and soil moisture influence grass health and
terrain changes.

This document explains the intended logic and current design. The
project is still evolving, so check the source code and `config.json`
for the exact current settings and API routes.

## Intended audience

EcoSimPy is a personal project for experimenting with ecosystem
simulation and testing approaches to integrating it with a game engine
in the future.

## Built with

-   **Python** for the simulation and API.
-   **FastAPI** and **Uvicorn** to serve the API and browser interface.
-   **HTML, CSS, and JavaScript** for the frontend.

## Goals

-   Generate a world from configurable settings and a seed.
-   Track simulation time, seasons, and day/night.
-   Simulate rain, evaporation, and soil-moisture diffusion.
-   Let grass weaken, recover, die into dirt, and spread into suitable
    dirt.
-   Display the world and environmental overlays in a browser.
-   Keep behavior testable as new features are added.

Grass is represented by a tile and a health value, not by an individual
Python object for every plant. Grass is intended to be food for future
herbivores. Pollination is not part of the current design.

## Project structure

``` text
EcoSim/
├── config.json
├── requirements.txt
├── README.md
├── ecosim/
│   ├── main.py
│   ├── config/       # Configuration loading and validation
│   ├── world/        # World generation
│   ├── simulation/   # Clock, engine, terrain, weather
│   ├── api/          # HTTP API
│   └── storage/      # Future/persistent storage work
├── frontend/
│   ├── index.html
│   ├── css/style.css
│   ├── js/main.js
│   └── world.json
└── tests/            # Automated tests
```

### Responsibilities

  -----------------------------------------------------------------------
  Component                           Responsibility
  ----------------------------------- -----------------------------------
  `config.json`                       World-generation, season, weather,
                                      and terrain settings.

  `ecosim/config/loader.py`           Loads configuration relative to the
                                      project root.

  `ecosim/config/validator.py`        Validates configuration values.

  `ecosim/world/generator.py`         Generates the initial grid, using
                                      settings and a seed.

  `ecosim/simulation/clock.py`        Tracks hour, day, year, season, and
                                      day/night.

  `ecosim/simulation/weather.py`      Handles weather events, including
                                      rain and its amount/intensity.

  `ecosim/simulation/terrain.py`      Updates moisture and grass health,
                                      and changes grass/dirt tiles.

  `ecosim/simulation/engine.py`       Coordinates the clock, weather, and
                                      terrain each tick.

  `ecosim/api/app.py`                 Exposes world state and simulation
                                      controls to the frontend.

  `frontend/`                         Renders the map, controls,
                                      statistics, and overlays.

  `tests/`                            Checks configuration, generation,
                                      clock, weather, and terrain logic.
  -----------------------------------------------------------------------

## Terrain grid

The world uses rows of tile values:

-   **Grass:** vegetation with a health value.
-   **Dirt:** bare ground that can become grass under suitable
    conditions.
-   **Water:** maintains its configured moisture.
-   **Stone:** maintains its configured moisture and does not support
    grass in the current logic.

The `tiles`, `moisture`, and `grass_health` grids use the same `[y][x]`
coordinates. For example, `tiles[y][x]`, `moisture[y][x]`, and
`grass_health[y][x]` describe the terrain, moisture, and grass health at
one location.

## Configuration and world generation

Settings live in `config.json` so they can be tuned without changing
simulation code. The configuration loader finds the file relative to the
project root.

World generation uses settings such as width, height, seed, water
smoothing, and terrain percentages. A fixed seed with the same settings
should produce a repeatable world. The frontend can request a new world
through the API, then redraw the map and refresh terrain statistics.

Use the actual `config.json` as the source of truth for current values;
examples in documentation should not replace the live configuration.

## Clock, seasons, and day/night

One simulation tick represents one hour.

-   Hours run from `0` to `23`.
-   After hour `23`, the hour resets to `0` and the day increases.
-   When the day passes the total configured duration of all seasons,
    the day resets and the year increases.
-   The current season is derived from the day of the year and
    configured season lengths.
-   Per-season sunrise and sunset values determine whether a given hour
    is daytime.

The clock exposes hour, day, year, season, and `is_daytime` for the API
and frontend.

## Weather and rain

The weather simulation tracks whether it is raining and properties such
as intensity and rain amount. The engine passes the current rain amount
to terrain during each tick. Rain adds moisture to grass and dirt; water
and stone retain their configured moisture values.

Weather settings may vary by season. Weather and terrain are tested
separately so failures can be narrowed to the responsible system.

## Soil moisture

Moisture is intended to stay between `0.0` and `1.0`:

-   `0.0` means very dry; `1.0` means fully moist.
-   Grass and dirt begin with configured moisture values.
-   Water and stone are reset to their configured values each tick.
-   Rain adds moisture to grass and dirt.
-   Evaporation removes moisture and can use seasonal rates.
-   Diffusion moves a tile's moisture a small fraction toward the
    average of its orthogonal neighbors (up, down, left, right).
-   Values are clamped to the valid range.

Moisture updates are calculated into a separate grid, based on the
previous grid. This prevents one tile's newly calculated value from
influencing another tile during the same diffusion pass.

## Grass health and lifecycle

Grass health ranges from `0.0` to `1.0`. A value of `1.0` represents
healthy grass; lower values represent weakened grass; `0.0` represents
dead grass.

### Health update

Each tick updates existing grass health using the newly calculated
moisture:

1.  In winter, grass loses the configured winter health amount.
2.  Outside winter, grass below the minimum moisture loses the
    configured health amount.
3.  Otherwise, grass recovers by the configured recovery amount.
4.  Health is clamped to `0.0`--`1.0`.

Winter damage takes priority over moisture-based recovery in the current
logic. Outside winter, grass can recover when its moisture is
sufficient. Non-grass tiles have grass health set to zero.

### Grass death

After health is updated, grass at or below the configured death
threshold becomes dirt, and its health is reset to zero.

Test setup matters: a grass tile whose moisture is already above the
minimum will recover instead of losing health. A death test should
therefore start with sufficiently low moisture so it actually exercises
the health-loss path.

### Grass spreading

Healthy grass can spread to an orthogonally adjacent dirt tile when:

-   The dirt has at least the configured spreading-moisture level.
-   At least one of its four neighbors is grass.
-   That neighboring grass meets the configured source-health threshold.
-   A random roll succeeds according to the spread chance.

New grass currently starts with partial health (for example, `0.5`) and
must recover before it can become a healthy spreading source. The
simulation works with copies of the tile and health grids so newly
created grass cannot spread again in the same tick. A configured random
seed can make spreading tests reproducible.

The exact names and defaults for these settings should be verified
against `terrain.py` and `config.json`.

## What happens in one tick?

At a high level:

1.  The engine advances the simulation clock and updates weather.
2.  Terrain calculates moisture from diffusion, evaporation, and rain.
3.  Existing grass health is updated.
4.  Dead grass changes into dirt.
5.  Eligible dirt may change into grass through spreading.
6.  The engine exposes the updated state through the API.
7.  The frontend refreshes displayed state and redraws any active
    overlay.

The order matters: health uses the updated moisture for the tick, and
spreading uses the updated moisture and health values.

## API and frontend

The API connects Python simulation state to the browser. The frontend
uses `fetch()` to load configuration, world data, simulation state, and
terrain data. It also sends requests to generate a world and control the
simulation (start, pause, restart, and speed).

The world is drawn on an HTML canvas. Base colors represent grass, dirt,
water, and stone. The frontend can display overlays:

-   **Moisture:** colors tiles according to moisture.
-   **Grass health:** colors grass from greener (healthier) to browner
    (weaker).

Overlays only visualize simulation data; they do not change the
simulation. For grass-to-dirt and dirt-to-grass changes to be visible,
the frontend must receive the latest terrain grid and redraw the canvas.

## Install, run, and test

Install dependencies from the project root:

``` bash
pip install -r requirements.txt
```

From the project root, start the API and frontend with:

``` bash
python -m uvicorn ecosim.api.app:app --reload
```

Then open `http://127.0.0.1:8000` in your browser.

Run all tests:

``` bash
python -m pytest -v
```

Run terrain tests while working on terrain logic:

``` bash
python -m pytest tests/test_terrain.py -v
```

Prefer tests with controlled initial conditions. For example, a
grass-death test should start with low moisture, and a spreading test
can use a spread chance of `1.0` so its result is deterministic apart
from other conditions.

## Current limitations and likely next steps

-   Grass uses tile state and a health grid, not individual plant
    entities.
-   Herbivore populations and feeding mechanics are not yet part of the
    current design.
-   Pollination is not implemented.
-   Growth thresholds and rates will need balancing through testing and
    observation.
-   Spreading is probabilistic under normal settings; a particular tile
    is not guaranteed to spread on every tick.
-   The frontend overlays are visual only.
-   Exact API endpoints and configuration values can evolve; verify them
    in the current source.

A useful next step is to verify that the frontend refreshes the latest
tile grid as well as moisture and health, then add lifecycle edge-case
tests and tune the rates so grass does not disappear too quickly or
spread across the whole map too quickly.

## Design principle

EcoSim separates responsibilities so features can be added without
putting all behavior into one place:

-   **Configuration** supplies tunable values.
-   **World generation** creates the initial map.
-   **Clock and weather** describe environmental conditions.
-   **Terrain simulation** updates moisture, grass health, and terrain
    types.
-   **Simulation engine** coordinates each tick.
-   **API** exposes state and controls.
-   **Frontend** visualizes state and sends user actions.
-   **Tests** protect behavior as the simulation evolves.

This structure leaves room for future systems such as herbivores,
population dynamics, and persistence without mixing them into the core
terrain update.
