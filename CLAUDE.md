# MIDI Piano Teacher

Real-time MIDI note and chord display app for macOS, written in Python.

## Files
- `midi_display.py` — terminal app (original); MIDI logic shared by GUI
- `main.py` — desktop app entry point
- `main_window.py` — `MainWindow(QMainWindow)` shell; owns `QStackedWidget` navigation and window sizing
- `home_page.py` — `HomePage(QWidget)` landing screen with title and navigation buttons
- `midi_display_page.py` — `MidiDisplayPage(QWidget)` live MIDI note/chord display; owns MIDI thread lifecycle
- `find_chord_page.py` — `FindChordPage(QWidget)` Infinite mode: interactive chord practice; sliding window of random chord targets
- `find_chord_mode_page.py` — `FindChordModePage(QWidget)` mode selection screen for Find the Chord (routes to Infinite or Timed mode); delegates chord settings to `ChordSettingsWidget`
- `find_chord_timed_page.py` — `FindChordTimedPage(QWidget)` Timed mode: 60-second chord challenge with score counter; records scores to disk
- `chord_settings_widget.py` — `ChordSettingsWidget(QWidget)` reusable toggle panel for chord groups + sharps; emits `settings_changed` signal on toggle; loads/saves selections via `settings_manager`
- `high_scores_page.py` — `HighScoresPage(QWidget)` displays top-10 scores per chord group/sharps combination with timestamps and accuracy %
- `score_manager.py` — score persistence module: loads/saves JSON, manages top-10 per settings key, records new scores with timestamps and errors
- `settings_manager.py` — chord settings persistence: loads/saves selected chord groups and sharps to `chord_settings.json` on startup and after each toggle
- `stats_manager.py` — chord transition stats: tracks per-transition time and error averages in `stats.json` for timed mode
- `requirements.txt` — `mido>=1.3.0`, `python-rtmidi>=1.5.0`, `PyQt6>=6.0.0`

## Key functions in `midi_display.py`
- `midi_to_note(midi_num)` → `(name, octave)` — converts MIDI number to note name/octave
- `identify_chord(midi_notes)` → `str | None` — chord detection from a list of MIDI numbers; tries all inversions, falls back to subset matching
- `count_chord_instances(active_notes: set, target_chord: str) → int` — counts how many independent instances of the target chord appear in the active notes using pitch-class counting; returns 0 if target not found or not enough notes
- `NOTE_NAMES` — 12-element list of note name strings
- `CHORD_PATTERNS` — dict mapping semitone interval tuples to chord name suffixes (18 chord types)

## Architecture
- Single `QMainWindow` shell with `QStackedWidget` for multi-screen navigation (6 pages: Home, MIDI Display, Find Chord Mode, Find Chord Infinite, Find Chord Timed, High Scores)
- MIDI thread starts on demand when user navigates to a MIDI page (`activate()`); stops on back navigation (`deactivate()`)
- `_go_to_home()` in `MainWindow` defensively calls `deactivate()` on all MIDI pages (`_midi_display`, `_find_chord`, `_find_chord_timed`)
- `active_notes: set` tracks currently held MIDI note numbers; protected by `threading.Lock`
- GUI polls state every 50ms via `QTimer` on the main thread
- Navigation is signal-driven: pages emit `pyqtSignal` → `MainWindow` handles routing and window resizing
- Device: auto-selects first available MIDI input port
- Window sizes: home=(420, 390), midi_display=(420, 220), find_chord_mode=(620, 450), find_chord=(620, 440), find_chord_timed=(620, 440), high_scores=(620, 560)
- Score history is stored in `score_history.json` (git-ignored), keyed by settings combinations. When both left and right hands are enabled, the key includes `|hands=both`; when only left or right is enabled, the key includes `|hands=left` or `|hands=right`. Full history per key; top 10 returned for display

## Chord Settings Widget (`chord_settings_widget.py`)
- Reusable toggle UI for chord groups + sharps mode + hands selection; used by `FindChordModePage` and `HighScoresPage`
- On init: loads saved settings from `chord_settings.json` via `settings_manager.load_chord_settings()`; falls back to all-enabled defaults if file missing/corrupt
- On `showEvent`: reloads settings from disk (via `_reload_settings_from_disk()`) to stay in sync across multiple widget instances; button states updated without triggering signals
- Owns `_group_enabled: dict[str, bool]`, `_sharps_mode: str` (one of `"exclude"`, `"include"`, `"only"`), and `_hands_enabled: dict[str, bool]` (with keys `"left"` and `"right"`); button states initialized from loaded settings (with `blockSignals` to prevent spurious init signals)
- Two rows of toggle buttons (5 per row) for chord groups + three exclusive radio buttons for sharps mode ("No Sharps", "With Sharps", "Sharps Only") + two toggleable buttons for hands ("✋" for left, "🤚" for right); both hands can be selected simultaneously
- Enforces at-least-one constraint on both chord groups and hands selection; disallows unchecking the last enabled group or the last enabled hand
- On every toggle: calls `settings_manager.save_chord_settings()` to persist new state
- Emits `settings_changed` signal on any toggle change (after save)
- Exposes read-only properties: `group_enabled` (dict copy), `sharps_mode` (str), `hands_enabled` (dict copy)

