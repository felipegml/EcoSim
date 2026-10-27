
from dataclasses import dataclass, field

HOURS_PER_DAY = 24

@dataclass
class SimulationClock:
    hour: int = 0
    day: int = 1
    year: int = 1
    seasons: dict = field(default_factory=lambda: {
        "spring": 91,
        "summer": 92,
        "autumn": 91,
        "winter": 91,
    })
    day_night: dict = field(default_factory=dict)

    def tick(self) -> None:
        """Advance the simulation by one hour."""
        self.hour += 1

        if self.hour >= HOURS_PER_DAY:
            self.hour = 0
            self.day += 1

        if self.day > sum(self.seasons.values()):
            self.day = 1
            self.year += 1

    @property
    def season(self) -> str:
        day_of_year = self.day

        for season_name, duration in self.seasons.items():
            if day_of_year <= duration:
                return season_name
            day_of_year -= duration

        raise RuntimeError("Invalid simulation day.")

    @property
    def is_daytime(self) -> bool:
        settings = self.day_night.get(self.season, {})
        sunrise = settings.get("sunrise", 6)
        sunset = settings.get("sunset", 18)

        return sunrise <= self.hour < sunset

    def to_dict(self) -> dict:
        return {
            "hour": self.hour,
            "day": self.day,
            "year": self.year,
            "season": self.season,
            "is_daytime": self.is_daytime,
        }
