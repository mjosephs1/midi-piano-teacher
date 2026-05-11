import random
import threading

import mido
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, QMessageBox
from PyQt6.QtCore import QTimer, pyqtSignal, Qt
from PyQt6.QtGui import QFont

from midi_display import NOTE_NAMES, CHORD_PATTERNS, identify_chord, count_chord_instances

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
    nav_to_mode_select = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.active_notes = set()
        self._lock = threading.Lock()
        self._port = None
        self._active = False
        self._advancing = False
        self._queue = []
        self._group_enabled = {}
        self._sharps_mode = "include"
        self._hands_enabled = {"left": False, "right": True}

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

    def _available_roots(self) -> list[str]:
        if self._sharps_mode == "exclude":
            return [n for n in NOTE_NAMES if "#" not in n]
        elif self._sharps_mode == "only":
            return [n for n in NOTE_NAMES if "#" in n]
        else:  # "include"
            return NOTE_NAMES

    def _build_queue(self) -> list[str]:
        queue = []
        for _ in range(_QUEUE_SIZE):
            prev = queue[-1] if queue else None
            queue.append(self._random_chord(exclude=prev))
        return queue

    def _random_chord(self, exclude: str | None = None) -> str:
        roots = self._available_roots()
        suffixes = [s for name, sl in CHORD_GROUPS.items() if self._group_enabled[name] for s in sl]
        chord = f"{random.choice(roots)}{random.choice(suffixes)}"
        while exclude is not None and chord == exclude and len(roots) * len(suffixes) > 1:
            chord = f"{random.choice(roots)}{random.choice(suffixes)}"
        return chord

    def activate(self, group_enabled: dict[str, bool], sharps_mode: str, hands_enabled: dict[str, bool]):
        if self._active:
            return
        ports = mido.get_input_names()
        if not ports:
            QMessageBox.warning(self, "No MIDI Device",
                "No MIDI input devices found.\nConnect a device and try again.")
            return
        self._group_enabled = group_enabled.copy()
        self._sharps_mode = sharps_mode
        self._hands_enabled = hands_enabled.copy()
        self._active = True
        self._advancing = False
        self.active_notes = set()
        self._queue = self._build_queue()
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
        self.nav_to_mode_select.emit()

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

        if not chord or self._advancing or not self._queue:
            return

        target = self._queue[0]
        matched = False

        if self._hands_enabled.get("left") and self._hands_enabled.get("right"):
            matched = count_chord_instances(set(notes), target) >= 2
        else:
            matched = chord == target

        if matched:
            self._chord_labels[0].setStyleSheet("color: #44ff44; background-color: transparent;")
            self._advancing = True
            QTimer.singleShot(_GREEN_DURATION_MS, self._advance)

    def _advance(self):
        self._queue.pop(0)
        while len(self._queue) < _QUEUE_SIZE:
            self._queue.append(self._random_chord(exclude=self._queue[-1] if self._queue else None))
        self._refresh_chord_labels()
        self._advancing = False
