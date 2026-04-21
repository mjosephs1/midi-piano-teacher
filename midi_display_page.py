import threading

import mido
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, QMessageBox
from PyQt6.QtCore import QTimer, pyqtSignal
from PyQt6.QtGui import QFont

from midi_display import midi_to_note, identify_chord


class MidiDisplayPage(QWidget):
    nav_to_home = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.active_notes = set()
        self._lock = threading.Lock()
        self._port = None
        self._active = False

        self._timer = QTimer()
        self._timer.timeout.connect(self._poll)

        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet("background-color: #1e1e1e;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 16, 30, 20)
        layout.setSpacing(0)

        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)

        back_btn = QPushButton("← Back")
        back_btn.setFont(QFont("Helvetica", 13))
        back_btn.setFixedHeight(28)
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #aaaaaa;
                border: none;
                text-align: left;
                padding: 0;
            }
            QPushButton:hover { color: #ffffff; }
        """)
        back_btn.clicked.connect(self._on_back)
        top_row.addWidget(back_btn)
        top_row.addStretch()

        layout.addLayout(top_row)

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
        row.setStyleSheet("background-color: transparent;")
        row_layout = QVBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 8)
        row_layout.setSpacing(2)

        head = QLabel(heading)
        head.setStyleSheet("color: #aaaaaa; background-color: transparent;")
        head.setFont(QFont("Helvetica", 13))
        row_layout.addWidget(head)

        value = QLabel("--")
        value.setStyleSheet("color: #ffffff; background-color: transparent;")
        value.setFont(QFont("Helvetica", 28, QFont.Weight.Bold))
        row_layout.addWidget(value)

        layout.addWidget(row)
        return value

    def activate(self):
        if self._active:
            return
        ports = mido.get_input_names()
        if not ports:
            QMessageBox.warning(self, "No MIDI Device",
                "No MIDI input devices found.\nConnect a device and try again.")
            return
        self._active = True
        self.active_notes = set()
        self.notes_label.setText("--")
        self.chord_label.setText("--")
        t = threading.Thread(target=self._midi_loop, args=(ports[0],), daemon=True)
        t.start()
        self._timer.start(50)

    def deactivate(self):
        self._timer.stop()
        if self._port is not None:
            self._port.close()
            self._port = None
        self._active = False

    def _on_back(self):
        self.deactivate()
        self.nav_to_home.emit()

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
