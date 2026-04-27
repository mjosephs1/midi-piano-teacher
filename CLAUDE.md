# MIDI Piano Teacher

Real-time MIDI note and chord display app for macOS, written in Python.

## Files
- `midi_display.py` — terminal app (original); MIDI logic shared by GUI
- `main.py` — desktop app entry point
- `main_window.py` — `MainWindow(QMainWindow)` shell; owns `QStackedWidget` navigation and window sizing
- `home_page.py` — `HomePage(QWidget)` landing screen with title and navigation buttons
- `midi_display_page.py` — `MidiDisplayPage(QWidget)` live MIDI note/chord display; owns MIDI thread lifecycle
- `find_chord_page.py` — `FindChordPage(QWidget)` Infinite mode: interactive chord practice; sliding window of random chord targets
- `find_chord_mode_page.py` — `FindChordModePage(QWidget)` mode selection screen for Find the Chord (routes to Infinite or Timed mode)
- `find_chord_timed_page.py` — `FindChordTimedPage(QWidget)` Timed mode: 60-second chord challenge with score counter
- `requirements.txt` — `mido>=1.3.0`, `python-rtmidi>=1.5.0`, `PyQt6>=6.0.0`

## Key functions in `midi_display.py`
- `midi_to_note(midi_num)` → `(name, octave)` — converts MIDI number to note name/octave
- `identify_chord(midi_notes)` → `str | None` — chord detection from a list of MIDI numbers; tries all inversions, falls back to subset matching
- `NOTE_NAMES` — 12-element list of note name strings
- `CHORD_PATTERNS` — dict mapping semitone interval tuples to chord name suffixes (18 chord types)

## Architecture
- Single `QMainWindow` shell with `QStackedWidget` for multi-screen navigation (5 pages: Home, MIDI Display, Find Chord Mode, Find Chord Infinite, Find Chord Timed)
- MIDI thread starts on demand when user navigates to a MIDI page (`activate()`); stops on back navigation (`deactivate()`)
- `_go_to_home()` in `MainWindow` defensively calls `deactivate()` on all MIDI pages (`_midi_display`, `_find_chord`, `_find_chord_timed`)
- `active_notes: set` tracks currently held MIDI note numbers; protected by `threading.Lock`
- GUI polls state every 50ms via `QTimer` on the main thread
- Navigation is signal-driven: pages emit `pyqtSignal` → `MainWindow` handles routing and window resizing
- Device: auto-selects first available MIDI input port
- Window sizes: home=(420, 340), midi_display=(420, 220), find_chord_mode=(620, 450), find_chord=(620, 440), find_chord_timed=(620, 440)

## Find the Chord Mode page (`find_chord_mode_page.py`)
- Route selection screen: two buttons for Infinite and Timed modes
- Owns all chord settings shared by both gameplay modes:
  - `_group_enabled: dict[str, bool]` — which chord groups are active (all enabled by default)
  - `_sharps_enabled: bool` — whether sharps are enabled (true by default)
  - Two rows of toggle buttons (5 per row) for chord group filtering + "Sharps" toggle button
  - `_on_group_toggled(name, checked)`, `_on_sharps_toggled(checked)` — handle toggle updates
- Exposes read-only properties: `group_enabled` (dict copy), `sharps_enabled` (bool)
- Settings are passed to both `FindChordPage` and `FindChordTimedPage` at `activate()` time
- Window size: 620×450

## Find the Chord page (`find_chord_page.py`) — Infinite mode
- Maintains a `list` queue of random chord name strings (e.g. `"Cmaj"`, `"F#min7"`); always keeps 10 pre-generated
- Displays the first 5 chords in a row; leftmost is the current target (larger font, white); others are dimmer/smaller
- On correct chord match: target label turns green (`#44ff44`) for 500ms, then queue shifts left via `_advance()`
- `_advancing: bool` flag blocks re-triggering during the green flash
- `_group_enabled: dict[str, bool]`, `_sharps_enabled: bool` — set by `activate()` from FindChordModePage
- `_available_roots()` — returns filtered list of root notes based on `_sharps_enabled`
- `_random_chord()` picks a random root and suffix, respecting enabled groups and sharps setting
- `activate(group_enabled: dict, sharps_enabled: bool)` — stores settings and starts MIDI playback
- "Playing" label shows the currently detected chord so the user knows what they're playing if wrong
- Emits `nav_to_mode_select` on back button

## Find the Chord Timed page (`find_chord_timed_page.py`) — Timed mode
- 60-second countdown challenge; goal is to identify as many chords as possible before time expires
- `_waiting_to_start: bool` — when true, chord queue is hidden and Start button is shown; MIDI polling active for warm-up
- `_start_btn` — amber button that starts the game (hides on click, countdown begins)
- `_chord_area` — `QWidget` container wrapping chord row + arrow row; hidden during start screen, shown after Start is pressed
- `_score: int` — incremented on each correct chord; displayed in top-right
- `_time_remaining: int` — counts down from 60 to 0; label turns red (`#ff4444`) at ≤10 seconds
- `_game_over: bool` — set to `True` when timer reaches 0; blocks `_poll()` and `_advance()` from further scoring
- Two timers: `_poll_timer` (50ms, runs always) and `_countdown_timer` (1000ms, starts on Start or Play Again)
- `_group_enabled`, `_sharps_enabled` — set by `activate()` from FindChordModePage
- `_start_game()` — called on Start button click; shows chord queue, starts countdown
- `_tick()` — decrements `_time_remaining`; calls `_end_game()` at 0
- `_end_game()` — stops timers, shows results overlay with final score
- `_restart()` — called from "Play Again" button; skips start screen, goes straight to gameplay
- `activate(group_enabled, sharps_enabled, show_start=True)` — if show_start=True, enter start screen; if False, start immediately
- `_poll()` — guarded by `if self._waiting_to_start or self._game_over: return` to prevent scoring before Start
- Emits `nav_to_mode_select` on back button or "Back to Menu"

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
