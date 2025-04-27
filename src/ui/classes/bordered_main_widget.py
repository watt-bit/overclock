from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QRectF, QTimer
from PyQt5.QtGui import QPainter, QColor, QPainterPath, QLinearGradient
import math

class BorderedMainWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Initialize gradient colors for a cool, electric darkmode effect (same as GradientBorderText)
        self.colors = [
            QColor(58, 78, 178),    # Bright starlight electric blue
            QColor(46, 135, 175),   # Cool bright cyan
            QColor(30, 155, 145),   # Celestial teal
            QColor(20, 175, 185),   # Bright neon cyan
            QColor(18, 110, 190),   # Luminous sky blue
            QColor(75, 85, 195),    # Soft space indigo
            QColor(55, 95, 175),    # Twilight blue
            QColor(70, 145, 200),   # Arctic sky
            QColor(95, 170, 210),   # Distant pale cyan star
            QColor(40, 85, 150),    # Deep steel blue   
            QColor(65, 50, 135),    # Cosmic violet
            QColor(58, 78, 178),    # Bright starlight electric blue (for rhythm)
        ]
        
        # Animation properties
        self.animation_offset = 0
        self.animation_speed = 0.5
        self.border_width = 4
        self.corner_radius = 4
        
        # Set up animation timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.animate)
        self.timer.start(50)  # Update every 50ms
        
        # Make the widget's border transparent to mouse events
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        # Set style to ensure proper appearance
        self.setStyleSheet("background: transparent;")
        
    def animate(self):
        """Update animation and trigger redraw"""
        self.animation_offset = (self.animation_offset + self.animation_speed) % 100
        self.update()
        
    def paintEvent(self, event):
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        # First, fill the entire widget with black background
        painter.fillRect(self.rect(), QColor("#000000"))
        
        # Draw the border path
        rect = QRectF(self.rect())  # Convert QRect to QRectF
        path = QPainterPath()
        path.addRoundedRect(rect, self.corner_radius, self.corner_radius)
        
        # Create gradient for the border - use a rotated linear gradient for better performance
        angle = self.animation_offset * 3.6  # Convert percentage to degrees (0-100 to 0-360)
        radians = angle * 3.14159 / 180.0  # Convert to radians
        
        # Calculate endpoint based on angle to create rotating linear gradient
        length = max(self.width(), self.height()) * 2
        end_x = self.width() / 2 + length * math.cos(radians)
        end_y = self.height() / 2 + length * math.sin(radians)
        
        gradient = QLinearGradient(
            self.width() / 2 - length * math.cos(radians),
            self.height() / 2 - length * math.sin(radians),
            end_x, end_y
        )
        
        # Set gradient colors
        num_colors = len(self.colors)
        for i in range(num_colors):
            pos = i / (num_colors - 1)
            gradient.setColorAt(pos, self.colors[i])
        
        # Draw outer border
        painter.save()
        painter.setClipPath(path)
        painter.fillRect(rect, gradient)
        
        # Draw inner frame (creating a border effect)
        inner_rect = QRectF(
            rect.x() + self.border_width, 
            rect.y() + self.border_width,
            rect.width() - 2 * self.border_width,
            rect.height() - 2 * self.border_width
        )
        inner_path = QPainterPath()
        inner_path.addRoundedRect(inner_rect, self.corner_radius-self.border_width, self.corner_radius-self.border_width)
        
        # Set clipping to the inside area to create the border
        painter.setClipPath(inner_path, Qt.IntersectClip)
        painter.fillRect(rect, Qt.transparent)  # Clear the inner area
        painter.restore() 