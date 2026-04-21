from PyQt6.QtWidgets import QMainWindow, QStackedWidget

from home_page import HomePage
from midi_display_page import MidiDisplayPage

_HOME_SIZE = (420, 280)
_MIDI_DISPLAY_SIZE = (420, 220)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MIDI Piano Teacher")

        self._stack = QStackedWidget()
        self.setCentralWidget(self._stack)

        self._home = HomePage()
        self._midi_display = MidiDisplayPage()

        self._stack.addWidget(self._home)
        self._stack.addWidget(self._midi_display)

        self._home.nav_to_midi_display.connect(self._go_to_midi_display)
        self._midi_display.nav_to_home.connect(self._go_to_home)

        self._go_to_home()

    def _go_to_home(self):
        self._stack.setCurrentWidget(self._home)
        self.setFixedSize(*_HOME_SIZE)

    def _go_to_midi_display(self):
        self._stack.setCurrentWidget(self._midi_display)
        self.setFixedSize(*_MIDI_DISPLAY_SIZE)
        self._midi_display.activate()
