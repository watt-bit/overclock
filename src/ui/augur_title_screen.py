import sys
from PyQt5.QtWidgets import QWidget, QApplication, QLabel, QVBoxLayout
from PyQt5.QtGui import QPixmap, QKeyEvent
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from src.utils.resource import resource_path

class AugurTitleScreen(QWidget):
    # Add a custom signal to indicate the Augur title screen should transition to the next screen
    transition_to_next = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        
        # Set window to be frameless (no title bar)
        self.setWindowFlags(Qt.FramelessWindowHint)
        
        # Set up the layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Load and display the Augur title image
        title_image = QLabel()
        pixmap = QPixmap(resource_path("src/ui/assets/augurtitle2.png"))
        if not pixmap.isNull():
            title_image.setPixmap(pixmap)
        else:
            # Fallback if image is not found
            title_image.setText("Augur Title Screen (Image Not Found)")
            title_image.setStyleSheet("font-size: 24px; color: white;")
            self.setStyleSheet("background-color: #2A2A2A;")
        
        # Center the image in the layout
        title_image.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_image)
        
        # Set the window size to match the image size
        self.setFixedSize(pixmap.width(), pixmap.height())
        
        # Center the window on the screen
        self.center_on_screen()
        
        # Setup auto-transition timer (3 seconds)
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(5000)  # 5 seconds
        self.timer.timeout.connect(self.auto_transition)
    
    def showEvent(self, event):
        """Start the timer when the widget is shown"""
        super().showEvent(event)
        self.timer.start()
    
    def auto_transition(self):
        """Automatically transition to the next screen after timer expires"""
        self.transition_to_next.emit()
        self.close()
    
    def center_on_screen(self):
        """Center the window on the screen"""
        screen_geometry = QApplication.desktop().screenGeometry()
        window_geometry = self.geometry()
        
        x = (screen_geometry.width() - window_geometry.width()) // 2
        y = (screen_geometry.height() - window_geometry.height()) // 2
        
        self.move(x, y)
    
    def keyPressEvent(self, event: QKeyEvent):
        """Handle key press events"""
        # Transition to the next screen when Enter is pressed
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            # Emit signal before closing
            self.timer.stop()  # Stop the timer if a key is pressed
            self.transition_to_next.emit()
            self.close()
        # Also transition on Escape or Space for user convenience
        elif event.key() in (Qt.Key_Escape, Qt.Key_Space):
            # Emit signal before closing
            self.timer.stop()  # Stop the timer if a key is pressed
            self.transition_to_next.emit()
            self.close()
        else:
            super().keyPressEvent(event)

# For testing the Augur title screen independently
if __name__ == "__main__":
    app = QApplication(sys.argv)
    title = AugurTitleScreen()
    title.show()
    sys.exit(app.exec_()) 