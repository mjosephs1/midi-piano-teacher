# MIDI Piano Teacher

Real-time MIDI note and chord display app for macOS, written in Python.

## Files
- `midi_display.py` — terminal app (original); MIDI logic shared by GUI
- `main.py` — desktop app entry point
- `main_window.py` — `MainWindow(QMainWindow)` shell; owns `QStackedWidget` navigation and window sizing
- `home_page.py` — `HomePage(QWidget)` landing screen with title and navigation buttons
- `midi_display_page.py` — `MidiDisplayPage(QWidget)` live MIDI note/chord display; owns MIDI thread lifecycle
- `find_chord_page.py` — `FindChordPage(QWidget)` interactive chord practice; sliding window of random chord targets
- `requirements.txt` — `mido>=1.3.0`, `python-rtmidi>=1.5.0`, `PyQt6>=6.0.0`

## Key functions in `midi_display.py`
- `midi_to_note(midi_num)` → `(name, octave)` — converts MIDI number to note name/octave
- `identify_chord(midi_notes)` → `str | None` — chord detection from a list of MIDI numbers; tries all inversions, falls back to subset matching
- `NOTE_NAMES` — 12-element list of note name strings
- `CHORD_PATTERNS` — dict mapping semitone interval tuples to chord name suffixes (18 chord types)

## Architecture
- Single `QMainWindow` shell with `QStackedWidget` for multi-screen navigation
- MIDI thread starts on demand when user navigates to a MIDI page (`activate()`); stops on back navigation (`deactivate()`)
- `_go_to_home()` in `MainWindow` defensively calls `deactivate()` on all pages
- `active_notes: set` tracks currently held MIDI note numbers; protected by `threading.Lock`
- GUI polls state every 50ms via `QTimer` on the main thread
- Navigation is signal-driven: pages emit `pyqtSignal` → `MainWindow` handles routing and window resizing
- Device: auto-selects first available MIDI input port

## Find the Chord page (`find_chord_page.py`)
- Maintains a `list` queue of random chord name strings (e.g. `"Cmaj"`, `"F#min7"`); always keeps 10 pre-generated
- Displays the first 5 chords in a row; leftmost is the current target (larger font, white); others are dimmer/smaller
- On correct chord match: target label turns green (`#44ff44`) for 500ms, then queue shifts left via `_advance()`
- `_advancing: bool` flag blocks re-triggering during the green flash
- `CHORD_GROUPS` — module-level dict mapping 10 group names (e.g. "Major", "Minor", "Dom 7th") to lists of chord suffixes
- `_group_enabled: dict[str, bool]` — tracks which chord groups are active; all enabled by default
- `_sharps_enabled: bool` — controls whether sharp root notes (C#, D#, F#, G#, A#) can appear; enabled by default
- `_available_roots()` — returns filtered list of root notes based on `_sharps_enabled`
- `_random_chord()` picks a random root from `_available_roots()` and a random suffix from enabled `CHORD_GROUPS` entries
- `_on_group_toggled(name, checked)` — handles toggling chord groups on/off; enforces at least 1 group stays enabled, regenerates the queue if page is active
- `_on_sharps_toggled(checked)` — handles toggling sharps on/off, regenerates the queue if page is active
- Two rows of toggle buttons (5 per row) for chord group filtering, plus a "Sharps" toggle button
- "Playing" label below shows the currently detected chord so the user knows what they're playing if wrong

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

## When Implementing Changes
- When adding new features or files, update the relevant section of CLAUDE.md to document the change
- When removing or renaming files, update the Files section and any related documentation
- When modifying page logic or MIDI handling, update the corresponding section (Architecture, Find the Chord page, etc.)
- Before marking implementation tasks complete, verify that CLAUDE.md reflects all new code paths, methods, and state structures
