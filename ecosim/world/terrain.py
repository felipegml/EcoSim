from enum import Enum


class Terrain(str, Enum):
    GRASS = "grass"
    DIRT = "dirt"
    WATER = "water"
    STONE = "stone"
