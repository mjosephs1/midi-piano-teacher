import random
import threading

import mido
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, QMessageBox
from PyQt6.QtCore import QTimer, pyqtSignal, Qt
from PyQt6.QtGui import QFont

from midi_display import NOTE_NAMES, CHORD_PATTERNS, identify_chord
from find_chord_page import CHORD_GROUPS

_QUEUE_SIZE = 10
_DISPLAY_COUNT = 5
_GREEN_DURATION_MS = 500
_GAME_DURATION_SECS = 60


class FindChordTimedPage(QWidget):
    nav_to_mode_select = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.active_notes = set()
        self._lock = threading.Lock()
        self._port = None
        self._active = False
        self._advancing = False
        self._game_over = False
        self._waiting_to_start = False
        self._queue = []
        self._score = 0
        self._time_remaining = _GAME_DURATION_SECS
        self._group_enabled = {}
        self._sharps_enabled = True

        self._poll_timer = QTimer()
        self._poll_timer.timeout.connect(self._poll)

        self._countdown_timer = QTimer()
        self._countdown_timer.timeout.connect(self._tick)

        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet("background-color: #1e1e1e;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 16, 30, 24)
        layout.setSpacing(0)

        # Top row: Back button and Score label
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

        self._score_label = QLabel("Score: 0")
        self._score_label.setStyleSheet("color: #ffffff; background-color: transparent;")
        self._score_label.setFont(QFont("Helvetica", 14))
        top_row.addWidget(self._score_label)
        layout.addLayout(top_row)

        layout.addSpacing(8)
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("color: #333333;")
        layout.addWidget(divider)
        layout.addSpacing(16)

        # Time label
        self._time_label = QLabel("60s")
        self._time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._time_label.setStyleSheet("color: #ffffff; background-color: transparent;")
        self._time_label.setFont(QFont("Helvetica", 18, QFont.Weight.Bold))
        layout.addWidget(self._time_label)

        layout.addSpacing(8)

        # Title
        title = QLabel("Find the Chord — Timed")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #ffffff; background-color: transparent;")
        title.setFont(QFont("Helvetica", 18, QFont.Weight.Bold))
        layout.addWidget(title)

        layout.addSpacing(16)

        # Chord area container (chord row + arrow row)
        self._chord_area = QWidget()
        chord_area_layout = QVBoxLayout(self._chord_area)
        chord_area_layout.setContentsMargins(0, 0, 0, 0)
        chord_area_layout.setSpacing(2)

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
        chord_area_layout.addLayout(chord_row)

        # Arrow row
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
        chord_area_layout.addLayout(arrow_row)

        layout.addWidget(self._chord_area)

        # Start button (hidden initially)
        self._start_btn = QPushButton("Start")
        self._start_btn.setFixedHeight(44)
        self._start_btn.setFont(QFont("Helvetica", 15))
        self._start_btn.setStyleSheet("""
            QPushButton {
                background-color: #b06000;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #c07010; }
        """)
        self._start_btn.clicked.connect(self._start_game)
        self._start_btn.hide()
        layout.addWidget(self._start_btn)

        layout.addStretch()

        # Playing row
        divider2 = QFrame()
        divider2.setFrameShape(QFrame.Shape.HLine)
        divider2.setStyleSheet("color: #333333;")
        layout.addWidget(divider2)
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

        # Results overlay (hidden initially)
        self._results_overlay = QFrame(self)
        self._results_overlay.setStyleSheet("background-color: rgba(20, 20, 20, 220);")
        self._results_overlay.setFrameShape(QFrame.Shape.NoFrame)
        overlay_layout = QVBoxLayout(self._results_overlay)
        overlay_layout.setContentsMargins(40, 80, 40, 80)
        overlay_layout.setSpacing(16)

        results_title = QLabel("Time's Up!")
        results_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        results_title.setStyleSheet("color: #ffffff; background-color: transparent;")
        results_title.setFont(QFont("Helvetica", 22, QFont.Weight.Bold))
        overlay_layout.addWidget(results_title)

        self._results_score_label = QLabel("Score: 0")
        self._results_score_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._results_score_label.setStyleSheet("color: #44ff44; background-color: transparent;")
        self._results_score_label.setFont(QFont("Helvetica", 36, QFont.Weight.Bold))
        overlay_layout.addWidget(self._results_score_label)

        overlay_layout.addSpacing(20)

        play_again_btn = QPushButton("Play Again")
        play_again_btn.setFixedHeight(44)
        play_again_btn.setFont(QFont("Helvetica", 15))
        play_again_btn.setStyleSheet("""
            QPushButton {
                background-color: #2e7d4f;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #3a9560; }
        """)
        play_again_btn.clicked.connect(self._restart)
        overlay_layout.addWidget(play_again_btn)

        overlay_layout.addSpacing(10)

        back_menu_btn = QPushButton("Back to Menu")
        back_menu_btn.setFixedHeight(44)
        back_menu_btn.setFont(QFont("Helvetica", 15))
        back_menu_btn.setStyleSheet("""
            QPushButton {
                background-color: #444444;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #555555; }
        """)
        back_menu_btn.clicked.connect(self._on_back)
        overlay_layout.addWidget(back_menu_btn)

        overlay_layout.addStretch()

        self._results_overlay.hide()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._results_overlay.setGeometry(self.rect())

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

    def _build_queue(self) -> list[str]:
        queue = []
        for _ in range(_QUEUE_SIZE):
            prev = queue[-1] if queue else None
            queue.append(self._random_chord(exclude=prev))
        return queue

    def _random_chord(self, exclude: str | None = None) -> str:
        suffixes = [s for sl in CHORD_GROUPS.values() for s in sl]
        roots = NOTE_NAMES if self._sharps_enabled else [n for n in NOTE_NAMES if "#" not in n]
        enabled_roots = roots
        enabled_suffixes = [s for name, sl in CHORD_GROUPS.items() if self._group_enabled.get(name, True) for s in sl]
        chord = f"{random.choice(enabled_roots)}{random.choice(enabled_suffixes)}"
        while exclude is not None and chord == exclude and len(enabled_roots) * len(enabled_suffixes) > 1:
            chord = f"{random.choice(enabled_roots)}{random.choice(enabled_suffixes)}"
        return chord

    def activate(self, group_enabled: dict[str, bool], sharps_enabled: bool, show_start: bool = True):
        if self._active:
            return
        ports = mido.get_input_names()
        if not ports:
            QMessageBox.warning(self, "No MIDI Device",
                "No MIDI input devices found.\nConnect a device and try again.")
            return

        self._group_enabled = group_enabled.copy()
        self._sharps_enabled = sharps_enabled
        self._active = True
        self._game_over = False
        self._advancing = False
        self._score = 0
        self._time_remaining = _GAME_DURATION_SECS
        self.active_notes = set()

        self._score_label.setText("Score: 0")
        self._time_label.setText("60s")
        self._time_label.setStyleSheet("color: #ffffff; background-color: transparent;")
        self._playing_label.setText("--")
        self._results_overlay.hide()

        t = threading.Thread(target=self._midi_loop, args=(ports[0],), daemon=True)
        t.start()
        self._poll_timer.start(50)

        if show_start:
            self._waiting_to_start = True
            self._chord_area.hide()
            self._start_btn.show()
        else:
            self._waiting_to_start = False
            self._queue = self._build_queue()
            self._refresh_chord_labels()
            self._chord_area.show()
            self._start_btn.hide()
            self._countdown_timer.start(1000)

    def deactivate(self):
        self._poll_timer.stop()
        self._countdown_timer.stop()
        if self._port is not None:
            self._port.close()
            self._port = None
        self._active = False

    def _on_back(self):
        self.deactivate()
        self.nav_to_mode_select.emit()

    def _start_game(self):
        self._waiting_to_start = False
        self._chord_area.show()
        self._start_btn.hide()
        self._queue = self._build_queue()
        self._refresh_chord_labels()
        self._countdown_timer.start(1000)

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

    def _tick(self):
        self._time_remaining -= 1
        self._time_label.setText(f"{self._time_remaining}s")
        if self._time_remaining <= 10:
            self._time_label.setStyleSheet("color: #ff4444; background-color: transparent;")
        if self._time_remaining <= 0:
            self._end_game()

    def _end_game(self):
        self._game_over = True
        self._countdown_timer.stop()
        self._poll_timer.stop()
        self._results_score_label.setText(f"Score: {self._score}")
        self._results_overlay.setGeometry(self.rect())
        self._results_overlay.raise_()
        self._results_overlay.show()

    def _restart(self):
        self._results_overlay.hide()
        self.deactivate()
        self.activate(self._group_enabled, self._sharps_enabled, show_start=False)

    def _poll(self):
        if self._waiting_to_start or self._game_over:
            return

        with self._lock:
            notes = sorted(self.active_notes)

        chord = identify_chord(notes) if notes else None
        self._playing_label.setText(chord if chord else "--")

        if chord and not self._advancing and self._queue and chord == self._queue[0]:
            self._chord_labels[0].setStyleSheet("color: #44ff44; background-color: transparent;")
            self._advancing = True
            QTimer.singleShot(_GREEN_DURATION_MS, self._advance)

    def _advance(self):
        if self._game_over:
            self._advancing = False
            return
        self._score += 1
        self._score_label.setText(f"Score: {self._score}")
        self._queue.pop(0)
        while len(self._queue) < _QUEUE_SIZE:
            self._queue.append(self._random_chord(exclude=self._queue[-1] if self._queue else None))
        self._refresh_chord_labels()
        self._advancing = False
