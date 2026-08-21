"""The route sub-agent - suggests routes to safety.

Uses the Google Maps Directions API to provide turn-by-turn driving directions,
for example to route a user away from a disaster area to a shelter, hospital, or
other safe location.
"""

from google.adk.agents import Agent

from .models import resolve_model
from .tools import get_directions

_INSTRUCTION = """\
You are a routing specialist for the ReadyNow! emergency-preparedness assistant.
When the user needs to get to safety:
1. Determine a start location and a safe destination (a shelter, hospital, or
   other safe place). Ask a brief clarifying question if either is missing.
2. Call `get_directions` with the origin and destination.
3. Summarize the route clearly: distance, estimated time, and the key
   turn-by-turn steps. Keep it calm, concise, and easy to follow in an
   emergency. If the tool returns an error, explain plainly what went wrong.
"""

route_agent = Agent(
    name="route_agent",
    model=resolve_model(),
    description=(
        "Provides driving routes to safety (shelters, hospitals) using the "
        "Google Maps Directions API."
    ),
    instruction=_INSTRUCTION,
    tools=[get_directions],
)
