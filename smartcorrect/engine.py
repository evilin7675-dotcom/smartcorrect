"""Correction logic, kept free of keyboard and UI code so it can be unit-tested.

The keyboard hook feeds every typed character into `CorrectionEngine.feed`.
When a word ends (space or punctuation), the engine may return an `Action`:
erase `backspaces` characters, then type `text`. The boundary character has
already reached the app when the hook sees it, so it is erased and retyped.
"""

from dataclasses import dataclass

SENTENCE_END = ".!?"
BOUNDARY = " .,;:!?)\"'"  # characters that finish a word
ABBREVIATIONS = {"e", "g", "i", "etc", "vs", "dr", "mr", "mrs", "ms", "no", "fig"}


@dataclass
class Action:
    backspaces: int
    text: str
    kind: str      # "rule", "expansion", "capital" or "undo"
    before: str
    after: str


def match_case(source: str, fix: str) -> str:
    """Give `fix` the capitalisation pattern of `source`."""
    if len(source) > 1 and source.isupper():
        return fix.upper()
    if source[:1].isupper():
        return fix[:1].upper() + fix[1:]
    return fix


class CorrectionEngine:
    def __init__(self, rules=None, expansions=None, auto_capitalise=True):
        self.rules = {k.lower(): v for k, v in (rules or {}).items()}
        self.expansions = dict(expansions or {})
        self.auto_capitalise = auto_capitalise
        self.word = ""
        self.sentence_start = True
        self.last = None  # the most recent Action, kept for undo

    # ---- input from the hook --------------------------------------------------
    def feed(self, ch: str):
        """Handle one typed character. Returns an Action or None."""
        starts_trigger = ch == ";" and not self.word   # expansions look like ";ty"
        if starts_trigger or (ch not in BOUNDARY and not ch.isspace()):
            self.word += ch
            self.last = None
            return None
        word, self.word = self.word, ""
        action = self._finish_word(word, ch)
        self._update_sentence_state(word, ch)
        self.last = action
        return action

    def backspace(self):
        self.word = self.word[:-1]
        self.last = None

    def new_line(self):
        """Enter/Tab: never correct across them (Enter may send a message)."""
        self.word = ""
        self.last = None
        self.sentence_start = True

    def reset(self):
        """Cursor moved (mouse click, arrow keys): forget the current word."""
        self.word = ""
        self.last = None

    def undo(self):
        """Reverse the last correction if nothing was typed after it."""
        if self.last is None or self.last.kind == "undo":
            return None
        a = self.last
        boundary = a.text[-1]
        self.last = None
        return Action(len(a.text), a.before + boundary, "undo", a.after, a.before)

    # ---- internals ------------------------------------------------------------
    def _finish_word(self, word: str, boundary: str):
        if not word:
            return None
        if word in self.expansions:
            return self._replace(word, self.expansions[word], boundary, "expansion")

        fixed, kind = word, None
        rule = self.rules.get(word.lower())
        if rule is not None:
            fixed, kind = match_case(word, rule), "rule"
        if word == "i":
            fixed, kind = "I", "rule"
        if self.auto_capitalise and self.sentence_start and fixed[:1].islower():
            fixed = fixed[:1].upper() + fixed[1:]
            kind = kind or "capital"

        if fixed == word:
            return None
        return self._replace(word, fixed, boundary, kind)

    @staticmethod
    def _replace(word, new, boundary, kind):
        return Action(len(word) + 1, new + boundary, kind, word, new)

    def _update_sentence_state(self, word: str, boundary: str):
        if boundary in SENTENCE_END:
            self.sentence_start = word.lower() not in ABBREVIATIONS
        elif word:
            self.sentence_start = False
