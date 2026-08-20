"""Unit tests for the weather agent's tool functions.

These tests mock the network layer (``requests.get``) so they run offline with
no API keys and no dependency on the ADK or Vertex AI. They cover the success
paths, the important failure paths (denied geocoding, network errors, HTTP
errors, malformed responses), the exact requests sent to each API, and that
the functions expose type hints and docstrings as PEP 8 / PEP 257 recommend.

Run with:

    python -m unittest discover -s tests
"""

import inspect
import os
import typing
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


# A reusable, well-formed geocoding success payload.
_GEOCODE_OK = {
    "status": "OK",
    "results": [
        {
            "geometry": {"location": {"lat": 39.7392, "lng": -104.9903}},
            "formatted_address": "Denver, CO, USA",
        }
    ],
}


class GeocodePlaceTests(unittest.TestCase):
    @patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "test-key"})
    @patch("requests.get")
    def test_success(self, mock_get):
        mock_get.return_value = _fake_response(_GEOCODE_OK)

        result = geocode_place("Denver, CO")

        self.assertEqual(result["status"], "success")
        self.assertAlmostEqual(result["latitude"], 39.7392)
        self.assertAlmostEqual(result["longitude"], -104.9903)
        self.assertEqual(result["formatted_address"], "Denver, CO, USA")

    @patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "test-key"})
    @patch("requests.get")
    def test_sends_address_and_key(self, mock_get):
        mock_get.return_value = _fake_response(_GEOCODE_OK)

        geocode_place("Miami, FL")

        _, kwargs = mock_get.call_args
        self.assertEqual(kwargs["params"]["address"], "Miami, FL")
        self.assertEqual(kwargs["params"]["key"], "test-key")
        # A network timeout must be set so a hung request can't stall the agent.
        self.assertIn("timeout", kwargs)

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
    def test_zero_results(self, mock_get):
        # A valid response that simply found nothing.
        mock_get.return_value = _fake_response({"status": "ZERO_RESULTS", "results": []})

        result = geocode_place("Nowheresville, ZZ")

        self.assertEqual(result["status"], "error")
        self.assertIn("ZERO_RESULTS", result["error_message"])

    @patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "test-key"})
    @patch("requests.get")
    def test_ok_status_but_empty_results(self, mock_get):
        # Defensive: status OK but no results should still be treated as error.
        mock_get.return_value = _fake_response({"status": "OK", "results": []})

        result = geocode_place("Denver, CO")

        self.assertEqual(result["status"], "error")

    @patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "test-key"})
    @patch("requests.get")
    def test_http_error(self, mock_get):
        response = MagicMock()
        response.raise_for_status.side_effect = requests.exceptions.HTTPError("500")
        mock_get.return_value = response

        result = geocode_place("Denver, CO")

        self.assertEqual(result["status"], "error")
        self.assertIn("Geocoding API", result["error_message"])

    @patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "test-key"})
    @patch("requests.get")
    def test_network_error(self, mock_get):
        mock_get.side_effect = requests.exceptions.ConnectionError("boom")

        result = geocode_place("Denver, CO")

        self.assertEqual(result["status"], "error")
        self.assertIn("Geocoding API", result["error_message"])


