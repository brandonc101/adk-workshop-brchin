"""Unit tests for event_utils (Agent Engine event parsing).

Pure-logic tests with no cloud dependencies - they exercise the helpers that
test_deployment.py uses to read text from streamed events, for both dict-shaped
and object-shaped events.

Run with:

    python -m unittest discover -s tests
"""

import types
import unittest

try:
    from event_utils import extract_texts, get_field
except Exception:  # pragma: no cover - depends on how tests are launched
    import importlib.util
    import pathlib

    _path = pathlib.Path(__file__).resolve().parent.parent / "event_utils.py"
    _spec = importlib.util.spec_from_file_location("event_utils", _path)
    _mod = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)
    extract_texts, get_field = _mod.extract_texts, _mod.get_field


def _obj(**kwargs):
    """Build a simple attribute object (stand-in for an event/part/content)."""
    return types.SimpleNamespace(**kwargs)


class GetFieldTests(unittest.TestCase):
    def test_reads_from_dict(self):
        self.assertEqual(get_field({"a": 1}, "a"), 1)

    def test_reads_from_object(self):
        self.assertEqual(get_field(_obj(a=2), "a"), 2)

    def test_missing_dict_key_is_none(self):
        self.assertIsNone(get_field({}, "a"))

    def test_missing_attr_is_none(self):
        self.assertIsNone(get_field(_obj(), "a"))

    def test_none_object_is_none(self):
        self.assertIsNone(get_field(None, "a"))


class ExtractTextsTests(unittest.TestCase):
    def test_dict_event_text(self):
        event = {"content": {"parts": [{"text": "hello"}]}}
        self.assertEqual(extract_texts(event), ["hello"])

    def test_object_event_text(self):
        event = _obj(content=_obj(parts=[_obj(text="hi there")]))
        self.assertEqual(extract_texts(event), ["hi there"])

    def test_multiple_parts_in_order(self):
        event = {"content": {"parts": [{"text": "a"}, {"text": "b"}]}}
        self.assertEqual(extract_texts(event), ["a", "b"])

    def test_no_content_returns_empty(self):
        self.assertEqual(extract_texts({}), [])
        self.assertEqual(extract_texts({"content": None}), [])

    def test_non_text_parts_ignored(self):
        # e.g. a function_call part with no text.
        event = {"content": {"parts": [{"function_call": {"name": "x"}}, {"text": "kept"}]}}
        self.assertEqual(extract_texts(event), ["kept"])

    def test_whitespace_text_ignored(self):
        event = {"content": {"parts": [{"text": "   "}, {"text": "real"}]}}
        self.assertEqual(extract_texts(event), ["real"])


if __name__ == "__main__":
    unittest.main()
