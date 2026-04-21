from PyQt6.QtWidgets import QMainWindow, QStackedWidget

from home_page import HomePage
from midi_display_page import MidiDisplayPage
from find_chord_page import FindChordPage

_HOME_SIZE = (420, 340)
_MIDI_DISPLAY_SIZE = (420, 220)
_FIND_CHORD_SIZE = (620, 440)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MIDI Piano Teacher")

        self._stack = QStackedWidget()
        self.setCentralWidget(self._stack)

        self._home = HomePage()
        self._midi_display = MidiDisplayPage()
        self._find_chord = FindChordPage()

        self._stack.addWidget(self._home)
        self._stack.addWidget(self._midi_display)
        self._stack.addWidget(self._find_chord)

        self._home.nav_to_midi_display.connect(self._go_to_midi_display)
        self._home.nav_to_find_chord.connect(self._go_to_find_chord)
        self._midi_display.nav_to_home.connect(self._go_to_home)
        self._find_chord.nav_to_home.connect(self._go_to_home)

        self._go_to_home()

    def _go_to_home(self):
        self._midi_display.deactivate()
        self._find_chord.deactivate()
        self._stack.setCurrentWidget(self._home)
        self.setFixedSize(*_HOME_SIZE)

    def _go_to_midi_display(self):
        self._stack.setCurrentWidget(self._midi_display)
        self.setFixedSize(*_MIDI_DISPLAY_SIZE)
        self._midi_display.activate()

    def _go_to_find_chord(self):
        self._stack.setCurrentWidget(self._find_chord)
        self.setFixedSize(*_FIND_CHORD_SIZE)
        self._find_chord.activate()
