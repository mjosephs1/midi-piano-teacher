#!/usr/bin/env python3
import sys

try:
    import mido  # noqa: F401
except ImportError:
    print("Missing dependency: pip install mido python-rtmidi")
    sys.exit(1)

try:
    from PyQt6.QtWidgets import QApplication
except ImportError:
    print("Missing dependency: pip install PyQt6")
    sys.exit(1)

from main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("MIDI Piano Teacher")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
