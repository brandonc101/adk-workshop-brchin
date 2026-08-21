"""Structure tests for the ReadyNow! multi-agent system.

Assert that the root coordinator, its specialist sub-agents (weather, search,
route), and the Sequential answer team (research -> critique -> refine) are
wired together correctly, with the right tools, transfer flags, output keys, and
callbacks. These import the ADK, so they run where ``google-adk`` is installed
(e.g. Cloud Shell) and auto-skip where it is not.

Run with:

    python -m unittest discover -s tests
"""

import unittest

try:  # ADK is required for these tests; skip cleanly if it isn't installed.
    from google.adk.agents import SequentialAgent

    from readynow_agent.agent import root_agent
    from readynow_agent.answer_team import answer_team
    from readynow_agent.callbacks import (
        log_model_response,
        log_user_prompt,
        screen_input_safety,
        validate_us_location,
    )
    from readynow_agent.critique_agent import critique_agent
    from readynow_agent.refine_agent import refine_agent
    from readynow_agent.research_agent import research_agent
    from readynow_agent.route_agent import route_agent
    from readynow_agent.search_agent import search_agent
    from readynow_agent.weather_agent import weather_agent

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
class ReadyNowStructureTests(unittest.TestCase):
    def test_root_has_four_specialist_sub_agents(self):
        names = {sa.name for sa in root_agent.sub_agents}
        self.assertEqual(
            names, {"weather_agent", "search_agent", "route_agent", "answer_team"}
        )

    def test_answer_team_is_sequential_research_critique_refine(self):
        self.assertIsInstance(answer_team, SequentialAgent)
        order = [sa.name for sa in answer_team.sub_agents]
        self.assertEqual(order, ["research_agent", "critique_agent", "refine_agent"])

    def test_weather_agent_tools_and_us_validation(self):
        names = _tool_names(weather_agent)
        self.assertIn("geocode_place", names)
        self.assertIn("get_weather", names)
        self.assertIn(validate_us_location, _as_list(weather_agent.before_model_callback))

    def test_route_agent_has_directions_tool(self):
        self.assertIn("get_directions", _tool_names(route_agent))

    def test_search_and_research_use_only_google_search(self):
        for agent in (search_agent, research_agent):
            self.assertEqual(len(agent.tools), 1)
            self.assertTrue(
                any("search" in n.lower() for n in _tool_names(agent)),
                msg=f"{agent.name}: expected a search tool, got {_tool_names(agent)}",
            )

    def test_output_keys_chain_the_workflow(self):
        self.assertEqual(research_agent.output_key, "draft_answer")
        self.assertEqual(critique_agent.output_key, "critique")
        self.assertEqual(refine_agent.output_key, "final_answer")

    def test_root_logging_and_validation_callbacks(self):
        before = _as_list(root_agent.before_model_callback)
        after = _as_list(root_agent.after_model_callback)
        self.assertIn(log_user_prompt, before)
        self.assertIn(screen_input_safety, before)
        self.assertIn(log_model_response, after)


if __name__ == "__main__":
    unittest.main()
