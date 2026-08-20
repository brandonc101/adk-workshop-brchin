"""The weather sub-agent.

Answers US weather questions using the National Weather Service and Google Maps
geocoding tools, with a callback that rejects non-US locations.
"""

from google.adk.agents import Agent

from .callbacks import validate_us_location
from .models import resolve_model
from .tools import geocode_place, get_weather

_INSTRUCTION = """\
You are a US weather specialist. When asked about the weather for a place:
1. Call `geocode_place` to convert the place name into latitude and longitude.
2. Call `get_weather` with that latitude and longitude.
3. Give a short (1-3 sentence) summary, and start with a WEATHER ALERT if
   conditions look hazardous (storms, extreme heat/cold, high winds, flooding).
Only US locations are supported.
"""

weather_agent = Agent(
    name="weather_agent",
    model=resolve_model(),
    description=(
        "Provides real-time weather and alerts for US cities using the "
        "National Weather Service API and Google Maps geocoding."
    ),
    instruction=_INSTRUCTION,
    tools=[geocode_place, get_weather],
    before_model_callback=[validate_us_location],
)