## Find the Chord Mode page (`find_chord_mode_page.py`)
- Route selection screen: two buttons for Infinite and Timed modes
- Delegates chord settings to `ChordSettingsWidget` (stored as `self._settings`)
- Exposes read-only properties: `group_enabled` (proxies to `self._settings`), `sharps_mode` (proxies to `self._settings`), `hands_enabled` (proxies to `self._settings`)
- Settings are passed to both `FindChordPage` and `FindChordTimedPage` at `activate()` time
- Window size: 620×450

## Find the Chord page (`find_chord_page.py`) — Infinite mode
- Maintains a `list` queue of random chord name strings (e.g. `"Cmaj"`, `"F#min7"`); always keeps 10 pre-generated
- Displays the first 5 chords in a row; leftmost is the current target (larger font, white); others are dimmer/smaller
- On correct chord match: target label turns green (`#44ff44`) for 500ms, then queue shifts left via `_advance()`
- `_advancing: bool` flag blocks re-triggering during the green flash
- `_group_enabled: dict[str, bool]`, `_sharps_mode: str`, `_hands_enabled: dict[str, bool]` — set by `activate()` from FindChordModePage
- `_available_roots()` — returns filtered list of root notes: all 12 if `"include"`, only naturals (7) if `"exclude"`, only sharps (5) if `"only"`
- `_random_chord()` picks a random root and suffix, respecting enabled groups and sharps mode
- `activate(group_enabled: dict, sharps_mode: str, hands_enabled: dict)` — stores settings and starts MIDI playback
- `_poll()` — when both left and right hands are enabled in `_hands_enabled`, uses `count_chord_instances()` to detect when the target chord appears in 2+ independent instances; otherwise uses standard `identify_chord()` comparison
- "Playing" label shows the currently detected chord so the user knows what they're playing if wrong
- Emits `nav_to_mode_select` on back button

## Find the Chord Timed page (`find_chord_timed_page.py`) — Timed mode
- 60-second countdown challenge; goal is to identify as many chords as possible before time expires
- `_waiting_to_start: bool` — when true, chord queue is hidden and Start button is shown; MIDI polling active for warm-up
- `_start_btn` — amber button that starts the game (hides on click, countdown begins)
- `_chord_area` — `QWidget` container wrapping chord row + arrow row; hidden during start screen, shown after Start is pressed
- `_score: int` — incremented on each correct chord; displayed in top-left
- `_best_score: int | None` — fetched on `activate()`; displayed in top-right as "Best: N" or "Best: —"
- `_errors: int` — incremented when user plays 3+ notes forming a recognized chord that doesn't match target; displayed during gameplay and in results overlay
- `_last_chord: str | None` — debounce tracker; any chord equal to `_last_chord` is ignored (prevents double-counting same held chord)
- `_transition_start_time: float | None` — `time.time()` when the current target chord became the target (set in `_start_game()` or in the `show_start=False` branch of `activate()`, updated each time `_advance()` shifts the queue)
- `_current_target_errors: int` — errors made while the current target chord has been the target; reset to 0 in `activate()` and after each `_advance()`
- `_prev_target: str | None` — the chord that was the target before the current one; used to create the chord transition key for stats recording
- `_errors_label`, `_results_errors_label`, `_results_accuracy_label` — UI labels for errors during gameplay and accuracy % in results overlay
- `_time_remaining: int` — counts down from 60 to 0; label turns red (`#ff4444`) at ≤10 seconds
- `_game_over: bool` — set to `True` when timer reaches 0; blocks `_poll()` and `_advance()` from further scoring
- Two timers: `_poll_timer` (50ms, runs always) and `_countdown_timer` (1000ms, starts on Start or Play Again)
- `_group_enabled`, `_sharps_mode`, `_hands_enabled` — set by `activate()` from FindChordModePage
- `_start_game()` — called on Start button click; shows chord queue, starts countdown, sets `_transition_start_time` to begin tracking the first chord
- `_tick()` — decrements `_time_remaining`; calls `_end_game()` at 0
- `_end_game()` — records score and errors to disk via `score_manager.record_score()`, computes accuracy (score / (score + errors) * 100), refreshes best score, stops timers, shows results overlay with final score, best, errors, and accuracy
- `_restart()` — called from "Play Again" button; skips start screen, goes straight to gameplay; error counter reset on `activate()`
- `activate(group_enabled, sharps_mode, hands_enabled, show_start=True)` — fetches and displays best score for this combo; resets errors to 0, `_last_chord` to None, and transition tracking state; if show_start=True, enter start screen; if False, start immediately and set `_transition_start_time`
- `_poll()` — guarded by `if self._waiting_to_start or self._game_over: return`; ignores chords where `chord is None` or `chord == _last_chord` (debounce); on new distinct chord: if both left and right hands are enabled uses `count_chord_instances()` to check for 2+ instances, otherwise uses standard chord comparison; if correct and not `_advancing`, triggers green flash and `_advance()`; if wrong (3+ notes), increments both `_errors` and `_current_target_errors` and updates label
- `_advance()` — records the completed transition via `stats_manager.record_transition()` if `_prev_target` is not None (skips first chord), increments score, shifts queue, updates target and transition timing state for the next chord
- Emits `nav_to_mode_select` on back button or "Back to Menu"

