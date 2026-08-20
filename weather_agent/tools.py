"""Tools for the weather agent.

Contains two tool functions that the ADK agent can call:

* ``geocode_place`` - converts a place name/address into latitude and
  longitude using the Google Maps Geocoding API.
* ``get_weather`` - retrieves the current forecast for a latitude/longitude
  using the United States National Weather Service (NWS) API.

Both functions follow the PEP 8 style guide, use type hints, and return a
plain ``dict`` so the agent's model can reason about the result.
"""

import os

import requests

# A descriptive User-Agent is required by the NWS API. Replace the contact
# address with your own if you deploy this for real.
_NWS_USER_AGENT = "adk-weather-challenge-lab (student@example.com)"

# Reasonable network timeout (seconds) so a hung request can't stall the agent.
_TIMEOUT = 15


def geocode_place(place: str) -> dict:
    """Convert a place name or address into latitude and longitude.

    Uses the Google Maps Geocoding API. The API key is read from the
    ``GOOGLE_MAPS_API_KEY`` environment variable so it is never hard-coded
    into the source.

    Args:
        place: A human-readable place name or address, for example
            ``"Denver, CO"`` or ``"1600 Amphitheatre Parkway, Mountain View"``.

    Returns:
        A dictionary describing the result. On success it contains::

            {
                "status": "success",
                "latitude": <float>,
                "longitude": <float>,
                "formatted_address": <str>,
            }

        On failure it contains::

            {"status": "error", "error_message": <str>}
    """
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return {
            "status": "error",
            "error_message": "GOOGLE_MAPS_API_KEY environment variable is not set.",
        }

    try:
        response = requests.get(
            "https://maps.googleapis.com/maps/api/geocode/json",
            params={"address": place, "key": api_key},
            timeout=_TIMEOUT,
        )
        response.raise_for_status()
        payload = response.json()
    except requests.exceptions.RequestException as exc:
        return {
            "status": "error",
            "error_message": f"Could not reach the Geocoding API: {exc}",
        }

    if payload.get("status") != "OK" or not payload.get("results"):
        return {
            "status": "error",
            "error_message": (
                f"Geocoding failed for '{place}': {payload.get('status', 'UNKNOWN')}"
            ),
        }

    top_result = payload["results"][0]
    location = top_result["geometry"]["location"]
    return {
        "status": "success",
        "latitude": location["lat"],
        "longitude": location["lng"],
        "formatted_address": top_result["formatted_address"],
    }


def get_weather(latitude: float, longitude: float) -> dict:
    """Retrieve the current weather forecast for a US latitude/longitude.

    Uses the United States National Weather Service (NWS) API, which provides
    free forecasts for locations within the United States and its territories.
    The NWS API is a two-step lookup: the ``/points`` endpoint returns a
    forecast URL for the grid cell, which is then fetched for the forecast
    periods.

    Args:
        latitude: The latitude of the location in decimal degrees.
        longitude: The longitude of the location in decimal degrees.

    Returns:
        A dictionary describing the result. On success it contains::

            {
                "status": "success",
                "period": <str>,            # e.g. "This Afternoon"
                "temperature": <int>,
                "temperature_unit": <str>,  # "F" or "C"
                "wind": <str>,              # e.g. "10 mph NW"
                "short_forecast": <str>,    # e.g. "Sunny"
                "detailed_forecast": <str>,
            }

        On failure it contains::

            {"status": "error", "error_message": <str>}
    """
    headers = {"User-Agent": _NWS_USER_AGENT, "Accept": "application/geo+json"}

    try:
        points = requests.get(
            f"https://api.weather.gov/points/{latitude},{longitude}",
            headers=headers,
            timeout=_TIMEOUT,
        )
        points.raise_for_status()
        forecast_url = points.json()["properties"]["forecast"]

        forecast = requests.get(forecast_url, headers=headers, timeout=_TIMEOUT)
        forecast.raise_for_status()
        period = forecast.json()["properties"]["periods"][0]
    except requests.exceptions.RequestException as exc:
        return {
            "status": "error",
            "error_message": (
                "Could not retrieve weather from the NWS API "
                f"(is this a US location?): {exc}"
            ),
        }
    except (KeyError, IndexError) as exc:
        return {
            "status": "error",
            "error_message": f"Unexpected response format from the NWS API: {exc}",
        }

    return {
        "status": "success",
        "period": period["name"],
        "temperature": period["temperature"],
        "temperature_unit": period["temperatureUnit"],
        "wind": f"{period['windSpeed']} {period['windDirection']}",
        "short_forecast": period["shortForecast"],
        "detailed_forecast": period["detailedForecast"],
    }
