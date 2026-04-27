from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont

from find_chord_page import CHORD_GROUPS, _toggle_style
from midi_display import NOTE_NAMES


class FindChordModePage(QWidget):
    nav_to_home = pyqtSignal()
    nav_to_infinite = pyqtSignal()
    nav_to_timed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._group_enabled = {name: True for name in CHORD_GROUPS}
        self._group_buttons: dict[str, QPushButton] = {}
        self._sharps_enabled = True
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

        # Chord group toggles
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

        layout.addSpacing(4)
        sharps_row = QHBoxLayout()
        sharps_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._sharps_btn = QPushButton("Sharps")
        self._sharps_btn.setCheckable(True)
        self._sharps_btn.setChecked(True)
        self._sharps_btn.setFixedHeight(26)
        self._sharps_btn.setFont(QFont("Helvetica", 11))
        self._sharps_btn.setStyleSheet(_toggle_style(checked=True))
        self._sharps_btn.toggled.connect(self._on_sharps_toggled)
        sharps_row.addWidget(self._sharps_btn)
        layout.addLayout(sharps_row)

        layout.addStretch()

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

    def _on_sharps_toggled(self, checked: bool) -> None:
        self._sharps_enabled = checked
        self._sharps_btn.setStyleSheet(_toggle_style(checked=checked))

    @property
    def group_enabled(self) -> dict[str, bool]:
        return self._group_enabled.copy()

    @property
    def sharps_enabled(self) -> bool:
        return self._sharps_enabled

    def _on_back(self):
        self.nav_to_home.emit()

    def _on_infinite(self):
        self.nav_to_infinite.emit()

    def _on_timed(self):
        self.nav_to_timed.emit()