## High Scores page (`high_scores_page.py`)
- Displays top-10 scores for the selected chord group/sharps combination with timestamps and accuracy %
- Uses `ChordSettingsWidget` for toggle controls; same at-least-one-group enforcement
- `_refresh_scores()` called on `settings_changed` signal and `showEvent`; queries `score_manager.get_top_scores()`; computes accuracy as `score / (score + errors) * 100`
- 10 pre-built rows: rank (fixed 30px) | score (fixed 60px, white text) | accuracy (fixed 70px, grey text) | datetime (variable, grey text)
- Empty slots show "—" in score column (grey text `#444444`), empty accuracy and datetime
- Backward compat: entries without `errors` field treated as 0 errors, display 100% accuracy
- Emits `nav_to_home` on back button
- Window size: 620×560

## Score Manager (`score_manager.py`)
- Pure Python module; no Qt dependencies
- `settings_key(group_enabled: dict, sharps_mode: str, hands_enabled: dict) → str` — generates canonical key from enabled group names (sorted), sharps mode (`"include"`, `"exclude"`, or `"only"`), and hands selection (translates `hands_enabled` dict to `"left"`, `"right"`, or `"both"` based on which hands are enabled)
- `get_top_scores(group_enabled, sharps_mode, hands_enabled) → list[dict]` — returns up to 10 entries sorted by score descending then errors ascending for the given settings combo; each entry is `{score: int, errors: int, datetime: str}` (ISO-8601)
- `get_best_score(group_enabled, sharps_mode, hands_enabled) → int | None` — returns highest score for this combo (primary sort) or None
- `record_score(group_enabled, sharps_mode, score: int, errors: int = 0, hands_enabled: dict = None)` — appends new entry with score, errors, and `datetime.now()` timestamp; sorts by (score desc, errors asc) to prioritize highest score, then fewest errors on tie; keeps full history; writes to `score_history.json`
- File format: JSON dict mapping settings keys to sorted entry lists; created on first save, silently recovers from corrupt files

## Settings Manager (`settings_manager.py`)
- Pure Python module; no Qt dependencies
- `load_chord_settings(group_names: list[str]) → dict` — returns saved settings from `chord_settings.json`, falling back to all-enabled defaults on any error (file missing, corrupt, or new groups added); returns dict with keys `"group_enabled"`, `"sharps_mode"`, and `"hands_enabled"`
- `save_chord_settings(group_enabled: dict, sharps_mode: str, hands_enabled: dict) → None` — writes settings to `chord_settings.json`
- File format: JSON with `{"group_enabled": {group_name: bool, ...}, "sharps_mode": "include"|"exclude"|"only", "hands_enabled": {"left": bool, "right": bool}}`; created on first toggle change; defaults to right hand only if no settings file exists

## Stats Manager (`stats_manager.py`)
- Pure Python module; no Qt dependencies; used only in timed mode
- Tracks chord transition statistics: per-transition time (in seconds) and error counts
- `record_transition(from_chord: str, to_chord: str, elapsed_seconds: float, errors: int) → None` — records or updates a transition stat entry; maintains running averages (new_avg = (old_avg * old_count + new_value) / (old_count + 1))
- File format: JSON dict mapping chord transition keys (e.g. `"AmajCmaj"`) to entry dicts; each entry: `{"time": float (rounded to 3 decimals), "errors": float (rounded to 3 decimals), "count": int}`
- Key generation: simple concatenation `f"{from_chord}{to_chord}"` with no separator (e.g. "Cmaj" → "F#min" becomes `"CmajF#min"`)
- File is created on first transition record; silently recovers from corrupt files (returns empty dict)
- Note: stats are global and not keyed by game settings (chord group filters, sharps mode, hands mode), as physical chord difficulty is independent of these settings

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
