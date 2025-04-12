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
from src.ui.wbr_title_screen import WBRTitleScreen
from src.ui.augur_title_screen import AugurTitleScreen

def main():
    app = QApplication(sys.argv)
    
    # Set application icon
    app_icon = QIcon("src/ui/assets/appicon.png")
    app.setWindowIcon(app_icon)
    
    # Create the main window but don't show it yet
    main_window = PowerSystemSimulator()
    
    # Create the original title screen but don't show it yet
    title_screen = TitleScreen()
    
    # Connect the title screen's transition signal to show the main window
    title_screen.transition_to_main.connect(main_window.show)
    
    # Connect the title screen's transition signal with file to load and show the main window
    def handle_load_transition(filename):
        main_window.show()
        main_window.model_manager.load_scenario_from_file(filename)
    
    title_screen.transition_to_main_with_file.connect(handle_load_transition)
    
    # Create the Augur title screen but don't show it yet
    augur_title_screen = AugurTitleScreen()
    
    # Create the WBR title screen
    wbr_title_screen = WBRTitleScreen()
    
    # Connect the Augur title screen's transition signal to show the WBR title screen
    augur_title_screen.transition_to_next.connect(wbr_title_screen.show)
    
    # Connect the WBR title screen's transition signal to show the original title screen
    wbr_title_screen.transition_to_next.connect(title_screen.show)
    
    # Show the Augur title screen first
    augur_title_screen.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 