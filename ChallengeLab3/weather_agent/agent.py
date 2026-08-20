"""Multi-agent weather + search system built with the ADK.

Three agents:

* ``weather_agent`` - answers US weather questions using the NWS + Google Maps
  tools (with a US-location validation callback).
* ``search_agent`` - answers general questions using the ADK built-in Google
  Search tool (which requires a Gemini model).
* ``root_agent``   - the coordinator. It receives every user request, screens
  it for safety (Model Armor) and logs it, then delegates to the appropriate
  sub-agent.

The model backend for the coordinator and weather agent is selectable with the
``MODEL_BACKEND`` environment variable (Gemini default; Claude/GPT via LiteLLM).
The search agent is always a Gemini model, because the built-in Google Search
tool only supports Gemini.
"""

import logging
import os

from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools import google_search

from .callbacks import (
    log_model_response,
    log_user_prompt,
    screen_input_safety,
    validate_us_location,
)
from .tools import geocode_place, get_weather

# Show the callback log lines ([USER PROMPT], [MODEL RESPONSE], [BLOCKED]).
logging.basicConfig(level=logging.INFO)


def _gemini_model() -> str:
    """Return the Gemini model id (used by the search agent)."""
    return os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


def _resolve_model():
    """Return the model for the coordinator/weather agent per MODEL_BACKEND.

    Returns:
        A Gemini model-name ``str`` or a ``LiteLlm`` instance (Claude/GPT).
    """
    backend = os.getenv("MODEL_BACKEND", "gemini").lower()

    if backend == "gemini":
        return _gemini_model()

    if backend in ("claude", "anthropic"):
        model_id = os.getenv("CLAUDE_MODEL", "vertex_ai/claude-sonnet-4-5")
        if model_id.startswith("vertex_ai/"):
            os.environ.setdefault(
                "VERTEXAI_PROJECT", os.getenv("GOOGLE_CLOUD_PROJECT", "")
            )
            os.environ.setdefault(
                "VERTEXAI_LOCATION", os.getenv("CLAUDE_LOCATION", "us-east5")
            )
        return LiteLlm(model=model_id)

    if backend in ("gpt", "openai"):
        return LiteLlm(model=os.getenv("OPENAI_MODEL", "openai/gpt-4o"))

    raise ValueError(
        f"Unknown MODEL_BACKEND '{backend}'. Use 'gemini', 'claude', or 'gpt'."
    )


_WEATHER_INSTRUCTION = """\
You are a US weather specialist. When asked about the weather for a place:
1. Call `geocode_place` to convert the place name into latitude and longitude.
2. Call `get_weather` with that latitude and longitude.
3. Give a short (1-3 sentence) summary, and start with a WEATHER ALERT if
   conditions look hazardous (storms, extreme heat/cold, high winds, flooding).
Only US locations are supported.
"""

_SEARCH_INSTRUCTION = """\
You are a research specialist. Use the Google Search tool to find accurate,
up-to-date information, then answer the user's question concisely and mention
what you found.
"""

_ROOT_INSTRUCTION = """\
You are a coordinating assistant with two specialist sub-agents:

* `weather_agent` - for questions about current weather or forecasts in US cities.
* `search_agent`  - for general knowledge, current events, or anything that
  needs an up-to-date web search.

Read each user request and delegate it to the most appropriate sub-agent. Send
weather questions to `weather_agent` and everything else that needs facts to
`search_agent`. Do not try to answer specialist questions yourself.
"""

# --- Sub-agent: weather (US-only, validated) ---
weather_agent = Agent(
    name="weather_agent",
    model=_resolve_model(),
    description=(
        "Provides real-time weather and alerts for US cities using the "
        "National Weather Service API and Google Maps geocoding."
    ),
    instruction=_WEATHER_INSTRUCTION,
    tools=[geocode_place, get_weather],
    before_model_callback=[validate_us_location],
)

# --- Sub-agent: search (built-in Google Search; requires a Gemini model) ---
search_agent = Agent(
    name="search_agent",
    model=_gemini_model(),
    description=(
        "Answers general-knowledge and current-events questions using Google "
        "Search."
    ),
    instruction=_SEARCH_INSTRUCTION,
    tools=[google_search],
    # Gemini requires google_search to be the ONLY tool. As a sub-agent, ADK
    # would otherwise add a transfer_to_agent tool alongside it, which Gemini
    # rejects ("Multiple tools are supported only when they are all search
    # tools"). Disabling this agent's own transfers keeps google_search alone.
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
)

# --- Root coordinator: delegates to the sub-agents ---
root_agent = Agent(
    name="root_agent",
    model=_resolve_model(),
    description="Coordinator that routes requests to the weather or search agent.",
    instruction=_ROOT_INSTRUCTION,
    sub_agents=[weather_agent, search_agent],
    # Log every prompt and screen it for malicious content before routing.
    before_model_callback=[log_user_prompt, screen_input_safety],
    after_model_callback=log_model_response,
)
