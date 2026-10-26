import unittest

from ecosim.simulation.weather import WeatherSimulation


class TestWeatherSimulation(unittest.TestCase):
    def test_weather_starts_clear(self):
        weather = WeatherSimulation()

        self.assertFalse(weather.is_raining)
        self.assertEqual(weather.intensity, "none")

    def test_rain_starts_when_chance_is_certain(self):
        weather = WeatherSimulation(
            settings={
                "rain_chance_per_tick": {
                    "spring": 1.0,
                },
                "minimum_duration_ticks": 3,
                "maximum_duration_ticks": 3,
            },
            seed=42,
        )

        weather.tick("spring")

        self.assertTrue(weather.is_raining)
        self.assertEqual(weather.rain_ticks_remaining, 3)

    def test_rain_increases_moisture(self):
        from ecosim.simulation.terrain import TerrainSimulation

        terrain = TerrainSimulation([["grass"]])
        initial = terrain.moisture[0][0]

        terrain.tick("spring", rain_amount=0.1)

        self.assertGreater(terrain.moisture[0][0], initial)


if __name__ == "__main__":
    unittest.main()