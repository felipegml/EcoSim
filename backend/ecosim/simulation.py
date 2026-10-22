from dataclasses import dataclass, field

from backend.ecosim.animals import Animal, Species
from backend.ecosim.config import WorldConfig
from backend.ecosim.world import Terrain, World, generate_world


ENERGY_LOSS_PER_TICK = 1.0
ENERGY_FROM_GRASS = 10.0

MIN_EATING_TICKS = 1
MAX_EATING_TICKS = 5


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
                    Animal(
                        id=animal_id,
                        species=species,
                        x=x,
                        y=y,
                    )
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

    def _move_herbivores(self) -> None:
        occupied = {(animal.x, animal.y) for animal in self.animals}

        herbivores = [
            animal for animal in self.animals
            if animal.species == Species.HERBIVORE
        ]
        self.world.rng.shuffle(herbivores)

        for animal in herbivores:
            cell = self.world.cells[animal.y][animal.x]

            # An animal already eating stays in place until its timer ends.
            if animal.eating_ticks_remaining > 0:
                animal.energy -= ENERGY_LOSS_PER_TICK
                animal.eating_ticks_remaining -= 1

                if animal.eating_ticks_remaining == 0:
                    if cell.terrain == Terrain.GRASS:
                        cell.terrain = Terrain.DIRT
                        animal.energy += ENERGY_FROM_GRASS

                continue

            # If the animal starts this tick on grass, begin eating.
            if cell.terrain == Terrain.GRASS:
                animal.eating_ticks_remaining = self.world.rng.randint(
                    MIN_EATING_TICKS,
                    MAX_EATING_TICKS,
                )
                animal.energy -= ENERGY_LOSS_PER_TICK
                continue

            # Otherwise, look for a valid adjacent tile.
            occupied.remove((animal.x, animal.y))

            candidates = [
                (x, y)
                for x, y in self._neighbors(animal.x, animal.y)
                if (x, y) not in occupied
                and self.world.cells[y][x].terrain != Terrain.WATER
            ]

            if candidates:
                grass_candidates = [
                    (x, y)
                    for x, y in candidates
                    if self.world.cells[y][x].terrain == Terrain.GRASS
                ]

                # Prefer adjacent grass, then begin eating on arrival.
                choices = grass_candidates or candidates
                animal.x, animal.y = self.world.rng.choice(choices)

            occupied.add((animal.x, animal.y))
            animal.energy -= ENERGY_LOSS_PER_TICK

            cell = self.world.cells[animal.y][animal.x]
            if cell.terrain == Terrain.GRASS:
                animal.eating_ticks_remaining = self.world.rng.randint(
                    MIN_EATING_TICKS,
                    MAX_EATING_TICKS,
                )

    def _remove_starved_animals(self) -> None:
        self.animals = [
            animal for animal in self.animals
            if animal.energy > 0
        ]

    def step(self) -> None:
        # Regrow grass on dirt tiles.
        for row in self.world.cells:
            for cell in row:
                if (
                    cell.terrain == Terrain.DIRT
                    and self.world.rng.random()
                    < self.config.grass_regrowth_chance
                ):
                    cell.terrain = Terrain.GRASS

        self._move_herbivores()
        self._remove_starved_animals()
        self.tick += 1