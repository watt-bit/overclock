from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QPixmap
from src.utils.resource import resource_path


class TiledBackgroundWidget(QWidget):
    """Widget that supports a tiled background image"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.background_image = None
        self.tile_size = 300  # Fixed tile size of 100x100 pixels
        
    def set_background(self, image_path):
        """Set the background image from a file path"""
        self.background_image = QPixmap(resource_path(image_path))
        self.update()
        
    def paintEvent(self, event):
        """Override paintEvent to draw the tiled background"""
        painter = QPainter(self)
        
        # First call the base implementation to clear the background
        super().paintEvent(event)
        
        # Only proceed if we have a valid background image
        if not self.background_image or self.background_image.isNull():
            return
            
        # Get the size of the widget
        rect = self.rect()
        
        # Scale the background image to our fixed tile size
        scaled_image = self.background_image.scaled(self.tile_size, self.tile_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        
        # Calculate the grid based on the view rect
        left = int(rect.left()) - (int(rect.left()) % self.tile_size)
        top = int(rect.top()) - (int(rect.top()) % self.tile_size)
        
        # Draw the tiled background
        for x in range(left, int(rect.right()) + self.tile_size, self.tile_size):
            for y in range(top, int(rect.bottom()) + self.tile_size, self.tile_size):
                painter.drawPixmap(x, y, self.tile_size, self.tile_size, scaled_image) 