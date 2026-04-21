# MIDI Piano Teacher

Real-time MIDI note and chord display app for macOS, written in Python.

## Files
- `midi_display.py` — terminal app (original); MIDI logic shared by GUI
- `main.py` — desktop app entry point
- `main_window.py` — `MainWindow(QMainWindow)` shell; owns `QStackedWidget` navigation and window sizing
- `home_page.py` — `HomePage(QWidget)` landing screen with title and navigation button
- `midi_display_page.py` — `MidiDisplayPage(QWidget)` live MIDI note/chord display; owns MIDI thread lifecycle
- `requirements.txt` — `mido>=1.3.0`, `python-rtmidi>=1.5.0`, `PyQt6>=6.0.0`

## Key functions in `midi_display.py`
- `midi_to_note(midi_num)` → `(name, octave)` — converts MIDI number to note name/octave
- `identify_chord(midi_notes)` → `str | None` — chord detection from a list of MIDI numbers; tries all inversions, falls back to subset matching
- `NOTE_NAMES` — 12-element list of note name strings
- `CHORD_PATTERNS` — dict mapping semitone interval tuples to chord name suffixes (18 chord types)

## Architecture
- Single `QMainWindow` shell with `QStackedWidget` for multi-screen navigation
- MIDI thread starts on demand when user navigates to the MIDI display page (`MidiDisplayPage.activate()`); stops on back navigation (`deactivate()`)
- `active_notes: set` tracks currently held MIDI note numbers; protected by `threading.Lock`
- GUI polls state every 50ms via `QTimer` on the main thread
- Navigation is signal-driven: pages emit `pyqtSignal` → `MainWindow` handles routing and window resizing
- Device: auto-selects first available MIDI input port

## Styling conventions
- On macOS, PyQt6 does not automatically inherit the parent's `background-color` stylesheet. Any child `QWidget` or `QLabel` inside a dark-background parent must explicitly set `background-color: transparent;` in its own stylesheet, otherwise it renders with the system default (visibly lighter or darker).
- All new widgets added to a dark-background container should follow this pattern:
  ```python
  widget.setStyleSheet("color: #ffffff; background-color: transparent;")
  ```

## Dependencies
```
pip install mido python-rtmidi PyQt6
```

## Run
```
python main.py               # desktop app
python midi_display.py       # terminal app
```
