"""System-wide keyboard hook using pynput.

The listener only records keys and queues actions; a worker thread does the
typing, because injecting keys from inside the listener callback can stall
the hook on Windows. Keys that arrive while the worker is typing are our own
and are ignored.

Hotkeys: Ctrl+Alt+Z undoes the last correction, Ctrl+Alt+P pauses/resumes.
"""

import queue
import threading
import time

from pynput import keyboard

from .engine import CorrectionEngine

CTRL_KEYS = {keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r}
ALT_KEYS = {keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r, keyboard.Key.alt_gr}
RESET_KEYS = {
    keyboard.Key.left, keyboard.Key.right, keyboard.Key.up, keyboard.Key.down,
    keyboard.Key.home, keyboard.Key.end, keyboard.Key.page_up, keyboard.Key.page_down,
    keyboard.Key.delete, keyboard.Key.esc,
}
VK_Z, VK_P = 0x5A, 0x50


class KeyboardHook:
    def __init__(self, engine: CorrectionEngine, on_action=None):
        self.engine = engine
        self.on_action = on_action          # called with each Action (for logging)
        self.enabled = True
        self._typing = threading.Event()
        self._queue = queue.Queue()
        self._ctrl = False
        self._alt = False
        self._out = keyboard.Controller()
        self._listener = keyboard.Listener(on_press=self._press, on_release=self._release)
        self._worker = threading.Thread(target=self._run_worker, daemon=True)

    def start(self):
        self._worker.start()
        self._listener.start()

    def stop(self):
        self._listener.stop()
        self._queue.put(None)

    # ---- listener callbacks ----------------------------------------------------
    def _press(self, key):
        if self._typing.is_set():
            return
        if key in CTRL_KEYS:
            self._ctrl = True
            return
        if key in ALT_KEYS:
            self._alt = True
            return

        if self._ctrl and self._alt:
            self._hotkey(key)
            return
        if self._ctrl or self._alt or not self.enabled:
            self.engine.reset()          # shortcuts such as Ctrl+V move text around
            return

        if key == keyboard.Key.space:
            self._queue_action(self.engine.feed(" "))
        elif key == keyboard.Key.backspace:
            self.engine.backspace()
        elif key in (keyboard.Key.enter, keyboard.Key.tab):
            self.engine.new_line()
        elif key in RESET_KEYS:
            self.engine.reset()
        elif getattr(key, "char", None):
            self._queue_action(self.engine.feed(key.char))

    def _release(self, key):
        if key in CTRL_KEYS:
            self._ctrl = False
        elif key in ALT_KEYS:
            self._alt = False

    def _hotkey(self, key):
        vk = getattr(key, "vk", None)
        char = (getattr(key, "char", None) or "").lower()
        if vk == VK_Z or char in ("z", "\x1a"):
            self._queue_action(self.engine.undo())
        elif vk == VK_P or char in ("p", "\x10"):
            self.enabled = not self.enabled
            self.engine.reset()

    def _queue_action(self, action):
        if action is not None:
            self._queue.put(action)

    # ---- worker -----------------------------------------------------------------
    def _run_worker(self):
        while True:
            action = self._queue.get()
            if action is None:
                return
            self._typing.set()
            try:
                time.sleep(0.02)   # let modifier keys settle
                for _ in range(action.backspaces):
                    self._out.press(keyboard.Key.backspace)
                    self._out.release(keyboard.Key.backspace)
                self._out.type(action.text)
                time.sleep(0.02)
            finally:
                self._typing.clear()
            if self.on_action:
                self.on_action(action)
