# ==========================================================
# main_v2.py — Launch SuperQin v2
# ==========================================================

import sys
from PyQt6.QtWidgets import QApplication
from gui_main_v2 import MainWindow

def main():
    app = QApplication(sys.argv)
    
    # Set application info
    app.setApplicationName("SuperQin v2")
    app.setOrganizationName("SuperQin")
    app.setApplicationVersion("2.0.0")
    
    w = MainWindow()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
