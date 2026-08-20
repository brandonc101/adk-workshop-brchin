"""The answer team - a Sequential workflow agent.

Runs the three answer-team sub-agents in order:

    search_agent  -> critique_agent -> refine_agent

so the system answers, verifies (critiques), and refines the answer before
returning it. Data flows between steps via session state (``draft_answer``,
``critique``, ``final_answer``).
"""

from google.adk.agents import SequentialAgent

from .critique_agent import critique_agent
from .refine_agent import refine_agent
from .search_agent import search_agent

answer_team = SequentialAgent(
    name="answer_team",
    description=(
        "Answers a question, then verifies and refines the answer: it searches "
        "for data, critiques the draft, and rewrites it into a final answer."
    ),
    sub_agents=[search_agent, critique_agent, refine_agent],
)
