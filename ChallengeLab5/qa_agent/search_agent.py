"""The search sub-agent (step 1 of the answer team).

Uses the ADK built-in Google Search tool to find data and produce an initial
draft answer, stored in session state under ``draft_answer`` for the critique
and refine steps.
"""

from google.adk.agents import Agent
from google.adk.tools import google_search

from .models import gemini_model

_INSTRUCTION = """\
You are a research agent. Use the Google Search tool to find accurate, current
information that answers the user's question, then write a thorough initial
answer based on what you found.
"""

search_agent = Agent(
    name="search_agent",
    model=gemini_model(),  # google_search requires a Gemini model
    description="Finds data with Google Search and drafts an initial answer.",
    instruction=_INSTRUCTION,
    tools=[google_search],
    # google_search must be the only tool; prevent ADK from adding a transfer
    # tool alongside it.
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
    # Store this agent's answer in state["draft_answer"] for the next steps.
    output_key="draft_answer",
)
