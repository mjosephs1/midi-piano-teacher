#!/usr/bin/env python3
"""Real-time MIDI note and chord display — macOS desktop app."""

import sys
import threading

try:
    import mido
except ImportError:
    print("Missing dependency: pip install mido python-rtmidi")
    sys.exit(1)

try:
    from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QFrame, QMessageBox
    from PyQt6.QtCore import Qt, QTimer
    from PyQt6.QtGui import QFont
except ImportError:
    print("Missing dependency: pip install PyQt6")
    sys.exit(1)

from midi_display import midi_to_note, identify_chord


class MidiDisplayWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.active_notes = set()
        self._lock = threading.Lock()
        self._port = None

        self._build_ui()
        self._start_midi()

        self._timer = QTimer()
        self._timer.timeout.connect(self._poll)
        self._timer.start(50)

    def _build_ui(self):
        self.setWindowTitle("MIDI Piano Display")
        self.setFixedSize(420, 200)
        self.setStyleSheet("background-color: #1e1e1e;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(0)

        self.device_label = QLabel("No device")
        self.device_label.setStyleSheet("color: #aaaaaa;")
        self.device_label.setFont(QFont("Helvetica", 13))
        layout.addWidget(self.device_label)

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("color: #333333;")
        layout.addSpacing(8)
        layout.addWidget(divider)
        layout.addSpacing(16)

        self.notes_label = self._make_row(layout, "Notes")
        self.chord_label = self._make_row(layout, "Chord")
        layout.addStretch()

    def _make_row(self, layout, heading):
        row = QWidget()
        row.setStyleSheet("background-color: #1e1e1e;")
        row_layout = QVBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 8)
        row_layout.setSpacing(2)

        head = QLabel(heading)
        head.setStyleSheet("color: #aaaaaa;")
        head.setFont(QFont("Helvetica", 13))
        row_layout.addWidget(head)

        value = QLabel("--")
        value.setStyleSheet("color: #ffffff;")
        value.setFont(QFont("Helvetica", 28, QFont.Weight.Bold))
        row_layout.addWidget(value)

        layout.addWidget(row)
        return value

    def _start_midi(self):
        ports = mido.get_input_names()
        if not ports:
            QMessageBox.critical(self, "No MIDI Device",
                "No MIDI input devices found.\nConnect a device and relaunch.")
            sys.exit(1)

        self.device_label.setText(f"Device: {ports[0]}")
        t = threading.Thread(target=self._midi_loop, args=(ports[0],), daemon=True)
        t.start()

    def _midi_loop(self, port_name):
        try:
            with mido.open_input(port_name) as port:
                self._port = port
                for msg in port:
                    with self._lock:
                        if msg.type == "note_on" and msg.velocity > 0:
                            self.active_notes.add(msg.note)
                        elif msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0):
                            self.active_notes.discard(msg.note)
        except Exception:
            pass

    def _poll(self):
        with self._lock:
            notes = sorted(self.active_notes)

        if notes:
            note_strs = [f"{name}{octave}" for name, octave in (midi_to_note(n) for n in notes)]
            self.notes_label.setText("  ".join(note_strs))
            chord = identify_chord(notes)
            self.chord_label.setText(chord if chord else "--")
        else:
            self.notes_label.setText("--")
            self.chord_label.setText("--")

    def closeEvent(self, event):
        if self._port is not None:
            self._port.close()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MidiDisplayWindow()
    window.show()
    sys.exit(app.exec())
