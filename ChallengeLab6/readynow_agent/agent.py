"""The ReadyNow! root coordinator agent.

ReadyNow! is an emergency-preparedness assistant (a FEMA proof of concept). The
root agent describes what the assistant can do, validates and logs input, and
coordinates the specialist sub-agents - each exposed as a tool so the
coordinator can call one or more of them in a single turn and combine their
results (e.g. a local forecast AND nationwide alerts in one request):

* ``weather_agent`` - US weather forecasts and alerts.
* ``search_agent``  - real-time internet and news search / alerts.
* ``route_agent``   - driving routes to safety (Google Maps Directions).
* ``answer_team``   - a Sequential workflow (research -> critique -> refine)
  that answers general questions and validates/refines the response.

Input is screened for malicious content with Google Cloud Model Armor, and
off-mission requests are declined. Every prompt and response is logged.

``root_agent`` is the entry point the ADK runs (``adk run readynow_agent``).
"""

import logging

from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool

from .answer_team import answer_team
from .callbacks import log_model_response, log_user_prompt, screen_input_safety
from .models import resolve_model
from .route_agent import route_agent
from .search_agent import search_agent
from .weather_agent import weather_agent

# Show the callback log lines ([USER PROMPT], [MODEL RESPONSE], [BLOCKED]).
logging.basicConfig(level=logging.INFO)

_INSTRUCTION = """\
You are ReadyNow!, an emergency-preparedness assistant built for FEMA. Your
mission is to help people stay safe before, during, and after emergencies.

You have four specialist tools:
* `weather_agent` - current US weather forecasts and hazard alerts for a place.
* `search_agent`  - real-time internet/news search (breaking news, nationwide
  alerts and advisories).
* `route_agent`   - driving routes to safety (shelters, hospitals, evacuation).
* `answer_team`   - researched, verified answers to general safety questions.

For each user message, decide which tool(s) are needed and call them. A single
message may need MORE THAN ONE tool - for example "the weather in Miami AND any
severe weather warnings in the US" should call BOTH `weather_agent` (Miami) and
`search_agent` (nationwide warnings). After the tools return, compose one clear,
well-written answer that addresses every part of the request.

If the user simply greets you or asks what you can do, briefly introduce
yourself and list these capabilities (do not call a tool).

IMPORTANT - stay on mission. If a request is not related to emergencies,
safety, preparedness, weather, news/alerts, or routes to safety, politely
decline and remind the user what ReadyNow! is for. Do not help with unrelated
tasks.
"""

root_agent = Agent(
    name="root_agent",
    model=resolve_model(),
    description=(
        "ReadyNow! coordinator - uses the weather, search, route, and "
        "answer-team specialists (as tools) to handle emergency-preparedness "
        "requests, including multi-part questions."
    ),
    instruction=_INSTRUCTION,
    tools=[
        AgentTool(agent=weather_agent),
        AgentTool(agent=search_agent),
        AgentTool(agent=route_agent),
        AgentTool(agent=answer_team),
    ],
    # Log every prompt and screen it for malicious content before routing.
    before_model_callback=[log_user_prompt, screen_input_safety],
    after_model_callback=log_model_response,
)
