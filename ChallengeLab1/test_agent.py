"""Test / demonstration harness for the weather agent.

Runs the agent against several US cities and prints each response, showing
that the geocoding + weather tools and the model work end to end. Run it with:

    python test_agent.py

This uses the ADK Runner with an in-memory session service, so it exercises
the real agent (tool calls included) exactly as `adk run` would.
"""

import asyncio
import os

from dotenv import load_dotenv

# Load weather_agent/.env so GOOGLE_MAPS_API_KEY and the Vertex/model settings
# are available when we run this script directly (adk web/run load it for you).
load_dotenv("weather_agent/.env")

from google.adk.runners import Runner  # noqa: E402  (import after load_dotenv)
from google.adk.sessions import InMemorySessionService  # noqa: E402
from google.genai import types  # noqa: E402

from weather_agent.agent import root_agent  # noqa: E402

APP_NAME = "weather_app"
USER_ID = "test_user"

# On a rate-limited model (e.g. a third-party model on Vertex AI with a low
# per-minute quota), retry transient 429s instead of failing the run.
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
RETRY_DELAY = float(os.getenv("RETRY_DELAY_SECONDS", "20"))

# A spread of US cities in different climate zones.
CITIES = [
    "New York, NY",
    "Chicago, IL",
    "Denver, CO",
    "Miami, FL",
    "Seattle, WA",
]


async def _ask(runner: Runner, session_id: str, query: str) -> str:
    """Send one query to the agent and return its final text response.

    Retries on transient rate-limit errors (HTTP 429 / RESOURCE_EXHAUSTED),
    which low per-minute model quotas can trigger.
    """
    message = types.Content(role="user", parts=[types.Part(text=query)])
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            final_text = ""
            async for event in runner.run_async(
                user_id=USER_ID, session_id=session_id, new_message=message
            ):
                if event.is_final_response() and event.content and event.content.parts:
                    final_text = event.content.parts[0].text
            return final_text
        except Exception as exc:  # noqa: BLE001 - re-raised after retries
            is_rate_limit = "429" in str(exc) or "RESOURCE_EXHAUSTED" in str(exc)
            if is_rate_limit and attempt < MAX_RETRIES:
                print(
                    f"  [rate limited; waiting {RETRY_DELAY:.0f}s then retrying "
                    f"(attempt {attempt}/{MAX_RETRIES})]"
                )
                await asyncio.sleep(RETRY_DELAY)
                continue
            raise
    return ""


async def main() -> None:
    session_service = InMemorySessionService()
    runner = Runner(
        agent=root_agent,
        app_name=APP_NAME,
        session_service=session_service,
    )

    for index, city in enumerate(CITIES):
        session_id = f"session_{index}"
        await session_service.create_session(
            app_name=APP_NAME, user_id=USER_ID, session_id=session_id
        )
        query = (
            f"What is the current weather in {city}? "
            "Give me a short summary and flag any weather alerts."
        )
        print(f"\n{'=' * 60}\n{city}\n{'=' * 60}")
        print(await _ask(runner, session_id, query))


if __name__ == "__main__":
    asyncio.run(main())
