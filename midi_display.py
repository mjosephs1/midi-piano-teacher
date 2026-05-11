#!/usr/bin/env python3
"""Real-time MIDI note and chord display for terminal."""

import sys
import time
import threading
from collections import defaultdict

try:
    import mido
except ImportError:
    print("Missing dependency: pip install mido python-rtmidi")
    sys.exit(1)

# Note names
NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# Common chord intervals (semitones from root)
CHORD_PATTERNS = {
    (4, 7): "maj",
    (3, 7): "min",
    (4, 7, 11): "maj7",
    (4, 7, 10): "7",
    (3, 7, 10): "min7",
    (3, 6): "dim",
    (4, 8): "aug",
    (3, 6, 9): "dim7",
    (3, 6, 10): "m7b5",
    (2, 7): "sus2",
    (5, 7): "sus4",
    (4, 7, 9): "6",
    (3, 7, 9): "min6",
    (4, 7, 11, 14): "maj9",
    (4, 7, 10, 14): "9",
    (3, 7, 10, 14): "min9",
    (5, 7, 10): "7sus4",
    (4, 8, 10): "aug7",
}

def midi_to_note(midi_num):
    octave = (midi_num // 12) - 1
    name = NOTE_NAMES[midi_num % 12]
    return name, octave

def identify_chord(midi_notes):
    if len(midi_notes) < 2:
        return None

    notes = sorted(midi_notes)

    # Try all inversions by rotating bass note
    for i in range(len(notes)):
        rotated = notes[i:] + [n + 12 for n in notes[:i]]
        root = rotated[0]
        intervals = tuple(n - root for n in rotated[1:])

        if intervals in CHORD_PATTERNS:
            root_name = NOTE_NAMES[root % 12]
            return f"{root_name}{CHORD_PATTERNS[intervals]}"

    # Try to match subset patterns (ignore extra notes)
    for i in range(len(notes)):
        root = notes[i]
        intervals = tuple(sorted(n - root for n in notes if n != root and (n - root) % 12 != 0))
        # Normalize to within one octave
        normalized = tuple(sorted(set(iv % 12 for iv in intervals if iv % 12 != 0)))
        if normalized in CHORD_PATTERNS:
            root_name = NOTE_NAMES[root % 12]
            return f"{root_name}{CHORD_PATTERNS[normalized]}"

    return None

def count_chord_instances(active_notes, target_chord):
    if not target_chord or not active_notes:
        return 0

    if len(active_notes) < 2:
        return 0

    root_name = target_chord[0]
    if target_chord.startswith("C#"):
        root_name = "C#"
    elif target_chord.startswith("D#"):
        root_name = "D#"
    elif target_chord.startswith("F#"):
        root_name = "F#"
    elif target_chord.startswith("G#"):
        root_name = "G#"
    elif target_chord.startswith("A#"):
        root_name = "A#"

    root_idx = NOTE_NAMES.index(root_name) if root_name in NOTE_NAMES else -1
    if root_idx == -1:
        return 0

    suffix = target_chord[len(root_name):]
    intervals = None
    for pattern, suffix_str in CHORD_PATTERNS.items():
        if suffix_str == suffix:
            intervals = pattern
            break

    if intervals is None:
        return 0

    required_pitch_classes = {(root_idx + i) % 12 for i in intervals}
    required_pitch_classes.add(root_idx)

    counts = defaultdict(int)
    for midi_note in active_notes:
        pitch_class = midi_note % 12
        if pitch_class in required_pitch_classes:
            counts[pitch_class] += 1

    if len(counts) < len(required_pitch_classes):
        return 0

    return min(counts[pc] for pc in required_pitch_classes)

def format_display(active_notes):
    if not active_notes:
        return "  Notes:  --\n  Chord:  --"

    sorted_notes = sorted(active_notes)
    note_strs = []
    for midi_num in sorted_notes:
        name, octave = midi_to_note(midi_num)
        note_strs.append(f"{name}{octave}")

    notes_line = "  Notes:  " + "  ".join(note_strs)

    chord = identify_chord(sorted_notes)
    chord_line = "  Chord:  " + (chord if chord else "--")

    return notes_line + "\n" + chord_line

def clear_lines(n):
    for _ in range(n):
        sys.stdout.write("\033[F\033[K")

def main():
    ports = mido.get_input_names()
    if not ports:
        print("No MIDI input devices found. Connect a MIDI device and try again.")
        sys.exit(1)

    print("\033[2J\033[H", end="")  # Clear screen
    print("=== MIDI Piano Display ===")
    print(f"Device: {ports[0]}")
    print("Press Ctrl+C to quit\n")

    active_notes = set()
    lock = threading.Lock()
    display_lines = 2

    # Print initial empty state
    print(format_display(active_notes))

    def refresh():
        clear_lines(display_lines)
        print(format_display(active_notes))

    try:
        with mido.open_input(ports[0]) as port:
            for msg in port:
                with lock:
                    if msg.type == "note_on" and msg.velocity > 0:
                        active_notes.add(msg.note)
                        refresh()
                    elif msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0):
                        active_notes.discard(msg.note)
                        refresh()
    except KeyboardInterrupt:
        print("\n\nGoodbye.")

if __name__ == "__main__":
    main()
