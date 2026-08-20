"""Structure tests for the multi-agent system.

These assert that the root/weather/search agents are wired together correctly
(sub-agents, tools, transfer flags, and callbacks). They import the ADK, so
they run in an environment where ``google-adk`` is installed (e.g. Cloud Shell)
and are automatically skipped where it is not.

Run with:

    python -m unittest discover -s tests
"""

import unittest

try:  # ADK is required for these tests; skip cleanly if it isn't installed.
    from multi_agent.agent import root_agent, search_agent, weather_agent
    from multi_agent.callbacks import (
        log_model_response,
        log_user_prompt,
        screen_input_safety,
        validate_us_location,
    )

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
class MultiAgentStructureTests(unittest.TestCase):
    def test_root_has_two_named_sub_agents(self):
        names = {sa.name for sa in root_agent.sub_agents}
        self.assertEqual(names, {"weather_agent", "search_agent"})

    def test_root_references_the_sub_agent_objects(self):
        self.assertIn(weather_agent, root_agent.sub_agents)
        self.assertIn(search_agent, root_agent.sub_agents)

    def test_weather_agent_has_both_tools(self):
        names = _tool_names(weather_agent)
        self.assertIn("geocode_place", names)
        self.assertIn("get_weather", names)

    def test_search_agent_has_only_google_search(self):
        # Gemini requires google_search to be the sole tool on the agent.
        self.assertEqual(len(search_agent.tools), 1)
        self.assertTrue(
            any("search" in n.lower() for n in _tool_names(search_agent)),
            msg=f"expected a search tool, got {_tool_names(search_agent)}",
        )

    def test_search_agent_transfers_are_disabled(self):
        # Keeps google_search alone (no auto-added transfer tool).
        self.assertTrue(search_agent.disallow_transfer_to_parent)
        self.assertTrue(search_agent.disallow_transfer_to_peers)

    def test_root_callbacks_are_wired(self):
        before = _as_list(root_agent.before_model_callback)
        after = _as_list(root_agent.after_model_callback)
        self.assertIn(log_user_prompt, before)
        self.assertIn(screen_input_safety, before)
        self.assertIn(log_model_response, after)

    def test_weather_agent_validates_us_location(self):
        before = _as_list(weather_agent.before_model_callback)
        self.assertIn(validate_us_location, before)


if __name__ == "__main__":
    unittest.main()
