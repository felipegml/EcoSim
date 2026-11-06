# EcoSimPy Roadmap

This roadmap lists possible next steps for EcoSimPy, in the order that
reduces rework: make the current simulation reliable, add animal life,
then make the API straightforward to consume from game engines. Items
are proposals and can be reprioritized as the project develops.

## 1. Fix and stabilize the simulation

- [ ] **Audit the current simulation behavior**
  - Review the clock, climate, weather, terrain, and engine tick order.
  - Compare actual behavior with `config.json` and the documented rules.
  - Record reproducible issues with the input configuration, world seed,
    action sequence, and observed versus expected state.
  - Prioritize incorrect state transitions, crashes, invalid values, and
    behavior that prevents a world from running reliably.
- [ ] **Make simulation runs reproducible**
  - Ensure seeded world generation and simulation randomness can be
    reproduced from the same seed and inputs.
  - Define how random-number generators are initialized and shared by
    simulation systems.
  - Add tests proving that repeated seeded runs produce the same state
    sequence, while unseeded runs can start with a newly generated seed.
- [ ] **Harden state and configuration validation**
  - Validate world dimensions, rectangular terrain grids, terrain types,
    and numeric configuration ranges at their entry points.
  - Check that moisture, grass health, temperatures, and tick rates stay
    within their documented ranges.
  - Return clear errors for invalid API requests rather than allowing
    malformed state into the simulation.
- [ ] **Expand simulation tests**
  - Add focused unit tests for clock boundaries, season changes,
    weather transitions, moisture updates, grass health, death, and
    spreading.
  - Add engine-level tests for start, pause, restart, world loading, and
    the order of updates in a tick.
  - Use small fixed worlds and controlled seeds/settings so failures are
    deterministic and easy to diagnose.
- [ ] **Verify and document expected behavior**
  - Run the full test suite after fixes.
  - Update the README when implemented behavior differs from its
    description.
  - Define a stable simulation-state shape that future animal and game
    engine features can extend without breaking existing consumers.

**Completion check:** The existing simulation has documented behavior,
reproducible regression tests for fixed seeds, and passes its test suite.

## 2. Add animals to the simulation

- [ ] **Define animal requirements and data**
  - Choose an initial scope, such as a small set of herbivore species,
    before adding predators or complex food webs.
  - Define the data needed by an animal: stable ID, species, position,
    health, energy or hunger, age, and lifecycle state.
  - Decide which properties are per-animal and which are species-level
    configuration, such as movement rate, diet, lifespan, and
    reproduction requirements.
- [ ] **Create animal models and population management**
  - Add typed animal/species models and validation for their state.
  - Add an animal system responsible for creating, locating, updating,
    and removing animals.
  - Specify how animals occupy the tile world, including whether several
    animals may share a tile and how map edges are handled.
  - Keep stable animal IDs so API clients can track an animal between
    state updates.
- [ ] **Connect animals to simulation ticks**
  - Add animal updates to the engine's tick sequence with an explicit,
    documented order relative to climate and terrain.
  - Make movement and behavior use the current terrain, weather, and
    simulation time.
  - Ensure pausing, restarting, loading a new world, and setting a seed
    have clearly defined effects on animal state.
- [ ] **Implement a minimal herbivore lifecycle**
  - Add movement across valid neighboring tiles.
  - Add searching for suitable grass, feeding, and energy/hunger changes.
  - Connect grass consumption to the terrain system so feeding has a
    visible, tested effect on the world.
  - Add health loss, death, and population removal rules.
  - Add reproduction only after movement and feeding behavior are stable;
    define eligibility, offspring creation, and population limits.
- [ ] **Make animal behavior configurable and testable**
  - Put species and behavior parameters in validated configuration.
  - Use the simulation's seeded randomness for stochastic decisions.
  - Test movement constraints, food selection, feeding, energy changes,
    death, reproduction, and interactions with terrain using small
    deterministic worlds.
- [ ] **Expose and display animal state**
  - Include animal summaries and, where needed, per-animal details in
    simulation state.
  - Add browser visualization for animal locations and useful population
    statistics.
  - Confirm frequent state updates remain practical as populations grow.

**Completion check:** At least one configured herbivore species can
move, consume grass, and change state over time, with deterministic
tests and visible/API-accessible results.

## 3. Create an API for Unity, Godot, and Unreal

- [ ] **Define the integration contract**
  - Document the supported HTTP/JSON API, request and response schemas,
    coordinate system, terrain and animal representations, and error
    format.
  - Define which system owns simulation time and state; initially, keep
    EcoSimPy as the simulation authority and game engines as clients.
  - Establish API versioning and compatibility rules before external
    integrations depend on the current routes.
- [ ] **Complete game-client workflows**
  - Ensure clients can inspect configuration and simulation state,
    create or load a world, start and pause the simulation, advance a
    tick, restart, and change speed.
  - Add clearly defined endpoints for animal state and any supported
    client commands.
  - Make responses sufficient for a client to render a full initial
    state and then apply later updates without guessing missing fields.
- [ ] **Choose and document update delivery**
  - Start with the existing request/response model for commands and
    snapshots.
  - Measure polling needs for live game clients; if polling is too
    costly or delayed, add a push option such as WebSockets or
    server-sent events.
  - Specify update frequency, ordering, reconnect behavior, and whether
    clients receive full snapshots or incremental changes.
- [ ] **Add integration safety and operational behavior**
  - Define behavior for concurrent clients and conflicting simulation
    commands.
  - Add request validation, useful error responses, and health/status
    checks suitable for a local development process.
  - Document local-network exposure and add authentication or other
    access controls before supporting untrusted or public clients.
- [ ] **Provide engine-specific examples**
  - Create a small Unity example that connects, loads state, and renders
    the world.
  - Create a small Godot example with the same basic connection and
    rendering workflow.
  - Create a small Unreal example demonstrating connection, JSON
    parsing, and state display.
  - Keep examples aligned with the same API contract and document
    required engine versions and setup steps.
- [ ] **Test compatibility end to end**
  - Add API contract tests for valid requests, malformed input, and
    error responses.
  - Add automated or repeatable manual smoke tests for each engine
    example.
  - Verify that an engine client can connect, load a world, observe
    updates, and handle pause/restart or a dropped connection.

**Completion check:** Each target engine has a documented example that
connects to a versioned API, loads simulation state, and handles updates
and errors consistently.

## Later possibilities

- [ ] Add additional species and predator/prey interactions after the
  first herbivore lifecycle is stable.
- [ ] Add persistence and save/load support for world and simulation
  state.
- [ ] Profile larger worlds and populations, then optimize based on
  measured bottlenecks.
