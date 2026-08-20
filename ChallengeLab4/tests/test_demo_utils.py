"""Unit tests for demo_utils.select_cities (the CLI city-selection logic).

These are pure-logic tests with no ADK, network, or API-key dependencies.

Run with:

    python -m unittest discover -s tests
"""

import unittest

# Prefer the normal import; fall back to loading the file directly so the test
# runs even when the package/entry-point layout differs.
try:  # pragma: no cover - depends on how tests are launched
    from demo_utils import select_cities
except Exception:  # pragma: no cover
    import importlib.util
    import pathlib

    _path = pathlib.Path(__file__).resolve().parent.parent / "demo_utils.py"
    _spec = importlib.util.spec_from_file_location("demo_utils", _path)
    _mod = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)
    select_cities = _mod.select_cities


DEFAULT = ["New York, NY", "Chicago, IL", "Denver, CO"]


class SelectCitiesTests(unittest.TestCase):
    def test_no_args_uses_default(self):
        self.assertEqual(select_cities([], DEFAULT), DEFAULT)

    def test_single_arg(self):
        self.assertEqual(select_cities(["Austin, TX"], DEFAULT), ["Austin, TX"])

    def test_multiple_args_preserve_order(self):
        args = ["Austin, TX", "Boston, MA"]
        self.assertEqual(select_cities(args, DEFAULT), ["Austin, TX", "Boston, MA"])

    def test_always_returns_a_list(self):
        self.assertIsInstance(select_cities(["X"], DEFAULT), list)
        self.assertIsInstance(select_cities([], DEFAULT), list)

    def test_default_is_copied_not_aliased(self):
        default = ["A", "B"]
        result = select_cities([], default)
        result.append("C")
        # Mutating the result must not affect the caller's default list.
        self.assertEqual(default, ["A", "B"])

    def test_args_are_copied_not_aliased(self):
        args = ["A"]
        result = select_cities(args, DEFAULT)
        result.append("B")
        # Mutating the result must not affect the caller's args list.
        self.assertEqual(args, ["A"])


if __name__ == "__main__":
    unittest.main()
