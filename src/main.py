import sys
import os
# OVERCLOCK Watt-Bit Sandbox from Augur | https://augurvc.com
# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib
matplotlib.use('Qt5Agg')
matplotlib.rcParams['interactive'] = False

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from src.ui.main_window import PowerSystemSimulator
from src.ui.title_screen import TitleScreen

def main():
    app = QApplication(sys.argv)
    
    # Set application icon
    app_icon = QIcon("src/ui/assets/appicon.png")
    app.setWindowIcon(app_icon)
    
    # Create the main window but don't show it yet
    main_window = PowerSystemSimulator()
    
    # Create the title screen first
    title_screen = TitleScreen()
    
    # Connect the title screen's transition signal to show the main window
    title_screen.transition_to_main.connect(main_window.show)
    
    # Show the title screen
    title_screen.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 