import tempfile
import unittest
from pathlib import Path

from smartcorrect.engine import CorrectionEngine, match_case
from smartcorrect.rules import BUILTIN_RULES
from smartcorrect.storage import Store


def type_text(engine, text):
    """Simulate typing and return the final text, applying every Action."""
    out = ""
    for ch in text:
        out += ch
        action = engine.feed(ch)
        if action:
            out = out[: len(out) - action.backspaces] + action.text
    return out


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.engine = CorrectionEngine(dict(BUILTIN_RULES), {";ty": "Thank you"})

    def test_rule_and_capitalisation(self):
        self.assertEqual(type_text(self.engine, "teh cat sat. it was adn happy "),
                         "The cat sat. It was and happy ")

    def test_case_is_kept(self):
        self.assertEqual(match_case("TEH", "the"), "THE")
        self.assertEqual(match_case("Teh", "the"), "The")

    def test_lone_i_and_abbreviation(self):
        self.engine.sentence_start = False
        self.assertEqual(type_text(self.engine, "i use e.g. tools "), "I use e.g. tools ")

    def test_expansion(self):
        self.engine.sentence_start = False
        self.assertEqual(type_text(self.engine, ";ty "), "Thank you ")

    def test_undo(self):
        out = type_text(self.engine, "teh ")
        undo = self.engine.undo()
        out = out[: len(out) - undo.backspaces] + undo.text
        self.assertEqual(out, "teh ")
        self.assertIsNone(self.engine.undo())

    def test_backspace_edits_word(self):
        self.engine.sentence_start = False
        for ch in "tehh":
            self.engine.feed(ch)
        self.engine.backspace()
        self.assertEqual(self.engine.feed(" ").text, "the ")


class StoreTests(unittest.TestCase):
    def test_seeds_97_rules_and_logs(self):
        with tempfile.TemporaryDirectory() as d:
            store = Store(Path(d) / "t.db")
            self.assertEqual(len(store.rules()), 97)
            store.log("rule", "teh", "the")
            self.assertEqual(store.recent()[0][1:], ("rule", "teh", "the"))


if __name__ == "__main__":
    unittest.main()
