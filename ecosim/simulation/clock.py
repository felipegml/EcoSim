
"""Track simulated time, seasons, and daylight."""

from dataclasses import dataclass, field


HOURS_PER_DAY = 24


@dataclass
class SimulationClock:
    seasons: dict[str, int]
    day_night: dict[str, dict[str, int]]

    hour: int = 0
    day: int = 1
    year: int = 1

    def __post_init__(self) -> None:
        """Validate clock configuration."""
        if not self.seasons:
            raise ValueError("At least one season must be configured.")

        if any(
            isinstance(duration, bool)
            or not isinstance(duration, int)
            or duration < 1
            for duration in self.seasons.values()
        ):
            raise ValueError(
                "Every season duration must be a positive integer."
            )

        if set(self.day_night) != set(self.seasons):
            raise ValueError(
                "Day/night settings must exist for every configured season."
            )

        if not 0 <= self.hour < HOURS_PER_DAY:
            raise ValueError("Hour must be between 0 and 23.")

        if not 1 <= self.day <= self.days_per_year:
            raise ValueError(
                "Day must be within the configured simulation year."
            )

        if self.year < 1:
            raise ValueError("Year must be at least 1.")

        for season_name, settings in self.day_night.items():
            sunrise = settings.get("sunrise")
            sunset = settings.get("sunset")

            if (
                not isinstance(sunrise, int)
                or isinstance(sunrise, bool)
                or not isinstance(sunset, int)
                or isinstance(sunset, bool)
                or not 0 <= sunrise <= 23
                or not 1 <= sunset <= HOURS_PER_DAY
                or sunrise >= sunset
            ):
                raise ValueError(
                    f"Invalid sunrise/sunset settings for "
                    f"season {season_name!r}."
                )

    @property
    def days_per_year(self) -> int:
        """Return the total number of days in a configured year."""
        return sum(self.seasons.values())

    def tick(self) -> None:
        """Advance the simulation by one hour."""
        self.hour += 1

        if self.hour >= HOURS_PER_DAY:
            self.hour = 0
            self.day += 1

        if self.day > self.days_per_year:
            self.day = 1
            self.year += 1

    @property
    def season(self) -> str:
        """Return the season containing the current day."""
        day_of_year = self.day

        for season_name, duration in self.seasons.items():
            if day_of_year <= duration:
                return season_name

            day_of_year -= duration

        raise RuntimeError(
            f"Day {self.day} does not belong to a configured season."
        )

    @property
    def is_daytime(self) -> bool:
        """Return whether the current hour is within daylight hours."""
        settings = self.day_night[self.season]
        sunrise = settings["sunrise"]
        sunset = settings["sunset"]

        return sunrise <= self.hour < sunset

    def to_dict(self) -> dict:
        """Return the current clock state."""
        return {
            "hour": self.hour,
            "day": self.day,
            "year": self.year,
            "season": self.season,
            "is_daytime": self.is_daytime,
        }
