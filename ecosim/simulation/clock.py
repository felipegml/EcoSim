
from dataclasses import dataclass


HOURS_PER_DAY = 24
DAYS_PER_YEAR = 365

SEASONS = (
    ("spring", 91),
    ("summer", 92),
    ("autumn", 91),
    ("winter", 91),
)


@dataclass
class SimulationClock:
    hour: int = 0
    day: int = 1
    year: int = 1

    def tick(self) -> None:
        """Advance the simulation by one hour."""
        self.hour += 1

        if self.hour >= HOURS_PER_DAY:
            self.hour = 0
            self.day += 1

        if self.day > DAYS_PER_YEAR:
            self.day = 1
            self.year += 1

    @property
    def season(self) -> str:
        day_of_year = self.day

        for season_name, duration in SEASONS:
            if day_of_year <= duration:
                return season_name
            day_of_year -= duration

        raise RuntimeError("Invalid simulation day.")

    @property
    def is_daytime(self) -> bool:
        return 6 <= self.hour < 18

    def to_dict(self) -> dict:
        return {
            "hour": self.hour,
            "day": self.day,
            "year": self.year,
            "season": self.season,
            "is_daytime": self.is_daytime,
        }
