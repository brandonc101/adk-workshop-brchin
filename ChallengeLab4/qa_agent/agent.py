"""The root coordinator agent.

Receives every user request, logs it, screens it for malicious content with
Google Cloud Model Armor, then delegates:

* greetings / small talk -> ``greeter_agent``
* questions to answer     -> ``answer_team`` (search -> critique -> refine)

``root_agent`` is the entry point the ADK runs (``adk run qa_agent``).
"""

import logging

from google.adk.agents import Agent

from .answer_team import answer_team
from .callbacks import log_model_response, log_user_prompt, screen_input_safety
from .greeter_agent import greeter_agent
from .models import resolve_model

# Show the callback log lines ([USER PROMPT], [MODEL RESPONSE], [BLOCKED]).
logging.basicConfig(level=logging.INFO)

_INSTRUCTION = """\
You are a coordinating assistant. Decide how to handle each user message:

* If it is a greeting, thanks, or small talk, transfer to `greeter_agent`.
* If it is a question that needs a researched, verified answer, transfer to
  `answer_team`, which will search for information, critique the draft, and
  refine it into a final answer.

Do not answer questions yourself - delegate to the right sub-agent.
"""

root_agent = Agent(
    name="root_agent",
    model=resolve_model(),
    description="Coordinator: greets, or routes questions to the answer team.",
    instruction=_INSTRUCTION,
    sub_agents=[greeter_agent, answer_team],
    # Log every prompt and screen it for malicious content before routing.
    before_model_callback=[log_user_prompt, screen_input_safety],
    after_model_callback=log_model_response,
)
