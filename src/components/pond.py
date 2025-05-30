# TODO_PYQT6: verify width()/isType() semantics
from PyQt6.QtGui import QBrush, QColor, QPixmap, QRadialGradient
from PyQt6.QtCore import Qt, QRectF
from .base import ComponentBase
from src.utils.resource import resource_path

class PondComponent(ComponentBase):
    def __init__(self, x, y):
        # Initialize with the same size as other components
        super().__init__(x, y, 300, 220)
        # Make brush transparent (no background)
        self.setBrush(Qt.GlobalColor.transparent)
        # Load the image
        self.image = QPixmap(resource_path("src/ui/assets/pond.png"))
        
        # Decorative component with no functional properties
        self.name = "Pond"
    
    def paint(self, painter, option, widget):
        # Save painter state
        painter.save()
        
        # Draw the shadow first (before the component)
        rect = self.boundingRect()
        
        # Create a shadow ellipse at the bottom of the component - HALF AS WIDE for ponds (like trees/bushes)
        shadow_width = rect.width() * 0.45    # Half as wide as normal (0.9 / 2)
        shadow_height = rect.height() * 0.4  # Keep the same height as normal
        
        # Position the shadow beneath the component with offset
        shadow_x = rect.x() + (rect.width() - shadow_width) / 2
        shadow_y = rect.y() + rect.height() - shadow_height / 2 + self.shadow_y_offset
        
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
        
        # Call the parent class paint method to handle selection highlight and the open button
        super().paint(painter, option, widget)
        
        # Get component dimensions for the pond image
        rect = self.boundingRect()
        
        # Calculate image area with 3:2.2 aspect ratio (wider than tall)
        # Make the pond larger than other decorative elements
        image_height = rect.height() * 0.85  # Larger than bush (0.6) or tree (0.68)
        
        # Calculate width based on 3:2.2 ratio (width:height)
        aspect_ratio = 3.0 / 2.2
        image_width = image_height * aspect_ratio
        
        # Ensure width is within component bounds
        if image_width > rect.width() * 0.95:
            image_width = rect.width() * 0.95
            image_height = image_width / aspect_ratio
        
        # Ensure dimensions are numeric values
        if isinstance(image_width, tuple):
            image_width = image_width[0]
        if isinstance(image_height, tuple):
            image_height = image_height[0]
            
        # Center the image horizontally
        x_offset = (rect.width() - image_width) / 2
        if isinstance(x_offset, tuple):
            x_offset = x_offset[0]
        
        # Create image rect with the 3:2.2 aspect ratio
        image_rect = QRectF(
            rect.x() + x_offset,
            rect.y() + (rect.height() * 0.05),  # Add a small top margin
            image_width,
            image_height
        )
        
        # Draw the image with transparent background and proper aspect ratio
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
            'type': 'pond',
            'x': self.x(),
            'y': self.y(),
            'name': self.name
        } 