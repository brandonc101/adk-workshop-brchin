"""The critique sub-agent (step 2 of the answer team).

Reviews the draft answer and suggests improvements to its clarity and
completeness. It does not rewrite the answer or change facts - the draft is
grounded in live search results, so its facts and dates are authoritative.
"""

from google.adk.agents import Agent

from .models import resolve_model

# {draft_answer} is filled in from session state (set by the search agent).
_INSTRUCTION = """\
You are a critique agent. Here is a draft answer produced from live web search
results:

{draft_answer}

The draft is grounded in current, up-to-date search results, so treat its
facts, dates, names, and numbers as authoritative and current. Do NOT flag them
as wrong, outdated, or "in the future" based on your own knowledge - your
training data may be out of date, and the search results are more current than
you are.

Focus your critique ONLY on clarity, structure, completeness, and whether the
answer fully addresses the question. Return a short, specific, bulleted list of
suggestions for improving the writing and coverage. Do NOT suggest changing any
facts or dates, and do NOT rewrite the answer yourself.
"""

critique_agent = Agent(
    name="critique_agent",
    model=resolve_model(),
    description="Reviews the draft answer's clarity and completeness.",
    instruction=_INSTRUCTION,
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
    output_key="critique",
)
