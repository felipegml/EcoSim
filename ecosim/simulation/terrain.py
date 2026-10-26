
from dataclasses import dataclass, field


@dataclass
class TerrainSimulation:
    tiles: list[list[str]]
    moisture: list[list[float]] = field(init=False)

    def __post_init__(self) -> None:
        moisture_by_terrain = {
            "water": 1.0,
            "grass": 0.5,
            "dirt": 0.25,
            "stone": 0.0,
        }

        self.moisture = [
            [
                moisture_by_terrain.get(terrain, 0.0)
                for terrain in row
            ]
            for row in self.tiles
        ]

    def get_state(self) -> dict:
        return {
            "width": len(self.tiles[0]) if self.tiles else 0,
            "height": len(self.tiles),
            "moisture": self.moisture,
        }
    
    
    def tick(self) -> None:
        height = len(self.tiles)
        width = len(self.tiles[0]) if height else 0

        updated = [row[:] for row in self.moisture]

        for y in range(height):
            for x in range(width):
                terrain = self.tiles[y][x]

                # Water is a permanent moisture source.
                if terrain == "water":
                    updated[y][x] = 1.0
                    continue

                # Stone does not participate in moisture spreading.
                if terrain == "stone":
                    updated[y][x] = 0.0
                    continue

                neighbors = []

                for nx, ny in (
                    (x - 1, y),
                    (x + 1, y),
                    (x, y - 1),
                    (x, y + 1),
                ):
                    if 0 <= nx < width and 0 <= ny < height:
                        neighbors.append(self.moisture[ny][nx])

                if neighbors:
                    average = sum(neighbors) / len(neighbors)

                    # Gradually move toward neighboring moisture levels.
                    current = self.moisture[y][x]
                    current += (average - current) * 0.05

                    # A small amount of moisture evaporates each tick.
                    current -= 0.001

                    updated[y][x] = max(0.0, min(1.0, current))

        self.moisture = updated
