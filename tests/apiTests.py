import unittest
from script import get_coordinates, get_weather_now, get_all_cities

import asyncio


class TestWeatherAPI(unittest.TestCase):

    def test_get_coordinates_success(self):
        coordinates = asyncio.run(get_coordinates("Moscow"))

        self.assertIsInstance(coordinates, tuple)
        self.assertEqual(len(coordinates), 2)
        self.assertTrue(isinstance(coordinates[0], float))
        self.assertTrue(isinstance(coordinates[1], float))

    def test_get_coordinates_invalid_city(self):
        coordinates = asyncio.run(get_coordinates("asfdasfdasf"))
        self.assertIsNone(coordinates)

    def test_get_weather_now_success(self):
        weather = asyncio.run(get_weather_now(55.7558, 37.6173))
        self.assertIn("Current temperature_2m", weather)
        self.assertIn("Current surface_pressure", weather)
        self.assertIn("Current wind_speed_10m", weather)
        self.assertIsInstance(weather["Current temperature_2m"], float)
        self.assertIsInstance(weather["Current surface_pressure"], float)
        self.assertIsInstance(weather["Current wind_speed_10m"], float)

    def test_get_weather_now_invalid_coordinates(self):
        with self.assertRaises(Exception):
            asyncio.run(get_weather_now(999, 999))  # Некорректные координаты

    def test_get_all_cities(self):
        cities = asyncio.run(get_all_cities())
        self.assertIsInstance(cities, dict)
        self.assertIn("all_cities", cities)
        self.assertIsInstance(cities["all_cities"], list)


if __name__ == "__main__":
    unittest.main()
