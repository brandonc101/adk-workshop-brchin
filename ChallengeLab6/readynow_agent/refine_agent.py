"""The refine sub-agent (step 3 of the answer team).

Rewrites the draft answer to incorporate the critique's suggestions, improving
clarity and completeness while preserving the draft's search-grounded facts.
"""

from google.adk.agents import Agent

from .models import resolve_model

# {draft_answer} and {critique} are filled in from session state.
_INSTRUCTION = """\
You are a refine agent. The draft answer, grounded in live web search results,
was:

{draft_answer}

A critique suggested these improvements:

{critique}

Rewrite the answer to improve its clarity, structure, and completeness based on
the critique. CRITICAL: preserve every fact, date, name, and number from the
draft exactly as given - they come from current search results and are
authoritative. Do NOT change, "correct", or update any fact or date based on
your own knowledge, which may be outdated. Return only the improved answer,
with no meta-commentary.
"""

refine_agent = Agent(
    name="refine_agent",
    model=resolve_model(),
    description="Rewrites the answer using the critique, preserving facts.",
    instruction=_INSTRUCTION,
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
    output_key="final_answer",
)
