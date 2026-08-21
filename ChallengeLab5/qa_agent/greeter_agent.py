"""The greeter sub-agent.

Handles greetings and small talk. Real questions are routed by the coordinator
to the answer team instead.
"""

from google.adk.agents import Agent

from .models import resolve_model

_INSTRUCTION = """\
You are a warm, friendly greeter. Respond briefly and pleasantly to greetings,
thanks, and small talk. If the user asks a real question that needs research,
let them know you'll hand it to the research team.
"""

greeter_agent = Agent(
    name="greeter_agent",
    model=resolve_model(),
    description="Handles greetings, thanks, and small talk.",
    instruction=_INSTRUCTION,
)
