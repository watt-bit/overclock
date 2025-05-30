import sys
import platform
from PyQt5.QtWidgets import QWidget, QApplication, QVBoxLayout, QGraphicsView, QGraphicsScene, QGraphicsRectItem
from PyQt5.QtGui import QKeyEvent, QBrush, QPen, QPixmap
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QUrl, QSizeF
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QGraphicsVideoItem
from PyQt5.QtWidgets import QGraphicsPixmapItem
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
        
        # Create graphics view and scene for display
        self.graphics_view = QGraphicsView()
        self.graphics_scene = QGraphicsScene()
        self.graphics_view.setScene(self.graphics_scene)
        
        # Set scene size to match dimensions (1600x900)
        self.graphics_scene.setSceneRect(0, 0, 1600, 900)
        self.graphics_view.setStyleSheet("background: black;")
        
        # Remove scroll bars and set view size
        self.graphics_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.graphics_view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.graphics_view.setFixedSize(1600, 900)

        # Add graphics view to layout
        layout.addWidget(self.graphics_view)
        
        # Determine if we're on macOS (use video) or Windows (use image)
        # Temporarily forcing image mode for testing
        self.is_macos = platform.system() == "Darwin"
        
        if self.is_macos:
            # Create video item and media player for macOS
            self.video_item = QGraphicsVideoItem()
            self.video_item.setSize(QSizeF(1600, 900))
            self.video_item.setZValue(0)  # Bottom layer
            self.graphics_scene.addItem(self.video_item)
            
            self.media_player = QMediaPlayer(None, QMediaPlayer.VideoSurface)
            self.media_player.setVideoOutput(self.video_item)
            
            # Load the video for macOS
            video_path = resource_path("src/ui/assets/video/titlevideo6small_faststart.mp4")
            video_url = QUrl.fromLocalFile(video_path)
            self.media_player.setMedia(QMediaContent(video_url))
        else:
            # Create image item for Windows
            image_path = resource_path("src/ui/assets/augurtitle2.png")
            pixmap = QPixmap(image_path)
            # Scale image to fit within 1600x900 while maintaining aspect ratio
            pixmap = pixmap.scaled(1600, 900, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            
            self.image_item = QGraphicsPixmapItem(pixmap)
            
            # Center the image in the scene
            image_width = pixmap.width()
            image_height = pixmap.height()
            x_offset = (1600 - image_width) / 2
            y_offset = (900 - image_height) / 2
            self.image_item.setPos(x_offset, y_offset)
            
            self.image_item.setZValue(0)  # Bottom layer
            self.graphics_scene.addItem(self.image_item)
            
            # No media player needed for Windows
            self.media_player = None
        
        # Create and add black mask on top of everything
        self.black_mask = QGraphicsRectItem(0, 0, 1600, 900)
        self.black_mask.setBrush(QBrush(Qt.black))
        self.black_mask.setPen(QPen(Qt.NoPen))  # No border
        self.black_mask.setZValue(1)  # Top layer - above video/image
        self.graphics_scene.addItem(self.black_mask)
        
        # Set the window size to match the dimensions
        self.setFixedSize(1600, 900)
        
        # Center the window on the screen
        self.center_on_screen()
        
        # Setup auto-transition timer (5 seconds)
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(10000)  # 10 seconds
        self.timer.timeout.connect(self.auto_transition)
        
        # Setup fade timer for black mask
        self.fade_timer = QTimer(self)
        self.fade_timer.setInterval(10)  # Update every 10ms for smooth animation
        self.fade_timer.timeout.connect(self.fade_step)
        self.fade_opacity = 1.0  # Start fully opaque
        
        # Setup fade-to-black timer (starts at 8.5 seconds)
        self.fade_to_black_timer = QTimer(self)
        self.fade_to_black_timer.setSingleShot(True)
        self.fade_to_black_timer.setInterval(8500)  # 8.5 seconds
        self.fade_to_black_timer.timeout.connect(self.start_fade_to_black)
        
        # Setup fade-to-black animation timer
        self.fade_black_timer = QTimer(self)
        self.fade_black_timer.setInterval(10)  # Update every 10ms for smooth animation
        self.fade_black_timer.timeout.connect(self.fade_to_black_step)
        self.is_fading_to_black = False
    
    def showEvent(self, event):
        """Start the display and timer when the widget is shown"""
        super().showEvent(event)
        
        # Start video only on macOS
        if self.is_macos and self.media_player:
            self.media_player.play()
            
        self.timer.start()
        # Start the fade animation for the black mask
        self.fade_timer.start()
        # Start the 8.5-second timer for fade-to-black
        self.fade_to_black_timer.start()
    
    def fade_step(self):
        """Handle one step of the fade animation"""
        self.fade_opacity -= 0.005
        
        if self.fade_opacity <= 0:
            # Animation complete - make fully transparent and stop timer
            self.fade_opacity = 0.0
            self.fade_timer.stop()
        
        # Apply the new opacity to the black mask
        self.black_mask.setOpacity(self.fade_opacity)
    
    def start_fade_to_black(self):
        """Start the fade-to-black animation at 8.5 seconds"""
        self.is_fading_to_black = True
        self.fade_black_timer.start()
    
    def fade_to_black_step(self):
        """Handle one step of the fade-to-black animation"""
        # Increase opacity by 0.01 each step (1.0 / 100 steps = 0.01)
        # 100 steps * 10ms = 1000ms (1 second) total duration
        self.fade_opacity += 0.01
        
        if self.fade_opacity >= 1.0:
            # Animation complete - make fully opaque and stop timer
            self.fade_opacity = 1.0
            self.fade_black_timer.stop()
        
        # Apply the new opacity to the black mask
        self.black_mask.setOpacity(self.fade_opacity)
    
    def auto_transition(self):
        """Automatically transition to the next screen after timer expires"""
        if self.is_macos and self.media_player:
            self.media_player.stop()
        self.fade_timer.stop()  # Stop fade timer when transitioning
        self.fade_to_black_timer.stop()  # Stop fade-to-black timer
        self.fade_black_timer.stop()  # Stop fade-to-black animation timer
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
            # Stop video if running and timer if a key is pressed
            if self.is_macos and self.media_player:
                self.media_player.stop()
            self.timer.stop()
            self.fade_timer.stop()  # Stop fade timer when transitioning
            self.fade_to_black_timer.stop()  # Stop fade-to-black timer
            self.fade_black_timer.stop()  # Stop fade-to-black animation timer
            self.transition_to_next.emit()
            self.close()
        # Also transition on Escape or Space for user convenience
        elif event.key() in (Qt.Key_Escape, Qt.Key_Space):
            # Stop video if running and timer if a key is pressed
            if self.is_macos and self.media_player:
                self.media_player.stop()
            self.timer.stop()
            self.fade_timer.stop()  # Stop fade timer when transitioning
            self.fade_to_black_timer.stop()  # Stop fade-to-black timer
            self.fade_black_timer.stop()  # Stop fade-to-black animation timer
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