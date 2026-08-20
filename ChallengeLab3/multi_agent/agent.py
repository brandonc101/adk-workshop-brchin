"""The root coordinator agent for the multi-agent system.

Receives every user request, logs it, screens it for malicious content with
Google Cloud Model Armor, then delegates to the appropriate sub-agent:

* ``weather_agent`` - US weather questions (see ``weather_agent.py``).
* ``search_agent``  - general / current-events questions (see ``search_agent.py``).

``root_agent`` is the entry point the ADK runs (``adk run multi_agent``).
"""

import logging

from google.adk.agents import Agent

from .callbacks import log_model_response, log_user_prompt, screen_input_safety
from .models import resolve_model
from .search_agent import search_agent
from .weather_agent import weather_agent

# Show the callback log lines ([USER PROMPT], [MODEL RESPONSE], [BLOCKED]).
logging.basicConfig(level=logging.INFO)

_INSTRUCTION = """\
You are a coordinating assistant with two specialist sub-agents:

* `weather_agent` - for questions about current weather or forecasts in US cities.
* `search_agent`  - for general knowledge, current events, or anything that
  needs an up-to-date web search.

Read each user request and delegate it to the most appropriate sub-agent. Send
weather questions to `weather_agent` and everything else that needs facts to
`search_agent`. Do not try to answer specialist questions yourself.
"""

root_agent = Agent(
    name="root_agent",
    model=resolve_model(),
    description="Coordinator that routes requests to the weather or search agent.",
    instruction=_INSTRUCTION,
    sub_agents=[weather_agent, search_agent],
    # Log every prompt and screen it for malicious content before routing.
    before_model_callback=[log_user_prompt, screen_input_safety],
    after_model_callback=log_model_response,
)
