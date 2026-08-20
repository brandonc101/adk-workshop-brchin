"""The critique sub-agent (step 2 of the answer team).

Reviews the draft answer and suggests concrete improvements. It does not
rewrite the answer - it only produces suggestions, stored under ``critique``.
"""

from google.adk.agents import Agent

from .models import resolve_model

# {draft_answer} is filled in from session state (set by the search agent).
_INSTRUCTION = """\
You are a critique agent. Here is a draft answer to the user's question:

{draft_answer}

Critically evaluate it. Point out any inaccuracies, missing details, unclear
phrasing, or parts of the question left unanswered. Return a short, specific,
bulleted list of concrete suggestions for how to improve the answer. Do NOT
rewrite the answer yourself - only give suggestions.
"""

critique_agent = Agent(
    name="critique_agent",
    model=resolve_model(),
    description="Reviews the draft answer and suggests improvements.",
    instruction=_INSTRUCTION,
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
    output_key="critique",
)
