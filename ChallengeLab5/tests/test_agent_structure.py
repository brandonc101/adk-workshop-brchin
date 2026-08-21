"""Structure tests for the answer-team workflow.

Assert that the coordinator, greeter, and the Sequential answer team (search ->
critique -> refine) are wired together correctly, with the right output keys,
transfer flags, and callbacks. These import the ADK, so they run where
``google-adk`` is installed (e.g. Cloud Shell) and auto-skip where it is not.

Run with:

    python -m unittest discover -s tests
"""

import unittest

try:  # ADK is required for these tests; skip cleanly if it isn't installed.
    from google.adk.agents import SequentialAgent

    from qa_agent.agent import root_agent
    from qa_agent.answer_team import answer_team
    from qa_agent.callbacks import (
        log_model_response,
        log_user_prompt,
        screen_input_safety,
        validate_us_location,
    )
    from qa_agent.critique_agent import critique_agent
    from qa_agent.greeter_agent import greeter_agent
    from qa_agent.refine_agent import refine_agent
    from qa_agent.search_agent import search_agent
    from qa_agent.weather_agent import weather_agent

    _ADK_AVAILABLE = True
except Exception:  # pragma: no cover - depends on the environment
    _ADK_AVAILABLE = False


def _as_list(callback):
    """Normalize a callback attribute (callable | list | None) to a list."""
    if callback is None:
        return []
    if isinstance(callback, (list, tuple)):
        return list(callback)
    return [callback]


def _tool_names(agent):
    """Return the best-effort names of an agent's tools."""
    names = []
    for tool in getattr(agent, "tools", []) or []:
        name = (
            getattr(tool, "name", None)
            or getattr(tool, "__name__", None)
            or type(tool).__name__
        )
        names.append(name)
    return names


@unittest.skipUnless(_ADK_AVAILABLE, "google-adk not installed in this environment")
class AnswerTeamStructureTests(unittest.TestCase):
    def test_root_delegates_to_greeter_weather_and_answer_team(self):
        names = {sa.name for sa in root_agent.sub_agents}
        self.assertEqual(names, {"greeter_agent", "weather_agent", "answer_team"})

    def test_weather_agent_has_tools_and_us_validation(self):
        names = _tool_names(weather_agent)
        self.assertIn("geocode_place", names)
        self.assertIn("get_weather", names)
        before = _as_list(weather_agent.before_model_callback)
        self.assertIn(validate_us_location, before)

    def test_answer_team_is_a_sequential_workflow(self):
        self.assertIsInstance(answer_team, SequentialAgent)

    def test_answer_team_runs_search_critique_refine_in_order(self):
        order = [sa.name for sa in answer_team.sub_agents]
        self.assertEqual(order, ["search_agent", "critique_agent", "refine_agent"])

    def test_search_agent_uses_only_google_search(self):
        self.assertEqual(len(search_agent.tools), 1)
        self.assertTrue(
            any("search" in n.lower() for n in _tool_names(search_agent)),
            msg=f"expected a search tool, got {_tool_names(search_agent)}",
        )

    def test_output_keys_chain_the_steps(self):
        self.assertEqual(search_agent.output_key, "draft_answer")
        self.assertEqual(critique_agent.output_key, "critique")
        self.assertEqual(refine_agent.output_key, "final_answer")

    def test_greeter_agent_is_a_sub_agent(self):
        self.assertIn(greeter_agent, root_agent.sub_agents)

    def test_root_callbacks_are_wired(self):
        before = _as_list(root_agent.before_model_callback)
        after = _as_list(root_agent.after_model_callback)
        self.assertIn(log_user_prompt, before)
        self.assertIn(screen_input_safety, before)
        self.assertIn(log_model_response, after)


if __name__ == "__main__":
    unittest.main()
