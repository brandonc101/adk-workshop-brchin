"""The research sub-agent (step 1 of the answer team).

Uses the ADK built-in Google Search tool to find data and produce an initial
draft answer, stored in session state under ``draft_answer`` for the critique
and refine steps.
"""

from google.adk.agents import Agent
from google.adk.tools import google_search

from .models import gemini_model

_INSTRUCTION = """\
You are a research agent for the ReadyNow! emergency-preparedness assistant.
Use the Google Search tool to find accurate, current information that answers
the user's question - prioritizing official and up-to-date sources - then write
a thorough initial answer based on what you found.
"""

research_agent = Agent(
    name="research_agent",
    model=gemini_model(),  # google_search requires a Gemini model
    description="Finds data with Google Search and drafts an initial answer.",
    instruction=_INSTRUCTION,
    tools=[google_search],
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
    output_key="draft_answer",
)
