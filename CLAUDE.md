# MIDI Piano Teacher

Real-time MIDI note and chord display app for macOS, written in Python.

## Files
- `midi_display.py` — terminal app (original)
- `midi_display_gui.py` — macOS desktop app (PyQt6); imports from `midi_display.py`
- `requirements.txt` — `mido>=1.3.0`, `python-rtmidi>=1.5.0`; PyQt6 also required but not yet in requirements.txt

## Key functions in `midi_display.py`
- `midi_to_note(midi_num)` → `(name, octave)` — converts MIDI number to note name/octave
- `identify_chord(midi_notes)` → `str | None` — chord detection from a list of MIDI numbers; tries all inversions, falls back to subset matching
- `NOTE_NAMES` — 12-element list of note name strings
- `CHORD_PATTERNS` — dict mapping semitone interval tuples to chord name suffixes (18 chord types)

## Architecture
- MIDI input via `mido.open_input()` blocking iterator, runs in a daemon thread
- `active_notes: set` tracks currently held MIDI note numbers; protected by `threading.Lock`
- GUI polls state every 50ms via `QTimer` on the main thread
- Device: auto-selects first available MIDI input port

## Dependencies
```
pip install mido python-rtmidi PyQt6
```

## Run
```
python midi_display_gui.py   # desktop app
python midi_display.py       # terminal app
```
