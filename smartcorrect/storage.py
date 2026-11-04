"""SQLite store for rules, phrase expansions, settings and the audit log.

Privacy: only corrections are logged (the typo and its fix). Ordinary
keystrokes are never written to disk.
"""

import os
import sqlite3
import threading
from datetime import datetime
from pathlib import Path

from .rules import BUILTIN_RULES

DEFAULT_EXPANSIONS = {
    ";brb": "be right back",
    ";ty": "Thank you",
    ";sig": "Regards,\nRajinish S G",
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS rules (
    typo TEXT PRIMARY KEY,
    fix TEXT NOT NULL,
    builtin INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS expansions (
    trigger TEXT PRIMARY KEY,
    text TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS audit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    kind TEXT NOT NULL,
    before TEXT NOT NULL,
    after TEXT NOT NULL
);
"""


def default_db_path() -> Path:
    base = os.environ.get("APPDATA") or Path.home() / ".config"
    folder = Path(base) / "SmartCorrect"
    folder.mkdir(parents=True, exist_ok=True)
    return folder / "smartcorrect.db"


class Store:
    def __init__(self, path=None):
        self.path = Path(path) if path else default_db_path()
        self._lock = threading.Lock()
        self._db = sqlite3.connect(self.path, check_same_thread=False)
        self._db.executescript(SCHEMA)
        self._seed()

    def _seed(self):
        with self._lock, self._db:
            self._db.executemany(
                "INSERT OR IGNORE INTO rules (typo, fix, builtin) VALUES (?, ?, 1)",
                BUILTIN_RULES,
            )
            if not self._db.execute("SELECT 1 FROM expansions LIMIT 1").fetchone():
                self._db.executemany(
                    "INSERT INTO expansions (trigger, text) VALUES (?, ?)",
                    DEFAULT_EXPANSIONS.items(),
                )

    # ---- rules and expansions -----------------------------------------------
    def rules(self) -> dict:
        with self._lock:
            return dict(self._db.execute("SELECT typo, fix FROM rules ORDER BY typo"))

    def set_rule(self, typo: str, fix: str):
        with self._lock, self._db:
            self._db.execute(
                "INSERT INTO rules (typo, fix) VALUES (?, ?) "
                "ON CONFLICT(typo) DO UPDATE SET fix = excluded.fix",
                (typo.strip().lower(), fix.strip()),
            )

    def delete_rule(self, typo: str):
        with self._lock, self._db:
            self._db.execute("DELETE FROM rules WHERE typo = ?", (typo,))

    def expansions(self) -> dict:
        with self._lock:
            return dict(self._db.execute("SELECT trigger, text FROM expansions ORDER BY trigger"))

    def set_expansion(self, trigger: str, text: str):
        with self._lock, self._db:
            self._db.execute(
                "INSERT INTO expansions (trigger, text) VALUES (?, ?) "
                "ON CONFLICT(trigger) DO UPDATE SET text = excluded.text",
                (trigger.strip(), text),
            )

    def delete_expansion(self, trigger: str):
        with self._lock, self._db:
            self._db.execute("DELETE FROM expansions WHERE trigger = ?", (trigger,))

    # ---- settings ---------------------------------------------------------------
    def get_setting(self, key: str, default: str) -> str:
        with self._lock:
            row = self._db.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return row[0] if row else default

    def set_setting(self, key: str, value: str):
        with self._lock, self._db:
            self._db.execute(
                "INSERT INTO settings (key, value) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, value),
            )

    # ---- audit log ---------------------------------------------------------------
    def log(self, kind: str, before: str, after: str):
        with self._lock, self._db:
            self._db.execute(
                "INSERT INTO audit (ts, kind, before, after) VALUES (?, ?, ?, ?)",
                (datetime.now().isoformat(timespec="seconds"), kind, before, after),
            )

    def recent(self, limit: int = 200):
        with self._lock:
            return self._db.execute(
                "SELECT ts, kind, before, after FROM audit ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
