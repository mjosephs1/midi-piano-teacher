from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont

from chord_settings_widget import ChordSettingsWidget


class FindChordModePage(QWidget):
    nav_to_home = pyqtSignal()
    nav_to_infinite = pyqtSignal()
    nav_to_timed = pyqtSignal()

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
        title = QLabel("Find the Chord")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #ffffff; background-color: transparent;")
        title.setFont(QFont("Helvetica", 20, QFont.Weight.Bold))
        layout.addWidget(title)

        layout.addSpacing(20)

        # Infinite button
        infinite_btn = QPushButton("Infinite")
        infinite_btn.setFixedHeight(44)
        infinite_btn.setFont(QFont("Helvetica", 15))
        infinite_btn.setStyleSheet("""
            QPushButton {
                background-color: #2e7d4f;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #3a9560; }
        """)
        infinite_btn.clicked.connect(self._on_infinite)
        layout.addWidget(infinite_btn)

        layout.addSpacing(12)

        # Timed button
        timed_btn = QPushButton("Timed")
        timed_btn.setFixedHeight(44)
        timed_btn.setFont(QFont("Helvetica", 15))
        timed_btn.setStyleSheet("""
            QPushButton {
                background-color: #b06000;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #c07010; }
        """)
        timed_btn.clicked.connect(self._on_timed)
        layout.addWidget(timed_btn)

        layout.addSpacing(16)

        # Settings divider
        settings_divider = QFrame()
        settings_divider.setFrameShape(QFrame.Shape.HLine)
        settings_divider.setStyleSheet("color: #333333;")
        layout.addWidget(settings_divider)

        layout.addSpacing(8)

        self._settings = ChordSettingsWidget()
        layout.addWidget(self._settings)

        layout.addStretch()

    @property
    def group_enabled(self) -> dict[str, bool]:
        return self._settings.group_enabled

    @property
    def sharps_enabled(self) -> bool:
        return self._settings.sharps_enabled

    def _on_back(self):
        self.nav_to_home.emit()

    def _on_infinite(self):
        self.nav_to_infinite.emit()

    def _on_timed(self):
        self.nav_to_timed.emit()
