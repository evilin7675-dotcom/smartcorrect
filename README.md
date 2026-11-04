# SmartCorrect

System-wide autocorrect for Windows. It fixes common typos as you type in any app, using a global keyboard hook, a SQLite rule store and 97 built-in rules.

> Status: rewritten in November 2026. Correction logic is unit-tested; the full app still needs testing on Windows.

## Features

- Fixes typos when you finish a word and keeps your capitalisation (`teh` → `the`, `Teh` → `The`, `TEH` → `THE`).
- Phrase expansion: type a trigger such as `;ty` and a space to get "Thank you".
- Capitalises the first word of each sentence and a lone "i".
- **Ctrl+Alt+Z** undoes the last correction; **Ctrl+Alt+P** pauses and resumes.
- Settings window with Rules, Expansions, Settings and Log tabs.
- The log records only corrections (the typo and its fix), never your other keystrokes.
- Never corrects across Enter, so it won't change a chat message after you send it.

## Run

```bat
pip install -r requirements.txt
python -m smartcorrect
```

Data lives in `%APPDATA%\SmartCorrect\smartcorrect.db`.

## Build an installer

Run `build_windows.bat` to make `dist\SmartCorrect\SmartCorrect.exe` with PyInstaller, then compile `installer\smartcorrect.iss` with Inno Setup.

## Code layout

| File | What it does |
| --- | --- |
| `smartcorrect/engine.py` | Correction logic, no keyboard or UI code |
| `smartcorrect/hook.py` | Global keyboard hook (pynput) and a worker thread that types corrections |
| `smartcorrect/storage.py` | SQLite rules, expansions, settings and audit log |
| `smartcorrect/rules.py` | The 97 built-in rules |
| `smartcorrect/ui.py` | Settings window (tkinter) |
| `tests/` | Unit tests: `python -m unittest discover -s tests -t .` |
