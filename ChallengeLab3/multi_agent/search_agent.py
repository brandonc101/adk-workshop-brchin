"""The search sub-agent.

Answers general-knowledge and current-events questions using the ADK built-in
Google Search tool. The built-in tool requires a Gemini model, and Gemini
requires it to be the agent's only tool - so this agent's own transfers are
disabled to prevent ADK from adding a transfer tool alongside it.
"""

from google.adk.agents import Agent
from google.adk.tools import google_search

from .models import gemini_model

_INSTRUCTION = """\
You are a research specialist. Use the Google Search tool to find accurate,
up-to-date information, then answer the user's question concisely and mention
what you found.
"""

search_agent = Agent(
    name="search_agent",
    model=gemini_model(),
    description=(
        "Answers general-knowledge and current-events questions using Google "
        "Search."
    ),
    instruction=_INSTRUCTION,
    tools=[google_search],
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
)
