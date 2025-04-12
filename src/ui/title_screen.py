import sys
from PyQt5.QtWidgets import QWidget, QApplication, QLabel, QVBoxLayout, QPushButton, QHBoxLayout, QFileDialog
from PyQt5.QtGui import QPixmap, QKeyEvent, QFont, QCursor
from PyQt5.QtCore import Qt, QTimer, QSize, pyqtSignal
import json

class TitleScreen(QWidget):
    # Add a custom signal to indicate the title screen should be closed
    transition_to_main = pyqtSignal()
    transition_to_main_with_file = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        
        # Set window to be frameless (no title bar)
        self.setWindowFlags(Qt.FramelessWindowHint)
        
        # Set up the layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Load and display the title image
        title_image = QLabel()
        pixmap = QPixmap("src/ui/assets/demotitle6.png")
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
        
        # Add Exit button
        self.create_exit_button()
        
        # Add New Project button
        self.create_new_project_button()
        
        # Add Load Project button
        self.create_load_project_button()
        
        # Center the window on the screen
        self.center_on_screen()
    
    def create_exit_button(self):
        """Create and add the Exit button"""
        # Create button
        exit_btn = QPushButton("❌", self)
        exit_btn.setFixedSize(30, 30)  # Square button
        
        # Set font size to 18pt
        font = QFont()
        font.setPointSize(18)
        exit_btn.setFont(font)
        
        # Style the button (same transparent style as other buttons)
        exit_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #CCCCCC;
                border-radius: 3px;
                color: #CCCCCC;
            }
            QPushButton:hover {
                background-color: rgba(200, 240, 255, 20);
                border: 1px solid #D8F0FF;
                color: #D8F0FF;
            }
        """)
        
        # Position button at (5,5) in the top left corner
        exit_btn.move(5, 5)
        
        # Connect button click to exit application
        exit_btn.clicked.connect(QApplication.quit)
        
        # Set cursor to hand when hovering over button
        exit_btn.setCursor(QCursor(Qt.PointingHandCursor))
    
    def create_new_project_button(self):
        """Create and add the New Project button"""
        # Create button
        new_project_btn = QPushButton(self)
        new_project_btn.setFixedSize(120, 30)  # Width to accommodate text, height 30px
        
        # Create layout for button contents
        btn_layout = QHBoxLayout(new_project_btn)
        btn_layout.setContentsMargins(5, 5, 5, 5)
        btn_layout.setSpacing(5)
        
        # Add image to button
        img_label = QLabel()
        pixmap = QPixmap("src/ui/assets/newproject.png")
        if not pixmap.isNull():
            pixmap = pixmap.scaled(20, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            img_label.setPixmap(pixmap)
        else:
            img_label.setText("+")
        
        # Add text to button
        text_label = QLabel("New Project")
        text_label.setStyleSheet("color: #CCCCCC;")  # Light gray color for text
        
        # Add to layout
        btn_layout.addWidget(img_label)
        btn_layout.addWidget(text_label)
        btn_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        # Style the button
        new_project_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #CCCCCC;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: rgba(200, 240, 255, 20);
                border: 1px solid #D8F0FF;
            }
            QPushButton:hover QLabel {
                color: #D8F0FF;
            }
        """)
        
        # Position button
        window_width = self.width()
        window_height = self.height()
        btn_x = (window_width - new_project_btn.width()) // 2 - 90
        btn_y = (window_height - new_project_btn.height()) // 2 + 90 
        new_project_btn.move(btn_x, btn_y)
        
        # Connect button click to transition
        new_project_btn.clicked.connect(self.handle_new_project_click)
        
        # Set cursor to hand when hovering over button
        new_project_btn.setCursor(QCursor(Qt.PointingHandCursor))
    
    def create_load_project_button(self):
        """Create and add the Load Project button"""
        # Create button
        load_project_btn = QPushButton(self)
        load_project_btn.setFixedSize(120, 30)  # Width to accommodate text, height 30px
        
        # Create layout for button contents
        btn_layout = QHBoxLayout(load_project_btn)
        btn_layout.setContentsMargins(5, 5, 5, 5)
        btn_layout.setSpacing(5)
        
        # Add image to button
        img_label = QLabel()
        pixmap = QPixmap("src/ui/assets/loadproject.png")
        if not pixmap.isNull():
            pixmap = pixmap.scaled(20, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            img_label.setPixmap(pixmap)
        else:
            img_label.setText("📂")
        
        # Add text to button
        text_label = QLabel("Load Project")
        text_label.setStyleSheet("color: #CCCCCC;")  # Light gray color for text
        
        # Add to layout
        btn_layout.addWidget(img_label)
        btn_layout.addWidget(text_label)
        btn_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        # Style the button (same as New Project button)
        load_project_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #CCCCCC;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: rgba(200, 240, 255, 20);
                border: 1px solid #D8F0FF;
            }
            QPushButton:hover QLabel {
                color: #D8F0FF;
            }
        """)
        
        # Position button (same y as New Project but x+40 instead of x-80)
        window_width = self.width()
        window_height = self.height()
        btn_x = (window_width - load_project_btn.width()) // 2 + 50
        btn_y = (window_height - load_project_btn.height()) // 2 + 90
        load_project_btn.move(btn_x, btn_y)
        
        # Connect button click to load handler
        load_project_btn.clicked.connect(self.handle_load_project_click)
        
        # Set cursor to hand when hovering over button
        load_project_btn.setCursor(QCursor(Qt.PointingHandCursor))
    
    def handle_load_project_click(self):
        """Handle load project button click by opening file dialog"""
        filename, _ = QFileDialog.getOpenFileName(self, "Load Scenario", "", "JSON Files (*.json)")
        
        if filename:
            # Emit signal to transition to main window with the loaded file
            self.transition_to_main_with_file.emit(filename)
            self.close()
        # If no file selected (user cancelled), do nothing and stay on title screen
    
    def handle_new_project_click(self):
        """Handle new project button click"""
        self.transition_to_main.emit()
        self.close()
    
    def center_on_screen(self):
        """Center the window on the screen"""
        screen_geometry = QApplication.desktop().screenGeometry()
        window_geometry = self.geometry()
        
        x = (screen_geometry.width() - window_geometry.width()) // 2
        y = (screen_geometry.height() - window_geometry.height()) // 2
        
        self.move(x, y)

# For testing the title screen independently
if __name__ == "__main__":
    app = QApplication(sys.argv)
    title = TitleScreen()
    title.show()
    sys.exit(app.exec_()) 