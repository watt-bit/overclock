from PyQt5.QtWidgets import QGraphicsTextItem
from PyQt5.QtCore import Qt, QTimer, QRect, QRectF
from PyQt5.QtGui import QPainter, QPen, QColor, QPainterPath, QLinearGradient, QFontMetrics

class GradientBorderText(QGraphicsTextItem):
    """A text item with animated gradient border for welcome screen"""
    
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        # Initialize gradient colors for a cool, electric darkmode effect
        self.colors = [
            QColor(48, 68, 168),    # Starlight electric blue
            QColor(36, 120, 165),   # Cool bright cyan
            QColor(20, 140, 135),   # Crisp electric teal
            QColor(10, 160, 175),   # Bright neon cyan
            QColor(10, 95, 175),    # Luminous bright blue
            QColor(30, 100, 150),   # Starlight azure
            QColor(40, 125, 180),   # Brighter midnight sky blue
            QColor(24, 155, 180),   # Bright dark aquamarine
            QColor(35, 90, 140),    # Cool steel blue
            QColor(48, 68, 168),    # Starlight electric blue
        ]
        
        # Animation properties
        self.animation_offset = 0
        self.animation_speed = 0.5
        self.border_width = 2
        self.text_content = "Welcome\nBuild Here"
        
        # Initialize background image
        self.bg_image = None
        
        # Set up animation timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.animate)
        self.timer.start(50)  # Update every 50ms
        
        # Set clear background
        self.setDefaultTextColor(QColor(38, 38, 38, 255))
    
    def animate(self):
        """Update animation and trigger redraw"""
        self.animation_offset = (self.animation_offset + self.animation_speed) % 100
        self.update()
    
    def paint(self, painter, option, widget=None):
        """Paint the text with animated rainbow border following the letter contours"""
        painter.save()
        
        # First, paint the text normally to a temporary transparent pixmap
        # This is needed to get proper positioning with the original text renderer
        super().paint(painter, option, widget)
        
        # Create outline path for the text
        path = QPainterPath()
        
        # Get the font metrics for proper sizing
        font = self.font()
        font.setPointSize(120)  # Match the font size set in add_welcome_text
        font.setBold(True)
        
        # Split the text by lines
        lines = self.text_content.split('\n')
        y_offset = 0
        
        # Add each line of text as a separate text path
        for line in lines:
            # Center each line
            text_width = QFontMetrics(font).width(line)
            x_offset = (700 - text_width) / 2  # 700 is the text width set in add_welcome_text
            
            # Add text to path
            text_path = QPainterPath()
            text_path.addText(x_offset, y_offset + 100, font, line)  # 100 is approximate height for first line
            path.addPath(text_path)
            
            # Move down for next line
            y_offset += 130  # Approximate line height
        
        # Create gradient for the border
        gradient = QLinearGradient(0, 0, 700, 240)  # Approximate dimensions of text area
        
        # Set gradient colors with animation offset
        num_colors = len(self.colors)
        for i in range(num_colors):
            # Calculate position with offset for animation
            pos = (i / (num_colors - 1) + self.animation_offset / 100) % 1.0
            gradient.setColorAt(pos, self.colors[i])
        
        # Set up the pen for drawing the text outline
        outline_pen = QPen(gradient, self.border_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(outline_pen)
        
        # Draw the text outline
        painter.drawPath(path)
        
        painter.restore()

    def paintEvent(self, event):
        if self.bg_image and not self.bg_image.isNull():
            # Paint the background image first
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            
            # Create a rounded rect path for clipping
            rect = QRectF(self.rect())
            path = QPainterPath()
            path.addRoundedRect(rect, 3, 3)  # Match the 3px border-radius from CSS
            
            # Apply clipping to respect rounded corners
            painter.setClipPath(path)
            
            # Scale the image to fit the button width
            scaled_image = self.bg_image.scaled(
                self.width(), 
                self.height(),
                Qt.KeepAspectRatioByExpanding, 
                Qt.SmoothTransformation
            )
            
            # Center the image if it's taller than the button
            y_offset = 0
            if scaled_image.height() > self.height():
                y_offset = (scaled_image.height() - self.height()) / 2
                
            # Center the image if it's wider than the button
            x_offset = 0
            if scaled_image.width() > self.width():
                x_offset = (scaled_image.width() - self.width()) / 2
                
            # Draw the image centered and clipped to button shape
            painter.drawPixmap(
                QRect(0, 0, self.width(), self.height()),
                scaled_image,
                QRect(int(x_offset), int(y_offset), self.width(), self.height())
            )
            
        # Call the parent class paintEvent to draw the button content (text, etc.)
        super().paintEvent(event) 