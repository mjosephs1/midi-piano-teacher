from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class HomePage(QWidget):
    nav_to_midi_display = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet("background-color: #1e1e1e;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 50, 40, 50)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("MIDI Piano Teacher")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #ffffff; background-color: transparent;")
        title.setFont(QFont("Helvetica", 28, QFont.Weight.Bold))
        layout.addWidget(title)

        layout.addSpacing(40)

        btn = QPushButton("MIDI Display")
        btn.setFont(QFont("Helvetica", 15))
        btn.setFixedHeight(44)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #3a7bd5;
                color: #ffffff;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #4a8be5;
            }
            QPushButton:pressed {
                background-color: #2a6bc5;
            }
        """)
        btn.clicked.connect(self.nav_to_midi_display)
        layout.addWidget(btn)
