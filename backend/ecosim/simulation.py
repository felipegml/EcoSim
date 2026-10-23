from dataclasses import dataclass, field

from backend.ecosim.animals import Animal, Species
from backend.ecosim.config import WorldConfig
from backend.ecosim.world import Terrain, World, generate_world


# Energy costs per tick, selected randomly within each range.
MOVE_ENERGY_COST = (1.0, 2.0)
EAT_ENERGY_COST = (0.1, 0.5)
DRINK_ENERGY_COST = (0.1, 0.4)
FLEE_ENERGY_COST = (2.0, 4.0)

# Stamina costs per tick.
MOVE_STAMINA_COST = (1.0, 2.0)
EAT_STAMINA_COST = (0.25, 0.75)
DRINK_STAMINA_COST = (0.25, 0.75)
FLEE_STAMINA_COST = (3.0, 5.0)
REST_STAMINA_RECOVERY = (2.0, 5.0)

# Random changes to needs per tick.
HUNGER_INCREASE = (1.0, 3.0)
THIRST_INCREASE = (1.0, 3.0)
HUNGER_RECOVERY = (20.0, 40.0)
THIRST_RECOVERY = (5.0, 15.0)

ENERGY_FROM_GRASS = 10.0
MIN_EATING_TICKS = 1
MAX_EATING_TICKS = 5

HUNGRY_THRESHOLD = 70.0
CRITICAL_HUNGER = 80.0
THIRSTY_THRESHOLD = 60.0
STOP_DRINKING_AT = 30.0
LOW_STAMINA_THRESHOLD = 20.0
PREDATOR_DANGER_RADIUS = 3


