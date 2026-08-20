"""Unit tests for the weather agent's tool functions.

These tests mock the network layer (``requests.get``) so they run offline with
no API keys and no dependency on the ADK or Vertex AI. They cover the success
paths and the important failure paths (denied geocoding, network errors,
malformed responses) for both tools.

Run with:

    python -m unittest discover -s tests
"""

import os
import unittest
from unittest.mock import MagicMock, patch

import requests

# Import the tool functions. Prefer the normal package import (works in Cloud
# Shell where google-adk is installed); fall back to loading tools.py directly
# so the tests still run in a minimal environment where importing the package
# __init__ (which pulls in google.adk) would fail.
try:  # pragma: no cover - exercised implicitly by the environment
    from weather_agent.tools import geocode_place, get_weather
except Exception:  # pragma: no cover
    import importlib.util
    import pathlib

    _tools_path = (
        pathlib.Path(__file__).resolve().parent.parent
        / "weather_agent"
        / "tools.py"
    )
    _spec = importlib.util.spec_from_file_location("weather_agent_tools", _tools_path)
    _mod = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)
    geocode_place, get_weather = _mod.geocode_place, _mod.get_weather


def _fake_response(json_data: dict) -> MagicMock:
    """Build a fake requests.Response whose .json() returns json_data."""
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = json_data
    return response


class GeocodePlaceTests(unittest.TestCase):
    @patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "test-key"})
    @patch("requests.get")
    def test_success(self, mock_get):
        mock_get.return_value = _fake_response(
            {
                "status": "OK",
                "results": [
                    {
                        "geometry": {"location": {"lat": 39.7392, "lng": -104.9903}},
                        "formatted_address": "Denver, CO, USA",
                    }
                ],
            }
        )

        result = geocode_place("Denver, CO")

        self.assertEqual(result["status"], "success")
        self.assertAlmostEqual(result["latitude"], 39.7392)
        self.assertAlmostEqual(result["longitude"], -104.9903)
        self.assertEqual(result["formatted_address"], "Denver, CO, USA")
        # The API key from the environment should have been sent.
        _, kwargs = mock_get.call_args
        self.assertEqual(kwargs["params"]["key"], "test-key")

    @patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": ""})
    @patch("requests.get")
    def test_missing_api_key(self, mock_get):
        result = geocode_place("Denver, CO")

        self.assertEqual(result["status"], "error")
        self.assertIn("GOOGLE_MAPS_API_KEY", result["error_message"])
        mock_get.assert_not_called()  # must fail before any network call

    @patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "test-key"})
    @patch("requests.get")
    def test_request_denied_surfaces_google_reason(self, mock_get):
        mock_get.return_value = _fake_response(
            {
                "status": "REQUEST_DENIED",
                "error_message": "You must enable Billing on the project.",
            }
        )

        result = geocode_place("Denver, CO")

        self.assertEqual(result["status"], "error")
        self.assertIn("REQUEST_DENIED", result["error_message"])
        self.assertIn("enable Billing", result["error_message"])

    @patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "test-key"})
    @patch("requests.get")
    def test_network_error(self, mock_get):
        mock_get.side_effect = requests.exceptions.ConnectionError("boom")

        result = geocode_place("Denver, CO")

        self.assertEqual(result["status"], "error")
        self.assertIn("Geocoding API", result["error_message"])


class GetWeatherTests(unittest.TestCase):
    @patch("requests.get")
    def test_success(self, mock_get):
        points = _fake_response(
            {"properties": {"forecast": "https://api.weather.gov/x/forecast"}}
        )
        forecast = _fake_response(
            {
                "properties": {
                    "periods": [
                        {
                            "name": "This Afternoon",
                            "temperature": 75,
                            "temperatureUnit": "F",
                            "windSpeed": "10 mph",
                            "windDirection": "NW",
                            "shortForecast": "Sunny",
                            "detailedForecast": "Sunny skies throughout the afternoon.",
                        }
                    ]
                }
            }
        )
        # get_weather makes two calls: /points, then the forecast URL.
        mock_get.side_effect = [points, forecast]

        result = get_weather(39.7392, -104.9903)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["period"], "This Afternoon")
        self.assertEqual(result["temperature"], 75)
        self.assertEqual(result["temperature_unit"], "F")
        self.assertEqual(result["wind"], "10 mph NW")
        self.assertEqual(result["short_forecast"], "Sunny")
        self.assertEqual(mock_get.call_count, 2)

    @patch("requests.get")
    def test_network_error(self, mock_get):
        mock_get.side_effect = requests.exceptions.Timeout("slow")

        result = get_weather(39.7392, -104.9903)

        self.assertEqual(result["status"], "error")
        self.assertIn("NWS API", result["error_message"])

    @patch("requests.get")
    def test_malformed_points_response(self, mock_get):
        # Missing the "properties" key entirely -> KeyError should be handled.
        mock_get.return_value = _fake_response({})

        result = get_weather(39.7392, -104.9903)

        self.assertEqual(result["status"], "error")
        self.assertIn("Unexpected response format", result["error_message"])


if __name__ == "__main__":
    unittest.main()