class GetWeatherTests(unittest.TestCase):
    def _forecast_periods(self, periods):
        """Return (points_response, forecast_response) mocks for the two calls."""
        points = _fake_response(
            {"properties": {"forecast": "https://api.weather.gov/x/forecast"}}
        )
        forecast = _fake_response({"properties": {"periods": periods}})
        return points, forecast

    _PERIOD = {
        "name": "This Afternoon",
        "temperature": 75,
        "temperatureUnit": "F",
        "windSpeed": "10 mph",
        "windDirection": "NW",
        "shortForecast": "Sunny",
        "detailedForecast": "Sunny skies throughout the afternoon.",
    }

    @patch("requests.get")
    def test_success(self, mock_get):
        mock_get.side_effect = list(self._forecast_periods([self._PERIOD]))

        result = get_weather(39.7392, -104.9903)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["period"], "This Afternoon")
        self.assertEqual(result["temperature"], 75)
        self.assertEqual(result["temperature_unit"], "F")
        self.assertEqual(result["wind"], "10 mph NW")
        self.assertEqual(result["short_forecast"], "Sunny")
        self.assertIn("Sunny skies", result["detailed_forecast"])
        self.assertEqual(mock_get.call_count, 2)

    @patch("requests.get")
    def test_builds_points_url_and_sends_user_agent(self, mock_get):
        mock_get.side_effect = list(self._forecast_periods([self._PERIOD]))

        get_weather(39.7392, -104.9903)

        # First call hits the /points endpoint with the lat,lon in the URL.
        first_call = mock_get.call_args_list[0]
        url = first_call.args[0]
        self.assertIn("api.weather.gov/points/39.7392,-104.9903", url)
        # The NWS API requires a descriptive User-Agent header.
        self.assertIn("User-Agent", first_call.kwargs["headers"])

    @patch("requests.get")
    def test_points_call_network_error(self, mock_get):
        mock_get.side_effect = requests.exceptions.Timeout("slow")

        result = get_weather(39.7392, -104.9903)

        self.assertEqual(result["status"], "error")
        self.assertIn("NWS API", result["error_message"])

    @patch("requests.get")
    def test_forecast_call_http_error(self, mock_get):
        # First (points) call succeeds; the second (forecast) call errors.
        points = _fake_response(
            {"properties": {"forecast": "https://api.weather.gov/x/forecast"}}
        )
        mock_get.side_effect = [points, requests.exceptions.HTTPError("503")]

        result = get_weather(39.7392, -104.9903)

        self.assertEqual(result["status"], "error")
        self.assertIn("NWS API", result["error_message"])

    @patch("requests.get")
    def test_malformed_points_response(self, mock_get):
        # Missing "properties" entirely -> KeyError should be handled.
        mock_get.return_value = _fake_response({})

        result = get_weather(39.7392, -104.9903)

        self.assertEqual(result["status"], "error")
        self.assertIn("Unexpected response format", result["error_message"])

    @patch("requests.get")
    def test_empty_forecast_periods(self, mock_get):
        # Valid shape but no periods -> IndexError should be handled.
        mock_get.side_effect = list(self._forecast_periods([]))

        result = get_weather(39.7392, -104.9903)

        self.assertEqual(result["status"], "error")
        self.assertIn("Unexpected response format", result["error_message"])


class ContractTests(unittest.TestCase):
    """Every path must return a dict with a 'status', and errors an 'error_message'."""

    @patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": ""})
    def test_error_dicts_have_error_message(self):
        result = geocode_place("Denver, CO")
        self.assertIsInstance(result, dict)
        self.assertEqual(result["status"], "error")
        self.assertIsInstance(result["error_message"], str)
        self.assertTrue(result["error_message"])

    @patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "test-key"})
    @patch("requests.get")
    def test_success_dict_shape(self, mock_get):
        mock_get.return_value = _fake_response(_GEOCODE_OK)
        result = geocode_place("Denver, CO")
        self.assertEqual(
            set(result),
            {"status", "latitude", "longitude", "formatted_address"},
        )


class SignatureTests(unittest.TestCase):
    """Enforce PEP 8 / PEP 257: type hints on params + return, and docstrings."""

    def test_geocode_place_has_type_hints(self):
        hints = typing.get_type_hints(geocode_place)
        self.assertEqual(hints.get("place"), str)
        self.assertEqual(hints.get("return"), dict)

    def test_get_weather_has_type_hints(self):
        hints = typing.get_type_hints(get_weather)
        self.assertEqual(hints.get("latitude"), float)
        self.assertEqual(hints.get("longitude"), float)
        self.assertEqual(hints.get("return"), dict)

    def test_functions_have_docstrings(self):
        for func in (geocode_place, get_weather):
            doc = inspect.getdoc(func)
            self.assertIsNotNone(doc, f"{func.__name__} is missing a docstring")
            self.assertIn("Args:", doc)
            self.assertIn("Returns:", doc)


if __name__ == "__main__":
    unittest.main()
