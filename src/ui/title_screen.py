# -------- PyQt5→6 shim (auto-inserted) --------------------------
from PyQt6.QtCore import Qt
AlignmentFlag = Qt.AlignmentFlag   # backwards-compat alias
Orientation   = Qt.Orientation
# ----------------------------------------------------------------

# TODO_PYQT6: verify width()/isType() semantics
import sys
from PyQt6.QtWidgets import QWidget, QApplication, QLabel, QVBoxLayout, QPushButton, QHBoxLayout, QFileDialog
from PyQt6.QtGui import QPixmap, QFont, QCursor, QGuiApplication
from PyQt6.QtCore import Qt, pyqtSignal
from src.utils.resource import resource_path
from src.utils.audio_utils import get_audio_player, play_sound_effect

class TitleScreen(QWidget):
    # Add a custom signal to indicate the title screen should be closed
    transition_to_main = pyqtSignal()
    transition_to_main_with_file = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        
        # Set window to be frameless (no title bar)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        
        # Set up the layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Load and display the title image
        title_image = QLabel()
        pixmap = QPixmap(resource_path("src/ui/assets/demotitle7.png"))
        if not pixmap.isNull():
            # Scale the pixmap to 90% of its original size
            original_width = pixmap.width()
            original_height = pixmap.height()
            scaled_width = int(original_width * 0.9)
            scaled_height = int(original_height * 0.9)
            pixmap = pixmap.scaled(scaled_width, scaled_height, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            title_image.setPixmap(pixmap)
        else:
            # Fallback if image is not found
            title_image.setText("Title Screen (Image Not Found)")
            title_image.setStyleSheet("font-size: 24px; color: white;")
            self.setStyleSheet("background-color: #2A2A2A;")
        
        # Center the image in the layout
        title_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_image)
        
        # Set the window size to match the scaled image size
        self.setFixedSize(pixmap.width(), pixmap.height())
        
        # Add Exit button
        self.create_exit_button()
        
        # Add New Project button
        self.create_new_project_button()
        
        # Add Load Project button
        self.create_load_project_button()
        
        # Add version label in the bottom left corner
        self.create_version_label()
        
        # Center the window on the screen
        self.center_on_screen()
    
    def showEvent(self, event):
        """Enable audio looping when the title screen is shown"""
        super().showEvent(event)
        # Enable looping for any currently playing audio
        audio_player = get_audio_player()
        if audio_player.is_playing() and audio_player._current_file:
            # If audio is already playing, enable looping
            audio_player._should_loop = True
            print(f"AudioPlayer: Enabled looping for {audio_player._current_file}")
    
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
                border-radius: 3px;
                color: #CCCCCC;
            }
            QPushButton:hover {
                background-color: rgba(200, 240, 255, 20);
                color: #D8F0FF;
            }
        """)
        
        # Position button at (5,5) in the top left corner
        exit_btn.move(5, 5)
        
        # Connect button click to close the window instead of quitting the application
        exit_btn.clicked.connect(self.close_safely)
        
        # Set cursor to hand when hovering over button
        exit_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
        # Add hover sound effect
        exit_btn.enterEvent = lambda event: self.play_hover_sound()
        
        # Store reference to button for cleanup
        self.exit_btn = exit_btn
    
    def close_safely(self):
        """Safely close the window and exit the application"""
        # Stop any playing audio before exiting
        get_audio_player().stop()
        
        # First close this window properly
        self.close()
        
        # Then quit the entire application
        # We need to use QApplication.instance() to get the current application instance
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if app:
            app.quit()
    
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
        pixmap = QPixmap(resource_path("src/ui/assets/newproject.png"))
        if not pixmap.isNull():
            pixmap = pixmap.scaled(20, 20, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            img_label.setPixmap(pixmap)
        else:
            img_label.setText("+")
        
        # Add text to button
        text_label = QLabel("New Project")
        text_label.setStyleSheet("color: #CCCCCC;")  # Light gray color for text
        
        # Add to layout
        btn_layout.addWidget(img_label)
        btn_layout.addWidget(text_label)
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
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
        btn_y = (window_height - new_project_btn.height()) // 2
        new_project_btn.move(btn_x, btn_y)
        
        # Connect button click to transition
        new_project_btn.clicked.connect(self.handle_new_project_click)
        
        # Set cursor to hand when hovering over button
        new_project_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
        # Add hover sound effect
        new_project_btn.enterEvent = lambda event: self.play_hover_sound()
        
        # Store reference to button for cleanup
        self.new_project_btn = new_project_btn
    
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
        pixmap = QPixmap(resource_path("src/ui/assets/loadproject.png"))
        if not pixmap.isNull():
            pixmap = pixmap.scaled(20, 20, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            img_label.setPixmap(pixmap)
        else:
            img_label.setText("📂")
        
        # Add text to button
        text_label = QLabel("Load Project")
        text_label.setStyleSheet("color: #CCCCCC;")  # Light gray color for text
        
        # Add to layout
        btn_layout.addWidget(img_label)
        btn_layout.addWidget(text_label)
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
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
        btn_y = (window_height - load_project_btn.height()) // 2
        load_project_btn.move(btn_x, btn_y)
        
        # Connect button click to load handler
        load_project_btn.clicked.connect(self.handle_load_project_click)
        
        # Set cursor to hand when hovering over button
        load_project_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
        # Add hover sound effect
        load_project_btn.enterEvent = lambda event: self.play_hover_sound()
        
        # Store reference to button for cleanup
        self.load_project_btn = load_project_btn
    
    def handle_load_project_click(self):
        """Handle load project button click by opening file dialog"""
        # Play click sound effect
        self.play_click_sound()
        
        filename, _ = QFileDialog.getOpenFileName(self, "Load Scenario", "", "JSON Files (*.json)")
        
        if filename:
            # Stop any playing audio before transitioning
            get_audio_player().stop()
            # Emit signal to transition to main window with the loaded file
            self.transition_to_main_with_file.emit(filename)
            self.close()
        # If no file selected (user cancelled), do nothing and stay on title screen
    
    def handle_new_project_click(self):
        """Handle new project button click"""
        # Stop any playing audio before transitioning
        get_audio_player().stop()
        self.transition_to_main.emit()
        self.close()
    
    def create_version_label(self):
        """Create and add the version label in the bottom left corner"""
        version_label = QLabel("OVERCLOCK v 2025.02.01b | Open Core GPLv3 (repos@watt-bit.com) | Binaries, Powerlandia Data Packs, and all Resources (c) 2025 Watt-Bit Research Inc.", self)
        version_label.setFixedWidth(1100)
        
        # Set font to 12pt normal weight
        font = QFont()
        font.setPointSize(12)
        version_label.setFont(font)
        
        # Set icy blue color
        version_label.setStyleSheet("color: #A0D8FF;")
        
        # Position in bottom left corner
        version_label.move(10, self.height() - version_label.height())
    
    def center_on_screen(self):
        """Center the window on the screen"""
        screen_geometry = QGuiApplication.primaryScreen().availableGeometry()
        window_geometry = self.geometry()
        
        x = (screen_geometry.width() - window_geometry.width()) // 2
        y = (screen_geometry.height() - window_geometry.height()) // 2
        
        self.move(x, y)
    
    def play_hover_sound(self):
        """Play button hover sound effect"""
        try:
            play_sound_effect("buttonhover.wav")
        except Exception as e:
            print(f"Error playing hover sound: {e}")
    
    def play_click_sound(self):
        """Play button click sound effect"""
        try:
            play_sound_effect("buttonclick.wav")
        except Exception as e:
            print(f"Error playing click sound: {e}")

# For testing the title screen independently
if __name__ == "__main__":
    app = QApplication(sys.argv)
    title = TitleScreen()
    title.show()
    sys.exit(app.exec()) 