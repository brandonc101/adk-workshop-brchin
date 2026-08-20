"""The refine sub-agent (step 3 of the answer team).

Rewrites the draft answer to incorporate the critique's suggestions and
produces the final answer, stored under ``final_answer``.
"""

from google.adk.agents import Agent

from .models import resolve_model

# {draft_answer} and {critique} are filled in from session state.
_INSTRUCTION = """\
You are a refine agent. The draft answer to the user's question was:

{draft_answer}

A critique suggested these improvements:

{critique}

Rewrite the answer to incorporate the suggestions. Produce a single, polished,
accurate, well-organized final answer to the user's question. Return only the
improved answer, with no meta-commentary about the changes.
"""

refine_agent = Agent(
    name="refine_agent",
    model=resolve_model(),
    description="Rewrites the answer using the critique's suggestions.",
    instruction=_INSTRUCTION,
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
    output_key="final_answer",
)
