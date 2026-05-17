from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QScrollArea, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

import stats_manager
from find_chord_page import _toggle_style


class StatsPage(QWidget):
    nav_to_home = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._sort_by = "time"
        self._hand_key = "right"
        self._hand_buttons = {}
        self._rows_layout = None
        self._rows_widget = None
        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet("background-color: #1e1e1e;")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 24, 30, 24)
        main_layout.setSpacing(0)

        back_row = QHBoxLayout()
        back_row.setSpacing(0)
        back_btn = QPushButton("← Back")
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
        back_btn.setFixedHeight(28)
        back_btn.setFont(QFont("Helvetica", 12))
        back_btn.clicked.connect(self._on_back)
        back_row.addWidget(back_btn)
        back_row.addStretch()
        main_layout.addLayout(back_row)

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("color: #333333;")
        main_layout.addWidget(divider)

        title = QLabel("Stats")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #ffffff; background-color: transparent;")
        title.setFont(QFont("Helvetica", 20, QFont.Weight.Bold))
        main_layout.addWidget(title)

        main_layout.addSpacing(12)

        controls_row = QHBoxLayout()
        controls_row.setSpacing(12)

        sort_label = QLabel("Sort by:")
        sort_label.setStyleSheet("color: #ffffff; background-color: transparent;")
        sort_label.setFont(QFont("Helvetica", 12))
        controls_row.addWidget(sort_label)

        self._sort_combo = QComboBox()
        self._sort_combo.addItem("Time", "time")
        self._sort_combo.addItem("Errors", "errors")
        self._sort_combo.setStyleSheet("""
            QComboBox {
                background-color: #2a2a2a;
                color: #ffffff;
                border: 1px solid #444444;
                border-radius: 4px;
                padding: 4px 8px;
            }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView {
                background-color: #2a2a2a;
                color: #ffffff;
                selection-background-color: #3a7bd5;
            }
        """)
        self._sort_combo.setFixedWidth(120)
        self._sort_combo.currentIndexChanged.connect(self._on_sort_changed)
        controls_row.addWidget(self._sort_combo)

        controls_row.addStretch()

        for label, hand in [("✋", "left"), ("🤚", "right"), ("✋🤚", "both")]:
            btn = QPushButton(label)
            btn.setCheckable(True)
            checked = hand == self._hand_key
            btn.setChecked(checked)
            btn.setFixedHeight(26)
            btn.setFont(QFont("Helvetica", 14))
            btn.setStyleSheet(_toggle_style(checked=checked))
            btn.toggled.connect(lambda checked, h=hand: self._on_hand_toggled(h, checked))
            controls_row.addWidget(btn)
            self._hand_buttons[hand] = btn

        main_layout.addLayout(controls_row)

        main_layout.addSpacing(8)

        divider2 = QFrame()
        divider2.setFrameShape(QFrame.Shape.HLine)
        divider2.setStyleSheet("color: #333333;")
        main_layout.addWidget(divider2)

        main_layout.addSpacing(8)

        header_row = QHBoxLayout()
        header_row.setSpacing(0)

        headers = [
            ("From → To", 240),
            ("Avg Time", 90),
            ("Avg Errors", 90),
            ("Count", 60),
        ]
        for text, width in headers:
            label = QLabel(text)
            label.setFixedWidth(width)
            if text == "From → To":
                label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            else:
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("color: #666666; background-color: transparent;")
            label.setFont(QFont("Helvetica", 11, QFont.Weight.Bold))
            header_row.addWidget(label)
        header_row.addStretch()
        main_layout.addLayout(header_row)

        divider3 = QFrame()
        divider3.setFrameShape(QFrame.Shape.HLine)
        divider3.setStyleSheet("color: #333333;")
        main_layout.addWidget(divider3)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollArea > QWidget > QWidget {
                background-color: #1e1e1e;
            }
        """)

        self._rows_widget = QWidget()
        self._rows_widget.setStyleSheet("background-color: #1e1e1e;")
        self._rows_layout = QVBoxLayout(self._rows_widget)
        self._rows_layout.setContentsMargins(0, 0, 0, 0)
        self._rows_layout.setSpacing(0)

        scroll_area.setWidget(self._rows_widget)
        main_layout.addWidget(scroll_area)

        main_layout.addStretch()

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _on_hand_toggled(self, hand: str, checked: bool):
        if not checked:
            return
        self._hand_key = hand
        for h, btn in self._hand_buttons.items():
            btn.blockSignals(True)
            btn.setChecked(h == hand)
            btn.setStyleSheet(_toggle_style(checked=(h == hand)))
            btn.blockSignals(False)
        self._refresh()

    def _on_sort_changed(self):
        self._sort_by = self._sort_combo.currentData()
        self._refresh()

    def _refresh(self):
        stats = stats_manager.get_all_stats(self._hand_key)

        if self._sort_by == "time":
            stats.sort(key=lambda x: x["time"], reverse=True)
        else:
            stats.sort(key=lambda x: x["errors"], reverse=True)

        while self._rows_layout.count():
            item = self._rows_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

        if not stats:
            empty_label = QLabel("No stats recorded yet.")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_label.setStyleSheet("color: #666666; background-color: transparent;")
            empty_label.setFont(QFont("Helvetica", 12))
            self._rows_layout.addWidget(empty_label)
            self._rows_layout.addStretch()
            return

        for stat in stats:
            row = QHBoxLayout()
            row.setSpacing(0)
            row.setContentsMargins(0, 6, 0, 6)

            transition_label = QLabel(f"{stat['from_chord']}  →  {stat['to_chord']}")
            transition_label.setFixedWidth(240)
            transition_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            transition_label.setStyleSheet("color: #ffffff; background-color: transparent;")
            transition_label.setFont(QFont("Helvetica", 12))
            row.addWidget(transition_label)

            time_label = QLabel(f"{stat['time']:.3f}s")
            time_label.setFixedWidth(90)
            time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            time_label.setStyleSheet("color: #aaaaaa; background-color: transparent;")
            time_label.setFont(QFont("Helvetica", 12))
            row.addWidget(time_label)

            errors_label = QLabel(f"{stat['errors']:.2f}")
            errors_label.setFixedWidth(90)
            errors_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            errors_label.setStyleSheet("color: #aaaaaa; background-color: transparent;")
            errors_label.setFont(QFont("Helvetica", 12))
            row.addWidget(errors_label)

            count_label = QLabel(str(stat["count"]))
            count_label.setFixedWidth(60)
            count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            count_label.setStyleSheet("color: #666666; background-color: transparent;")
            count_label.setFont(QFont("Helvetica", 11))
            row.addWidget(count_label)

            row.addStretch()
            self._rows_layout.addLayout(row)

    def showEvent(self, event):
        super().showEvent(event)
        self._refresh()

    def _on_back(self):
        self.nav_to_home.emit()
