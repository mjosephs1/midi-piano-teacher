from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QButtonGroup
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont

from find_chord_page import CHORD_GROUPS, _toggle_style
import settings_manager


class ChordSettingsWidget(QWidget):
    settings_changed = pyqtSignal()

    def showEvent(self, event):
        super().showEvent(event)
        self._reload_settings_from_disk()

    def _reload_settings_from_disk(self):
        saved = settings_manager.load_chord_settings(list(CHORD_GROUPS.keys()))
        self._group_enabled = saved["group_enabled"]
        self._sharps_mode = saved["sharps_mode"]

        for group_name, btn in self._group_buttons.items():
            btn.blockSignals(True)
            btn.setChecked(self._group_enabled[group_name])
            btn.blockSignals(False)
            btn.setStyleSheet(_toggle_style(checked=self._group_enabled[group_name]))

        for mode, btn in self._sharps_buttons.items():
            btn.blockSignals(True)
            btn.setChecked(self._sharps_mode == mode)
            btn.blockSignals(False)
            btn.setStyleSheet(_toggle_style(checked=self._sharps_mode == mode))

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: transparent;")
        saved = settings_manager.load_chord_settings(list(CHORD_GROUPS.keys()))
        self._group_enabled = saved["group_enabled"]
        self._group_buttons: dict[str, QPushButton] = {}
        self._sharps_mode = saved["sharps_mode"]
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        group_names = list(CHORD_GROUPS.keys())
        for row_names in [group_names[:5], group_names[5:]]:
            row = QHBoxLayout()
            row.setSpacing(6)
            row.setAlignment(Qt.AlignmentFlag.AlignCenter)
            for group_name in row_names:
                btn = QPushButton(group_name)
                btn.setCheckable(True)
                initial = self._group_enabled.get(group_name, True)
                btn.blockSignals(True)
                btn.setChecked(initial)
                btn.blockSignals(False)
                btn.setFixedHeight(26)
                btn.setFont(QFont("Helvetica", 11))
                btn.setStyleSheet(_toggle_style(checked=initial))
                btn.toggled.connect(lambda checked, n=group_name: self._on_group_toggled(n, checked))
                row.addWidget(btn)
                self._group_buttons[group_name] = btn
            layout.addLayout(row)
            layout.addSpacing(4)

        layout.addSpacing(4)
        sharps_row = QHBoxLayout()
        sharps_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sharps_row.setSpacing(6)

        self._sharps_btn_group = QButtonGroup()
        self._sharps_btn_group.setExclusive(True)

        modes = [("No Sharps", "exclude"), ("With Sharps", "include"), ("Sharps Only", "only")]
        self._sharps_buttons: dict[str, QPushButton] = {}

        for button_id, (label, mode) in enumerate(modes):
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.blockSignals(True)
            btn.setChecked(self._sharps_mode == mode)
            btn.blockSignals(False)
            btn.setFixedHeight(26)
            btn.setFont(QFont("Helvetica", 11))
            btn.setStyleSheet(_toggle_style(checked=self._sharps_mode == mode))
            btn.toggled.connect(lambda checked, m=mode: self._on_sharps_mode_selected(m, checked))
            self._sharps_btn_group.addButton(btn, button_id)
            self._sharps_buttons[mode] = btn
            sharps_row.addWidget(btn)

        layout.addLayout(sharps_row)

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
        settings_manager.save_chord_settings(self._group_enabled, self._sharps_mode)
        self.settings_changed.emit()

    def _on_sharps_mode_selected(self, mode: str, checked: bool) -> None:
        if not checked:
            return
        self._sharps_mode = mode
        for m, btn in self._sharps_buttons.items():
            btn.setStyleSheet(_toggle_style(checked=(m == mode)))
        settings_manager.save_chord_settings(self._group_enabled, self._sharps_mode)
        self.settings_changed.emit()

    @property
    def group_enabled(self) -> dict[str, bool]:
        return self._group_enabled.copy()

    @property
    def sharps_mode(self) -> str:
        return self._sharps_mode
