from datetime import datetime

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont

from chord_settings_widget import ChordSettingsWidget
import score_manager


def _fmt_dt(iso_str: str) -> str:
    try:
        return datetime.fromisoformat(iso_str).strftime("%b %d, %Y  %H:%M")
    except Exception:
        return iso_str


class HighScoresPage(QWidget):
    nav_to_home = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet("background-color: #1e1e1e;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 24, 30, 24)
        layout.setSpacing(0)

        # Back button at top
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

        # Title
        title = QLabel("High Scores")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #ffffff; background-color: transparent;")
        title.setFont(QFont("Helvetica", 20, QFont.Weight.Bold))
        layout.addWidget(title)

        layout.addSpacing(12)

        # Settings widget
        self._settings = ChordSettingsWidget()
        self._settings.settings_changed.connect(self._refresh_scores)
        layout.addWidget(self._settings)

        layout.addSpacing(12)

        # Second divider
        divider2 = QFrame()
        divider2.setFrameShape(QFrame.Shape.HLine)
        divider2.setStyleSheet("color: #333333;")
        layout.addWidget(divider2)

        layout.addSpacing(8)

        # Score rows
        self._scores_container = QVBoxLayout()
        self._scores_container.setSpacing(2)

        self._rank_labels: list[QLabel] = []
        self._score_value_labels: list[QLabel] = []
        self._datetime_labels: list[QLabel] = []

        for i in range(10):
            row = QHBoxLayout()
            row.setContentsMargins(0, 2, 0, 2)

            rank_lbl = QLabel(f"{i+1}.")
            rank_lbl.setFixedWidth(30)
            rank_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            rank_lbl.setFont(QFont("Helvetica", 13))
            rank_lbl.setStyleSheet("color: #666666; background-color: transparent;")

            score_lbl = QLabel("—")
            score_lbl.setFixedWidth(60)
            score_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            score_lbl.setFont(QFont("Helvetica", 13, QFont.Weight.Bold))
            score_lbl.setStyleSheet("color: #ffffff; background-color: transparent;")

            date_lbl = QLabel("")
            date_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            date_lbl.setFont(QFont("Helvetica", 11))
            date_lbl.setStyleSheet("color: #666666; background-color: transparent;")

            row.addWidget(rank_lbl)
            row.addSpacing(8)
            row.addWidget(score_lbl)
            row.addSpacing(8)
            row.addWidget(date_lbl)
            row.addStretch()

            self._scores_container.addLayout(row)
            self._rank_labels.append(rank_lbl)
            self._score_value_labels.append(score_lbl)
            self._datetime_labels.append(date_lbl)

        layout.addLayout(self._scores_container)
        layout.addStretch()

    def _refresh_scores(self) -> None:
        entries = score_manager.get_top_scores(
            self._settings.group_enabled, self._settings.sharps_enabled
        )
        for i, (rank_lbl, score_lbl, date_lbl) in enumerate(
            zip(self._rank_labels, self._score_value_labels, self._datetime_labels)
        ):
            if i < len(entries):
                e = entries[i]
                score_lbl.setText(str(e["score"]))
                score_lbl.setStyleSheet("color: #ffffff; background-color: transparent;")
                dt_str = _fmt_dt(e["datetime"])
                date_lbl.setText(dt_str)
            else:
                score_lbl.setText("—")
                score_lbl.setStyleSheet("color: #444444; background-color: transparent;")
                date_lbl.setText("")

    def showEvent(self, event):
        super().showEvent(event)
        self._refresh_scores()

    def _on_back(self):
        self.nav_to_home.emit()
