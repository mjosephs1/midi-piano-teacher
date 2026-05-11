from PyQt6.QtWidgets import QMainWindow, QStackedWidget

from home_page import HomePage
from midi_display_page import MidiDisplayPage
from find_chord_page import FindChordPage
from find_chord_mode_page import FindChordModePage
from find_chord_timed_page import FindChordTimedPage
from high_scores_page import HighScoresPage

_HOME_SIZE = (420, 390)
_MIDI_DISPLAY_SIZE = (420, 220)
_FIND_CHORD_MODE_SIZE = (620, 450)
_FIND_CHORD_SIZE = (620, 440)
_FIND_CHORD_TIMED_SIZE = (620, 440)
_HIGH_SCORES_SIZE = (620, 560)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MIDI Piano Teacher")

        self._stack = QStackedWidget()
        self.setCentralWidget(self._stack)

        self._home = HomePage()
        self._midi_display = MidiDisplayPage()
        self._find_chord = FindChordPage()
        self._find_chord_mode = FindChordModePage()
        self._find_chord_timed = FindChordTimedPage()
        self._high_scores = HighScoresPage()

        self._stack.addWidget(self._home)
        self._stack.addWidget(self._midi_display)
        self._stack.addWidget(self._find_chord)
        self._stack.addWidget(self._find_chord_mode)
        self._stack.addWidget(self._find_chord_timed)
        self._stack.addWidget(self._high_scores)

        self._home.nav_to_midi_display.connect(self._go_to_midi_display)
        self._home.nav_to_find_chord.connect(self._go_to_find_chord_mode)
        self._home.nav_to_high_scores.connect(self._go_to_high_scores)
        self._midi_display.nav_to_home.connect(self._go_to_home)
        self._find_chord_mode.nav_to_home.connect(self._go_to_home)
        self._find_chord_mode.nav_to_infinite.connect(self._go_to_find_chord)
        self._find_chord_mode.nav_to_timed.connect(self._go_to_find_chord_timed)
        self._find_chord.nav_to_mode_select.connect(self._go_to_find_chord_mode)
        self._find_chord_timed.nav_to_mode_select.connect(self._go_to_find_chord_mode)
        self._high_scores.nav_to_home.connect(self._go_to_home)

        self._go_to_home()

    def _go_to_home(self):
        self._midi_display.deactivate()
        self._find_chord.deactivate()
        self._find_chord_timed.deactivate()
        self._stack.setCurrentWidget(self._home)
        self.setFixedSize(*_HOME_SIZE)

    def _go_to_midi_display(self):
        self._stack.setCurrentWidget(self._midi_display)
        self.setFixedSize(*_MIDI_DISPLAY_SIZE)
        self._midi_display.activate()

    def _go_to_find_chord_mode(self):
        self._find_chord.deactivate()
        self._find_chord_timed.deactivate()
        self._stack.setCurrentWidget(self._find_chord_mode)
        self.setFixedSize(*_FIND_CHORD_MODE_SIZE)

    def _go_to_find_chord(self):
        self._stack.setCurrentWidget(self._find_chord)
        self.setFixedSize(*_FIND_CHORD_SIZE)
        self._find_chord.activate(self._find_chord_mode.group_enabled, self._find_chord_mode.sharps_mode)

    def _go_to_find_chord_timed(self):
        self._stack.setCurrentWidget(self._find_chord_timed)
        self.setFixedSize(*_FIND_CHORD_TIMED_SIZE)
        self._find_chord_timed.activate(self._find_chord_mode.group_enabled, self._find_chord_mode.sharps_mode)

    def _go_to_high_scores(self):
        self._stack.setCurrentWidget(self._high_scores)
        self.setFixedSize(*_HIGH_SCORES_SIZE)
