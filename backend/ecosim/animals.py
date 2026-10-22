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