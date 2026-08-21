"""The ReadyNow! root coordinator agent.

ReadyNow! is an emergency-preparedness assistant (a FEMA proof of concept). The
root agent describes what the assistant can do, validates and logs input, and
coordinates the specialist sub-agents:

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

You can:
* Give current US weather forecasts and hazard alerts.
* Search the internet for real-time news, emergency alerts, and advisories.
* Provide driving routes to safety (shelters, hospitals, evacuation).
* Answer general safety and preparedness questions with verified information.

If a user simply greets you or asks what you can do, briefly introduce yourself
and list these capabilities.

Delegate each request to the most appropriate sub-agent:
* Weather or forecast questions -> `weather_agent`.
* Requests for news, current events, alerts, or general web search -> `search_agent`.
* Requests for directions, evacuation, or how to get to safety -> `route_agent`.
* Other questions that need a researched, verified answer -> `answer_team`.

IMPORTANT - stay on mission. If a request is not related to emergencies,
safety, preparedness, weather, news/alerts, or routes to safety, politely
decline and remind the user what ReadyNow! is for. Do not help with unrelated
tasks.
"""

root_agent = Agent(
    name="root_agent",
    model=resolve_model(),
    description=(
        "ReadyNow! coordinator - routes emergency-preparedness requests to the "
        "weather, search, route, and answer-team sub-agents."
    ),
    instruction=_INSTRUCTION,
    sub_agents=[weather_agent, search_agent, route_agent, answer_team],
    # Log every prompt and screen it for malicious content before routing.
    before_model_callback=[log_user_prompt, screen_input_safety],
    after_model_callback=log_model_response,
)
