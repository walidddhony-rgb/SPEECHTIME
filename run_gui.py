#!/usr/bin/env python3
"""
Launch SpeechScribe GUI - Professional Version.
"""

import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPalette, QColor
from gui.main_window import SpeechScribeMainWindow


def main():
    """Main entry point."""
    app = QApplication(sys.argv)
    
    # Set application info
    app.setApplicationName("SpeechScribe")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("SpeechScribe Team")
    
    # Set application style
    app.setStyle('Fusion')
    
    # Set palette
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(255, 255, 255))
    palette.setColor(QPalette.WindowText, QColor(0, 0, 0))
    app.setPalette(palette)
    
    # Create and show main window
    window = SpeechScribeMainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()