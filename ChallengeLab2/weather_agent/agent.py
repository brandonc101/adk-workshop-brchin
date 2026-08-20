"""Weather agent built with the Google Agent Development Kit (ADK).

The agent exposes two tools (``geocode_place`` and ``get_weather``) and is
configured to work with either Gemini (default) or a third-party model such
as Claude or GPT via LiteLLM. The active model is selected with the
``MODEL_BACKEND`` environment variable so no code changes are needed to swap
providers.
"""

import logging
import os

from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

from .callbacks import log_model_response, log_user_prompt, validate_user_input
from .tools import geocode_place, get_weather

# Show the callback log lines ([USER PROMPT], [MODEL RESPONSE], [BLOCKED]).
logging.basicConfig(level=logging.INFO)


def _resolve_model():
    """Return the model object/string for the configured backend.

    The backend is chosen with the ``MODEL_BACKEND`` environment variable:

    * ``gemini`` (default) - a Gemini model string, run through Vertex AI.
    * ``claude``           - Anthropic Claude via LiteLLM (needs ANTHROPIC_API_KEY).
    * ``gpt``              - OpenAI GPT via LiteLLM (needs OPENAI_API_KEY).

    Returns:
        Either a model-name ``str`` (Gemini) or a ``LiteLlm`` instance
        (third-party models), suitable for passing to ``Agent(model=...)``.
    """
    backend = os.getenv("MODEL_BACKEND", "gemini").lower()

    if backend == "gemini":
        return os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    if backend in ("claude", "anthropic"):
        # Two ways to reach Claude:
        #   * "anthropic/claude-..."  -> Anthropic API (needs ANTHROPIC_API_KEY)
        #   * "vertex_ai/claude-..."  -> Claude via your GCP project's Vertex AI
        #     Model Garden (no separate key; uses your gcloud credentials).
        model_id = os.getenv("CLAUDE_MODEL", "vertex_ai/claude-sonnet-4-5")
        if model_id.startswith("vertex_ai/"):
            # LiteLLM reads VERTEXAI_PROJECT / VERTEXAI_LOCATION for Vertex.
            # Claude on Vertex lives in specific regions (e.g. us-east5), which
            # differ from the Gemini region, so it has its own location var.
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


_INSTRUCTION = """\
You are a friendly and concise US weather assistant.

When a user asks about the weather for a place, follow these steps:
1. Call `geocode_place` to convert the place name into latitude and longitude.
2. Call `get_weather` with that latitude and longitude.
3. Give the user a short (1-3 sentence) summary of the current conditions,
   including the temperature and a plain-language description.
4. If the conditions look hazardous (for example thunderstorms, high winds,
   extreme heat or cold, snow, or flooding), call it out clearly as a
   WEATHER ALERT at the start of your reply.

If either tool returns a status of "error", explain to the user plainly what
went wrong instead of guessing. Only US locations are supported, because the
National Weather Service API only covers the United States and its
territories.
"""

# The ADK looks for a module-level `root_agent` when you run `adk web`,
# `adk run`, or import the package.
root_agent = Agent(
    name="weather_agent",
    model=_resolve_model(),
    description=(
        "Retrieves real-time US weather using the National Weather Service "
        "API and Google Maps geocoding, and summarizes it for the user."
    ),
    instruction=_INSTRUCTION,
    tools=[geocode_place, get_weather],
    # Before the model runs: log the prompt, then validate it (US-only +
    # Model Armor). After the model runs: log the response.
    before_model_callback=[log_user_prompt, validate_user_input],
    after_model_callback=log_model_response,
)
