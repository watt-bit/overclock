import sys
import os
import gc
# OVERCLOCK Watt-Bit Sandbox]

import matplotlib
matplotlib.use('Qt5Agg')
matplotlib.rcParams['interactive'] = False

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QObject, Qt, QTimer
from src.ui.main_window import PowerSystemSimulator
from src.ui.title_screen import TitleScreen
from src.ui.wbr_title_screen import WBRTitleScreen
from src.ui.augur_title_screen import AugurTitleScreen
from src.ui.startup_sequence import StartupSequence
from src.utils.resource import resource_path

# Create a dedicated class to manage application lifecycle and cleanup
class AppManager(QObject):
    # Class variables to avoid circular references
    main_window = None
    title_screen = None
    wbr_title_screen = None
    augur_title_screen = None
    startup_sequence = None
    
    def __init__(self):
        super().__init__()
        self._cleanup_done = False
        self._is_quitting = False
        self._pending_load_file = None
        self._load_timer = None
        
    def clean_up_application(self):
        """Safely clean up all application resources"""
        # Only run cleanup once
        if self._cleanup_done:
            return
            
        self._is_quitting = True
        self._cleanup_done = True
        
        print("Cleaning up application resources...")
        
        # Disconnect signal handlers first to prevent callbacks during cleanup
        self._disconnect_signals()
        
        # Clean up matplotlib resources
        try:
            matplotlib.pyplot.close('all')
        except Exception:
            pass
        
        # Clean up title screens - stop timers first, then hide screens
        self._cleanup_screens()
        
        # Clean up main window resources
        self._cleanup_main_window()
        
        # Clean up startup sequence
        self.startup_sequence = None
        
        # Clean up load timer if it exists
        if self._load_timer and self._load_timer.isActive():
            self._load_timer.stop()
        self._load_timer = None
        
        # Force garbage collection to clean up any lingering objects
        gc.collect()
            
        print("Application cleanup complete.")
    
    def _disconnect_signals(self):
        """Disconnect all signal connections to prevent callbacks during shutdown"""
        try:
            if self.title_screen:
                try:
                    self.title_screen.transition_to_main.disconnect()
                except TypeError:
                    pass
                try:
                    self.title_screen.transition_to_main_with_file.disconnect()
                except TypeError:
                    pass
                    
            if self.augur_title_screen:
                try:
                    self.augur_title_screen.transition_to_next.disconnect()
                except TypeError:
                    pass
                    
            if self.wbr_title_screen:
                try:
                    self.wbr_title_screen.transition_to_next.disconnect()
                except TypeError:
                    pass
        except Exception:
            pass
    
    def _cleanup_screens(self):
        """Clean up all title screens"""
        # Process each screen in reverse order of appearance
        for screen_name in ['title_screen', 'wbr_title_screen', 'augur_title_screen']:
            try:
                screen = getattr(self, screen_name)
                if screen:
                    # Stop timer if exists
                    if hasattr(screen, 'timer') and screen.timer and screen.timer.isActive():
                        screen.timer.stop()
                        # Disconnect timer signals
                        try:
                            screen.timer.timeout.disconnect()
                        except TypeError:
                            pass
                    
                    # Block all signals to prevent further event processing
                    screen.blockSignals(True)
                    # Hide the screen
                    screen.hide()
                    # Set parent to None to break parent-child relationships
                    screen.setParent(None)
            except Exception:
                pass
                
            # Clear the reference
            setattr(self, screen_name, None)
    
    def _cleanup_main_window(self):
        """Clean up the main window and its resources"""
        try:
            if self.main_window:
                # Clean up autocomplete manager
                if hasattr(self.main_window, 'autocomplete_manager') and self.main_window.autocomplete_manager:
                    try:
                        self.main_window.autocomplete_manager.cleanup()
                    except Exception:
                        pass
                
                # Stop all timers
                timer_names = [
                    'sim_timer', 'cursor_timer', 'scrub_timer', 'autocomplete_timer'
                ]
                
                for timer_name in timer_names:
                    try:
                        timer = getattr(self.main_window, timer_name, None)
                        if timer and timer.isActive():
                            timer.stop()
                            # Disconnect timer signals
                            try:
                                timer.timeout.disconnect()
                            except TypeError:
                                pass
                    except Exception:
                        pass
                
                # Block all signals
                self.main_window.blockSignals(True)
                
                # Hide the window
                self.main_window.hide()
                
                # Set parent to None
                self.main_window.setParent(None)
                
                # Clear the reference
                self.main_window = None
        except Exception:
            pass

    def load_pending_file(self):
        """Load the pending file after the main window is fully initialized"""
        if self._pending_load_file and self.main_window:
            filename = self._pending_load_file
            self._pending_load_file = None
            self.main_window.model_manager.load_scenario_from_file(filename)
            # Ensure CAPEX display is updated
            self.main_window.update_capex_display()


def main():
    # Create application with disabled quit on last window closed
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    # Set application icon
    app_icon = QIcon(resource_path("src/ui/assets/appicon.png"))
    app.setWindowIcon(app_icon)
    
    # Create app manager to handle cleanup
    app_manager = AppManager()
    
    # Create the main window but don't show it yet
    app_manager.main_window = PowerSystemSimulator()
    
    # Create the original title screen but don't show it yet
    app_manager.title_screen = TitleScreen()
    
    # Connect the title screen's transition signal to show the main window
    # with a custom handler to ensure welcome text is centered
    def handle_new_project_transition():
        # Show the main window first
        app_manager.main_window.show()
        # Initialize the startup sequence and store it in app_manager
        app_manager.startup_sequence = StartupSequence(app_manager.main_window)
        # Use a timer to ensure the window is fully initialized before running startup sequence
        QTimer.singleShot(100, app_manager.startup_sequence.run)
    
    app_manager.title_screen.transition_to_main.connect(handle_new_project_transition)
    
    # Connect the title screen's transition signal with file to load and show the main window
    def handle_load_transition(filename):
        # Store the filename for loading after the window is shown and initialized
        app_manager._pending_load_file = filename
        # Show the main window first
        app_manager.main_window.show()
        # Create a timer to ensure the window is fully initialized before loading
        app_manager._load_timer = QTimer()
        app_manager._load_timer.setSingleShot(True)
        app_manager._load_timer.timeout.connect(app_manager.load_pending_file)
        app_manager._load_timer.start(50)
    
    app_manager.title_screen.transition_to_main_with_file.connect(handle_load_transition)
    
    # Create the Augur title screen but don't show it yet
    app_manager.augur_title_screen = AugurTitleScreen()
    
    # Create the WBR title screen
    app_manager.wbr_title_screen = WBRTitleScreen()
    
    # Connect the Augur title screen's transition signal to show the WBR title screen
    app_manager.augur_title_screen.transition_to_next.connect(app_manager.wbr_title_screen.show)
    
    # Connect the WBR title screen's transition signal to show the original title screen
    app_manager.wbr_title_screen.transition_to_next.connect(app_manager.title_screen.show)
    
    # Connect cleanup to application quit - use Qt.DirectConnection to ensure it runs immediately
    app.aboutToQuit.connect(app_manager.clean_up_application, Qt.ConnectionType.DirectConnection)
    
    # Show the Augur title screen first
    app_manager.augur_title_screen.show()
    
    # Run the application and capture the result
    result = app.exec()
    
    # Force a final garbage collection
    gc.collect()
    
    # Return the result code
    return result

if __name__ == "__main__":
    sys.exit(main()) 