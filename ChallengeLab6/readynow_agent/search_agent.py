"""The search sub-agent - real-time internet and news search.

Uses the ADK built-in Google Search tool to answer direct search requests and
surface real-time news and alerts relevant to safety and emergencies.
"""

from google.adk.agents import Agent
from google.adk.tools import google_search

from .models import gemini_model

_INSTRUCTION = """\
You are a search specialist for the ReadyNow! emergency-preparedness assistant.
Use the Google Search tool to find accurate, up-to-date information - especially
breaking news, emergency alerts, and official advisories - then answer the
user's question concisely and mention what you found and when.
"""

search_agent = Agent(
    name="search_agent",
    model=gemini_model(),  # google_search requires a Gemini model
    description=(
        "Searches the internet for real-time news, alerts, and general "
        "information."
    ),
    instruction=_INSTRUCTION,
    tools=[google_search],
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
)
