# TODO_PYQT6: verify width()/isType() semantics
from PyQt6.QtGui import QBrush, QColor, QPixmap, QRadialGradient
from PyQt6.QtCore import Qt, QRectF
from .base import ComponentBase
from src.utils.resource import resource_path

class FactoryComponent(ComponentBase):
    def __init__(self, x, y):
        # Initialize with the same size as other components
        super().__init__(x, y, 300, 220)
        # Make brush transparent (no background)
        self.setBrush(Qt.GlobalColor.transparent)
        # Load the image
        self.image = QPixmap(resource_path("src/ui/assets/factory.png"))
        
        # Decorative component with no functional properties
        self.name = "Factory"
    
    def paint(self, painter, option, widget):
        # Save painter state
        painter.save()
        
        # Draw the shadow first (before the component)
        rect = self.boundingRect()
        
        # Create a shadow ellipse at the bottom of the component - HALF AS WIDE for factory
        shadow_width = rect.width() * 0.45    # Half as wide as normal (0.9 / 2)
        shadow_height = rect.height() * 0.4  # Keep the same height as normal
        
        # Position the shadow beneath the component with offset
        shadow_x = rect.x() + (rect.width() - shadow_width) / 2 + 15
        shadow_y = rect.y() + rect.height() - shadow_height / 2 + self.shadow_y_offset - 10
        
        # Create a radial gradient for the shadow
        gradient = QRadialGradient(
            shadow_x + shadow_width / 2,
            shadow_y + shadow_height / 2,
            shadow_width / 2
        )
        gradient.setColorAt(0, QColor(0, 0, 0, int(255 * self.shadow_opacity)))
        gradient.setColorAt(1, QColor(0, 0, 0, 0))
        
        # Draw the shadow
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(int(shadow_x), int(shadow_y), int(shadow_width), int(shadow_height))
        
        # Restore painter state after drawing shadow
        painter.restore()
        
        # Now call the base class to handle the selection highlight
        painter.save()
        super().paint(painter, option, widget)
        painter.restore()
        
        # Get component dimensions for the factory image
        rect = self.boundingRect()
        
        # Calculate image area - factories are taller than bushes
        image_height = rect.height() * 0.68  # Factory is taller than bush
        
        # Ensure width is a numeric value
        width = rect.width()
        if isinstance(width, tuple):
            width = width[0]  # Use first element if it's a tuple
        
        # Ensure height is a numeric value
        height = image_height
        if isinstance(height, tuple):
            height = height[0]  # Use first element if it's a tuple
            
        image_width = min(float(width) * 0.9, float(height))
        
        # Center the image horizontally
        x_offset = (rect.width() - image_width) / 2
        if isinstance(x_offset, tuple):
            x_offset = x_offset[0]
        
        # Create image rect
        image_rect = QRectF(
            rect.x() + x_offset,
            rect.y() + (rect.height() * 0.05),  # Add a small top margin
            image_width,
            image_height
        )
        
        # Draw the image with transparent background
        if not self.image.isNull():
            painter.drawPixmap(
                image_rect,
                self.image,
                QRectF(0, 0, self.image.width(), self.image.height())
            )
    
    def mousePressEvent(self, event):
        # Call the base class mousePressEvent for selection functionality
        super().mousePressEvent(event)
        
        # Decorative components should not open properties panel
        # Do nothing else here - don't emit the component_clicked signal
    
    def serialize(self):
        return {
            'type': 'factory',
            'x': self.x(),
            'y': self.y(),
            'name': self.name
        } 