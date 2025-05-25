import sys
from PyQt5.QtWidgets import QWidget, QApplication, QVBoxLayout, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QGraphicsRectItem
from PyQt5.QtGui import QKeyEvent, QPixmap, QBrush, QPen
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QUrl, QSizeF
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QGraphicsVideoItem
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
        
        # Create graphics view and scene for layering video and logo
        self.graphics_view = QGraphicsView()
        self.graphics_scene = QGraphicsScene()
        self.graphics_view.setScene(self.graphics_scene)
        
        # Set scene size to match video dimensions (1600x900)
        self.graphics_scene.setSceneRect(0, 0, 1600, 900)
        self.graphics_view.setStyleSheet("background: black;")
        
        # Remove scroll bars and set view size
        self.graphics_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.graphics_view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.graphics_view.setFixedSize(1600, 900)

        # Add graphics view to layout
        layout.addWidget(self.graphics_view)
        
        # Create video item and media player
        self.video_item = QGraphicsVideoItem()
        self.video_item.setSize(QSizeF(1600, 900))
        self.video_item.setZValue(0)  # Bottom layer
        self.graphics_scene.addItem(self.video_item)
        
        self.media_player = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.media_player.setVideoOutput(self.video_item)
        
        # Load and add the logo overlay
        logo_pixmap = QPixmap(resource_path("src/ui/assets/augurvibelogosmall.png"))
        if not logo_pixmap.isNull():
            # Scale logo to 700px width while maintaining aspect ratio
            scaled_logo = logo_pixmap.scaledToWidth(700, Qt.SmoothTransformation)
            
            # Create graphics pixmap item for the logo
            self.logo_item = QGraphicsPixmapItem(scaled_logo)
            
            # Center logo on the screen
            logo_x = (1600 - scaled_logo.width()) / 2  # Center horizontally
            logo_y = (900 - scaled_logo.height()) / 2  # Center vertically
            self.logo_item.setPos(logo_x, logo_y)
            self.logo_item.setZValue(1)  # Middle layer
            
            # Add logo to scene (it will be on top of video)
            self.graphics_scene.addItem(self.logo_item)
        
        # Create and add black mask on top of everything
        self.black_mask = QGraphicsRectItem(0, 0, 1600, 900)
        self.black_mask.setBrush(QBrush(Qt.black))
        self.black_mask.setPen(QPen(Qt.NoPen))  # No border
        self.black_mask.setZValue(2)  # Top layer - above everything
        self.graphics_scene.addItem(self.black_mask)
        
        # Set the window size to match the video size
        self.setFixedSize(1600, 900)
        
        # Load the video
        video_path = resource_path("src/ui/assets/video/titlevideo3.mp4")
        video_url = QUrl.fromLocalFile(video_path)
        self.media_player.setMedia(QMediaContent(video_url))
        
        # Center the window on the screen
        self.center_on_screen()
        
        # Setup auto-transition timer (5 seconds)
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(10000)  # 5 seconds
        self.timer.timeout.connect(self.auto_transition)
        
        # Setup fade timer for black mask
        self.fade_timer = QTimer(self)
        self.fade_timer.setInterval(10)  # Update every 10ms for smooth animation
        self.fade_timer.timeout.connect(self.fade_step)
        self.fade_opacity = 1.0  # Start fully opaque
    
    def showEvent(self, event):
        """Start the video and timer when the widget is shown"""
        super().showEvent(event)
        self.media_player.play()
        self.timer.start()
        # Start the fade animation for the black mask
        self.fade_timer.start()
    
    def fade_step(self):
        """Handle one step of the fade animation"""
        self.fade_opacity -= 0.005
        
        if self.fade_opacity <= 0:
            # Animation complete - make fully transparent and stop timer
            self.fade_opacity = 0.0
            self.fade_timer.stop()
        
        # Apply the new opacity to the black mask
        self.black_mask.setOpacity(self.fade_opacity)
    
    def auto_transition(self):
        """Automatically transition to the next screen after timer expires"""
        self.media_player.stop()
        self.fade_timer.stop()  # Stop fade timer when transitioning
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
            # Stop video and timer if a key is pressed
            self.media_player.stop()
            self.timer.stop()
            self.fade_timer.stop()  # Stop fade timer when transitioning
            self.transition_to_next.emit()
            self.close()
        # Also transition on Escape or Space for user convenience
        elif event.key() in (Qt.Key_Escape, Qt.Key_Space):
            # Stop video and timer if a key is pressed
            self.media_player.stop()
            self.timer.stop()
            self.fade_timer.stop()  # Stop fade timer when transitioning
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