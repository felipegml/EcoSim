from dataclasses import dataclass
from enum import Enum


class Species(Enum):
    HERBIVORE = "herbivore"
    PREDATOR = "predator"


@dataclass
class Animal:
    id: int
    species: Species
    x: int
    y: int
    energy: float = 100.0
    eating_ticks_remaining: int = 0

    # Needs are measured from 0 to 100.
    hunger: float = 0.0
    thirst: float = 0.0
    stamina: float = 100.0

    # True while the animal is drinking at the water's edge.
    drinking: bool = False