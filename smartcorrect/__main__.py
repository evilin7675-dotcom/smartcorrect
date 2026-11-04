"""Start SmartCorrect: `python -m smartcorrect`."""

import sys
import time

from .engine import CorrectionEngine
from .hook import KeyboardHook
from .storage import Store


def main():
    store = Store()
    engine = CorrectionEngine(
        store.rules(),
        store.expansions(),
        store.get_setting("auto_capitalise", "1") == "1",
    )

    def reload():
        engine.rules = {k.lower(): v for k, v in store.rules().items()}
        engine.expansions = store.expansions()
        engine.auto_capitalise = store.get_setting("auto_capitalise", "1") == "1"

    hook = KeyboardHook(engine, on_action=lambda a: store.log(a.kind, a.before, a.after))
    hook.start()

    try:
        from .ui import SettingsWindow
    except ImportError:
        print("tkinter is not available; running without the settings window. Ctrl+C to quit.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
    else:
        SettingsWindow(store, reload, hook).run()
    hook.stop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