@dataclass
class Simulation:
    config: WorldConfig
    world: World
    animals: list[Animal] = field(default_factory=list)
    tick: int = 0

    @classmethod
    def create(cls, config: WorldConfig | None = None) -> "Simulation":
        if config is None:
            config = WorldConfig()

        world = generate_world(config)

        land_positions = [
            (x, y)
            for y in range(world.height)
            for x in range(world.width)
            if world.cells[y][x].terrain != Terrain.WATER
        ]

        total_animals = config.herbivore_count + config.predator_count
        positions = world.rng.sample(land_positions, total_animals)
        animals: list[Animal] = []
        animal_id = 1
        position_index = 0

        for species, count in (
            (Species.HERBIVORE, config.herbivore_count),
            (Species.PREDATOR, config.predator_count),
        ):
            for _ in range(count):
                x, y = positions[position_index]
                animals.append(
                    Animal(id=animal_id, species=species, x=x, y=y)
                )
                animal_id += 1
                position_index += 1

        return cls(config=config, world=world, animals=animals)

    @property
    def herbivore_count(self) -> int:
        return sum(
            animal.species == Species.HERBIVORE
            for animal in self.animals
        )

    @property
    def predator_count(self) -> int:
        return sum(
            animal.species == Species.PREDATOR
            for animal in self.animals
        )

    def _neighbors(self, x: int, y: int) -> list[tuple[int, int]]:
        positions = []

        if x > 0:
            positions.append((x - 1, y))
        if x < self.world.width - 1:
            positions.append((x + 1, y))
        if y > 0:
            positions.append((x, y - 1))
        if y < self.world.height - 1:
            positions.append((x, y + 1))

        return positions

    def _water_edges(self) -> set[tuple[int, int]]:
        """Return land tiles adjacent to permanent water."""
        edges = set()

        for y in range(self.world.height):
            for x in range(self.world.width):
                if self.world.cells[y][x].terrain == Terrain.WATER:
                    for nx, ny in self._neighbors(x, y):
                        if self.world.cells[ny][nx].terrain != Terrain.WATER:
                            edges.add((nx, ny))

        return edges

    def _nearest_predator(
        self, animal: Animal
    ) -> Animal | None:
        predators = [
            other
            for other in self.animals
            if other.species == Species.PREDATOR
            and abs(other.x - animal.x) + abs(other.y - animal.y)
            <= PREDATOR_DANGER_RADIUS
        ]

        if not predators:
            return None

        return min(
            predators,
            key=lambda other: (
                abs(other.x - animal.x) + abs(other.y - animal.y)
            ),
        )

    def _update_needs(self) -> None:
        """Needs change by random amounts every simulation tick."""
        rng = self.world.rng

        for animal in self.animals:
            animal.hunger = min(
                100.0,
                animal.hunger + rng.uniform(*HUNGER_INCREASE),
            )
            animal.thirst = min(
                100.0,
                animal.thirst + rng.uniform(*THIRST_INCREASE),
            )

    def _move_herbivores(self) -> None:
        rng = self.world.rng
        occupied = {(animal.x, animal.y) for animal in self.animals}
        water_edges = self._water_edges()

        herbivores = [
            animal
            for animal in self.animals
            if animal.species == Species.HERBIVORE
        ]
        rng.shuffle(herbivores)

        for animal in herbivores:
            position = (animal.x, animal.y)
            cell = self.world.cells[animal.y][animal.x]
            predator = self._nearest_predator(animal)

            # Nearby predators interrupt eating or drinking.
            if predator is not None:
                animal.eating_ticks_remaining = 0
                animal.drinking = False

                candidates = [
                    pos for pos in self._neighbors(animal.x, animal.y)
                    if pos not in occupied
                    and self.world.cells[pos[1]][pos[0]].terrain
                    != Terrain.WATER
                ]

                if candidates:
                    occupied.remove(position)

                    animal.x, animal.y = max(
                        candidates,
                        key=lambda pos: (
                            abs(pos[0] - predator.x)
                            + abs(pos[1] - predator.y),
                            rng.random(),
                        ),
                    )
                    occupied.add((animal.x, animal.y))

                animal.energy -= rng.uniform(*FLEE_ENERGY_COST)
                animal.stamina = max(
                    0.0,
                    animal.stamina - rng.uniform(*FLEE_STAMINA_COST),
                )
                continue

            # A drinking animal stays at the water's edge until
            # sufficiently hydrated, unless hunger makes it leave.
            if (
                animal.drinking
                and animal.thirst > STOP_DRINKING_AT
                and animal.hunger < HUNGRY_THRESHOLD
            ):
                animal.energy -= rng.uniform(*DRINK_ENERGY_COST)
                animal.stamina = max(
                    0.0,
                    animal.stamina - rng.uniform(*DRINK_STAMINA_COST),
                )
                animal.thirst = max(
                    0.0,
                    animal.thirst - rng.uniform(*THIRST_RECOVERY),
                )
                continue

            animal.drinking = False

            # A thirsty animal prioritizes reaching the water's edge,
            # unless it is hungry enough to prioritize food.
            if (
                animal.thirst >= THIRSTY_THRESHOLD
                and animal.hunger < HUNGRY_THRESHOLD
                and water_edges
            ):
                if position in water_edges:
                    animal.drinking = True
                    animal.energy -= rng.uniform(*DRINK_ENERGY_COST)
                    animal.stamina = max(
                        0.0,
                        animal.stamina - rng.uniform(*DRINK_STAMINA_COST),
                    )
                    animal.thirst = max(
                        0.0,
                        animal.thirst - rng.uniform(*THIRST_RECOVERY),
                    )
                    continue

                candidates = [
                    pos for pos in self._neighbors(animal.x, animal.y)
                    if pos not in occupied
                    and self.world.cells[pos[1]][pos[0]].terrain
                    != Terrain.WATER
                ]

                if candidates:
                    target = min(
                        water_edges,
                        key=lambda pos: (
                            abs(pos[0] - animal.x)
                            + abs(pos[1] - animal.y)
                        ),
                    )
                    occupied.remove(position)
                    animal.x, animal.y = min(
                        candidates,
                        key=lambda pos: (
                            abs(pos[0] - target[0])
                            + abs(pos[1] - target[1]),
                            rng.random(),
                        ),
                    )
                    occupied.add((animal.x, animal.y))

                animal.energy -= rng.uniform(*MOVE_ENERGY_COST)
                animal.stamina = max(
                    0.0,
                    animal.stamina - rng.uniform(*MOVE_STAMINA_COST),
                )
                continue

            # Finish a meal already in progress.
            if animal.eating_ticks_remaining > 0:
                animal.energy -= rng.uniform(*EAT_ENERGY_COST)
                animal.stamina = max(
                    0.0,
                    animal.stamina - rng.uniform(*EAT_STAMINA_COST),
                )
                animal.eating_ticks_remaining -= 1

                if animal.eating_ticks_remaining == 0:
                    cell = self.world.cells[animal.y][animal.x]
                    if cell.terrain == Terrain.GRASS:
                        cell.terrain = Terrain.DIRT
                        animal.energy += ENERGY_FROM_GRASS
                        animal.hunger = max(
                            0.0,
                            animal.hunger - rng.uniform(*HUNGER_RECOVERY),
                        )

                continue

            # Eat if standing on grass and not urgently seeking water.
            if (
                cell.terrain == Terrain.GRASS
                and animal.hunger >= HUNGRY_THRESHOLD
            ):
                animal.eating_ticks_remaining = rng.randint(
                    MIN_EATING_TICKS,
                    MAX_EATING_TICKS,
                )
                animal.energy -= rng.uniform(*EAT_ENERGY_COST)
                animal.stamina = max(
                    0.0,
                    animal.stamina - rng.uniform(*EAT_STAMINA_COST),
                )
                continue

            # Rest if stamina is low and no urgent need takes priority.
            if animal.stamina <= LOW_STAMINA_THRESHOLD:
                animal.stamina = min(
                    100.0,
                    animal.stamina + rng.uniform(*REST_STAMINA_RECOVERY),
                )
                continue

            # Otherwise move. Prefer grass if hungry.
            candidates = [
                pos for pos in self._neighbors(animal.x, animal.y)
                if pos not in occupied
                and self.world.cells[pos[1]][pos[0]].terrain
                != Terrain.WATER
            ]

            if candidates:
                grass_candidates = [
                    pos for pos in candidates
                    if self.world.cells[pos[1]][pos[0]].terrain
                    == Terrain.GRASS
                ]

                choices = (
                    grass_candidates
                    if animal.hunger >= HUNGRY_THRESHOLD
                    and grass_candidates
                    else candidates
                )

                occupied.remove(position)
                animal.x, animal.y = rng.choice(choices)
                occupied.add((animal.x, animal.y))

            animal.energy -= rng.uniform(*MOVE_ENERGY_COST)
            animal.stamina = max(
                0.0,
                animal.stamina - rng.uniform(*MOVE_STAMINA_COST),
            )

            # Arriving on grass starts a meal for a future tick.
            cell = self.world.cells[animal.y][animal.x]
            if (
                cell.terrain == Terrain.GRASS
                and animal.hunger >= HUNGRY_THRESHOLD
            ):
                animal.eating_ticks_remaining = rng.randint(
                    MIN_EATING_TICKS,
                    MAX_EATING_TICKS,
                )

    def _remove_starved_animals(self) -> None:
        self.animals = [
            animal for animal in self.animals
            if animal.energy > 0
        ]

    def step(self) -> None:
        # Regrow grass on dirt tiles. Water never changes.
        for row in self.world.cells:
            for cell in row:
                if (
                    cell.terrain == Terrain.DIRT
                    and self.world.rng.random()
                    < self.config.grass_regrowth_chance
                ):
                    cell.terrain = Terrain.GRASS

        self._update_needs()
        self._move_herbivores()

        # Predators do not yet have movement, hunting, or drinking behavior.
        # They recover stamina while stationary.
        for animal in self.animals:
            if animal.species == Species.PREDATOR:
                animal.stamina = min(
                    100.0,
                    animal.stamina
                    + self.world.rng.uniform(*REST_STAMINA_RECOVERY),
                )

        self._remove_starved_animals()
        self.tick += 1