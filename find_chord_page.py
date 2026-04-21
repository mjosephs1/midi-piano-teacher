import random
import threading

import mido
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, QMessageBox
from PyQt6.QtCore import QTimer, pyqtSignal, Qt
from PyQt6.QtGui import QFont

from midi_display import NOTE_NAMES, CHORD_PATTERNS, identify_chord

_QUEUE_SIZE = 10
_DISPLAY_COUNT = 5
_GREEN_DURATION_MS = 500

CHORD_GROUPS = {
    "Major":      ["maj"],
    "Minor":      ["min"],
    "Suspended":  ["sus2", "sus4", "7sus4"],
    "Augmented":  ["aug", "aug7"],
    "Diminished": ["dim", "dim7", "m7b5"],
    "Dom 7th":    ["7"],
    "Major 7th":  ["maj7"],
    "Minor 7th":  ["min7"],
    "Extended":   ["maj9", "9", "min9"],
    "Add":        ["6", "min6"],
}


def _toggle_style(checked: bool) -> str:
    if checked:
        return ("QPushButton { background-color: #3a7bd5; color: #ffffff; border: none; "
                "border-radius: 4px; padding: 0 10px; } "
                "QPushButton:hover { background-color: #4a8be5; }")
    return ("QPushButton { background-color: #2a2a2a; color: #666666; border: 1px solid #444444; "
            "border-radius: 4px; padding: 0 10px; } "
            "QPushButton:hover { background-color: #333333; color: #999999; }")


class FindChordPage(QWidget):
    nav_to_home = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.active_notes = set()
        self._lock = threading.Lock()
        self._port = None
        self._active = False
        self._advancing = False
        self._queue = []
        self._group_enabled = {name: True for name in CHORD_GROUPS}
        self._group_buttons: dict[str, QPushButton] = {}

        self._timer = QTimer()
        self._timer.timeout.connect(self._poll)

        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet("background-color: #1e1e1e;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 16, 30, 24)
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

        layout.addSpacing(8)
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("color: #333333;")
        layout.addWidget(divider)
        layout.addSpacing(16)

        title = QLabel("Find the Chord")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #ffffff; background-color: transparent;")
        title.setFont(QFont("Helvetica", 20, QFont.Weight.Bold))
        layout.addWidget(title)

        layout.addSpacing(20)

        chord_row = QHBoxLayout()
        chord_row.setSpacing(8)
        chord_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._chord_labels = []
        for i in range(_DISPLAY_COUNT):
            lbl = QLabel("--")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setFixedWidth(110)
            font_size = 32 if i == 0 else 24
            lbl.setFont(QFont("Helvetica", font_size, QFont.Weight.Bold))
            color = "#ffffff" if i == 0 else "#888888"
            lbl.setStyleSheet(f"color: {color}; background-color: transparent;")
            chord_row.addWidget(lbl)
            self._chord_labels.append(lbl)
        layout.addLayout(chord_row)

        layout.addSpacing(2)

        # Arrow points at the leftmost (target) chord label
        arrow_row = QHBoxLayout()
        arrow_row.setSpacing(8)
        arrow_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        arrow_lbl = QLabel("↑  play this")
        arrow_lbl.setFixedWidth(110)
        arrow_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        arrow_lbl.setStyleSheet("color: #3a7bd5; background-color: transparent;")
        arrow_lbl.setFont(QFont("Helvetica", 12))
        arrow_row.addWidget(arrow_lbl)
        for _ in range(_DISPLAY_COUNT - 1):
            spacer = QLabel()
            spacer.setFixedWidth(110)
            spacer.setStyleSheet("background-color: transparent;")
            arrow_row.addWidget(spacer)
        layout.addLayout(arrow_row)

        layout.addStretch()

        settings_divider = QFrame()
        settings_divider.setFrameShape(QFrame.Shape.HLine)
        settings_divider.setStyleSheet("color: #333333;")
        layout.addWidget(settings_divider)

        layout.addSpacing(8)

        group_names = list(CHORD_GROUPS.keys())
        for row_names in [group_names[:5], group_names[5:]]:
            row = QHBoxLayout()
            row.setSpacing(6)
            row.setAlignment(Qt.AlignmentFlag.AlignCenter)
            for group_name in row_names:
                btn = QPushButton(group_name)
                btn.setCheckable(True)
                btn.setChecked(True)
                btn.setFixedHeight(26)
                btn.setFont(QFont("Helvetica", 11))
                btn.setStyleSheet(_toggle_style(checked=True))
                btn.toggled.connect(lambda checked, n=group_name: self._on_group_toggled(n, checked))
                row.addWidget(btn)
                self._group_buttons[group_name] = btn
            layout.addLayout(row)
            layout.addSpacing(4)

        layout.addSpacing(8)

        playing_heading = QLabel("Playing")
        playing_heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        playing_heading.setStyleSheet("color: #aaaaaa; background-color: transparent;")
        playing_heading.setFont(QFont("Helvetica", 13))
        layout.addWidget(playing_heading)

        self._playing_label = QLabel("--")
        self._playing_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._playing_label.setStyleSheet("color: #ffffff; background-color: transparent;")
        self._playing_label.setFont(QFont("Helvetica", 28, QFont.Weight.Bold))
        layout.addWidget(self._playing_label)

    def _refresh_chord_labels(self):
        for i, lbl in enumerate(self._chord_labels):
            text = self._queue[i] if i < len(self._queue) else "--"
            lbl.setText(text)
            if i == 0:
                lbl.setFont(QFont("Helvetica", 32, QFont.Weight.Bold))
                lbl.setStyleSheet("color: #ffffff; background-color: transparent;")
            else:
                lbl.setFont(QFont("Helvetica", 24, QFont.Weight.Bold))
                lbl.setStyleSheet("color: #888888; background-color: transparent;")

    def _random_chord(self) -> str:
        suffixes = [s for name, sl in CHORD_GROUPS.items() if self._group_enabled[name] for s in sl]
        return f"{random.choice(NOTE_NAMES)}{random.choice(suffixes)}"

    def _on_group_toggled(self, name: str, checked: bool) -> None:
        if not checked and sum(self._group_enabled.values()) <= 1:
            btn = self._group_buttons[name]
            btn.blockSignals(True)
            btn.setChecked(True)
            btn.blockSignals(False)
            btn.setStyleSheet(_toggle_style(checked=True))
            return
        self._group_enabled[name] = checked
        self._group_buttons[name].setStyleSheet(_toggle_style(checked=checked))
        if self._active:
            self._queue = [self._random_chord() for _ in range(_QUEUE_SIZE)]
            self._refresh_chord_labels()

    def activate(self):
        if self._active:
            return
        ports = mido.get_input_names()
        if not ports:
            QMessageBox.warning(self, "No MIDI Device",
                "No MIDI input devices found.\nConnect a device and try again.")
            return
        self._active = True
        self._advancing = False
        self.active_notes = set()
        self._queue = [self._random_chord() for _ in range(_QUEUE_SIZE)]
        self._refresh_chord_labels()
        self._playing_label.setText("--")
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

        chord = identify_chord(notes) if notes else None
        self._playing_label.setText(chord if chord else "--")

        if chord and not self._advancing and self._queue and chord == self._queue[0]:
            self._chord_labels[0].setStyleSheet("color: #44ff44; background-color: transparent;")
            self._advancing = True
            QTimer.singleShot(_GREEN_DURATION_MS, self._advance)

    def _advance(self):
        self._queue.pop(0)
        while len(self._queue) < _QUEUE_SIZE:
            self._queue.append(self._random_chord())
        self._refresh_chord_labels()
        self._advancing = False
