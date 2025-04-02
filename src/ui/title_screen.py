import sys
from PyQt5.QtWidgets import QWidget, QApplication, QLabel, QVBoxLayout
from PyQt5.QtGui import QPixmap, QKeyEvent
from PyQt5.QtCore import Qt, QTimer, QSize, pyqtSignal

class TitleScreen(QWidget):
    # Add a custom signal to indicate the title screen should be closed
    transition_to_main = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        
        # Set window to be frameless (no title bar)
        self.setWindowFlags(Qt.FramelessWindowHint)
        
        # Set up the layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Load and display the title image
        title_image = QLabel()
        pixmap = QPixmap("src/ui/assets/demotitle.png")
        if not pixmap.isNull():
            title_image.setPixmap(pixmap)
        else:
            # Fallback if image is not found
            title_image.setText("Title Screen (Image Not Found)")
            title_image.setStyleSheet("font-size: 24px; color: white;")
            self.setStyleSheet("background-color: #2A2A2A;")
        
        # Center the image in the layout
        title_image.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_image)
        
        # Set the window size to match the image size
        self.setFixedSize(pixmap.width(), pixmap.height())
        
        # Center the window on the screen
        self.center_on_screen()
    
    def center_on_screen(self):
        """Center the window on the screen"""
        screen_geometry = QApplication.desktop().screenGeometry()
        window_geometry = self.geometry()
        
        x = (screen_geometry.width() - window_geometry.width()) // 2
        y = (screen_geometry.height() - window_geometry.height()) // 2
        
        self.move(x, y)
    
    def keyPressEvent(self, event: QKeyEvent):
        """Handle key press events"""
        # Close the title screen when Enter is pressed
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            # Emit signal before closing
            self.transition_to_main.emit()
            self.close()
        # Also close on Escape or Space for user convenience
        elif event.key() in (Qt.Key_Escape, Qt.Key_Space):
            # Emit signal before closing
            self.transition_to_main.emit()
            self.close()
        else:
            super().keyPressEvent(event)

# For testing the title screen independently
if __name__ == "__main__":
    app = QApplication(sys.argv)
    title = TitleScreen()
    title.show()
    sys.exit(app.exec_()) 