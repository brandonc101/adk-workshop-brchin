"""Integration test for the multi-agent system.

Drives the root (coordinator) agent with a weather question and a general
search question, and prints the ADK event stream for each. The events show the
root agent delegating to the ``weather_agent`` and ``search_agent`` sub-agents
(via ``transfer_to_agent``) and the sub-agents' tool calls - demonstrating that
the sub-agents are actually used.

Run with:

    python test_agents.py
"""

import asyncio

from dotenv import load_dotenv

# Load weather_agent/.env (Maps key, Vertex/model settings, Model Armor).
load_dotenv("weather_agent/.env")

from google.adk.runners import Runner  # noqa: E402
from google.adk.sessions import InMemorySessionService  # noqa: E402
from google.genai import types  # noqa: E402

from weather_agent.agent import root_agent  # noqa: E402

APP_NAME = "multi_agent_app"
USER_ID = "test_user"

# (label, prompt) - one weather question (-> weather_agent) and one general
# question (-> search_agent).
QUERIES = [
    ("WEATHER", "What's the current weather in Denver, CO? Flag any alerts."),
    ("SEARCH", "Who won the most recent FIFA World Cup, and in what year?"),
]


def _describe_event(event) -> list:
    """Return human-readable lines describing one ADK event."""
    author = getattr(event, "author", "?")
    lines = []
    content = getattr(event, "content", None)
    for part in getattr(content, "parts", None) or []:
        call = getattr(part, "function_call", None)
        result = getattr(part, "function_response", None)
        text = getattr(part, "text", None)
        if call is not None:
            args = dict(call.args) if getattr(call, "args", None) else {}
            lines.append(f"[{author}] -> tool_call: {call.name}({args})")
        elif result is not None:
            lines.append(f"[{author}] <- tool_result: {result.name}")
        elif text and text.strip():
            lines.append(f"[{author}] text: {text.strip()}")
    return lines


async def _run_query(runner: Runner, session_id: str, query: str) -> None:
    """Send one query to the root agent and print every event it emits."""
    message = types.Content(role="user", parts=[types.Part(text=query)])
    async for event in runner.run_async(
        user_id=USER_ID, session_id=session_id, new_message=message
    ):
        for line in _describe_event(event):
            print("   ", line)
        if event.is_final_response():
            print(f"    [{getattr(event, 'author', '?')}] === FINAL RESPONSE ===")


async def main() -> None:
    session_service = InMemorySessionService()
    runner = Runner(
        agent=root_agent,
        app_name=APP_NAME,
        session_service=session_service,
    )

    for index, (label, query) in enumerate(QUERIES):
        session_id = f"session_{index}"
        await session_service.create_session(
            app_name=APP_NAME, user_id=USER_ID, session_id=session_id
        )
        print(f"\n{'=' * 72}\n{label} QUERY: {query}\n{'=' * 72}")
        await _run_query(runner, session_id, query)


if __name__ == "__main__":
    asyncio.run(main())
