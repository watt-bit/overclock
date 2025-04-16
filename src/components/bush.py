from PyQt5.QtGui import QBrush, QColor, QPixmap, QRadialGradient
from PyQt5.QtCore import Qt, QRectF
from .base import ComponentBase

class BushComponent(ComponentBase):
    def __init__(self, x, y):
        # Initialize with the same size as other components
        super().__init__(x, y, 300, 220)
        # Make brush transparent (no background)
        self.setBrush(Qt.transparent)
        # Load the image
        self.image = QPixmap("src/ui/assets/bush.png")
        
        # Decorative component with no functional properties
        self.name = "Bush"
    
    def paint(self, painter, option, widget):
        # Save painter state
        painter.save()
        
        # Draw the shadow first (before the component)
        rect = self.boundingRect()
        
        # Create a shadow ellipse at the bottom of the component - HALF AS WIDE for bushes
        shadow_width = rect.width() * 0.45    # Half as wide as normal (0.9 / 2)
        shadow_height = rect.height() * 0.4  # Keep the same height as normal
        
        # Position the shadow beneath the component with offset
        shadow_x = rect.x() + (rect.width() - shadow_width) / 2 + 10
        shadow_y = rect.y() + rect.height() - shadow_height / 2 + self.shadow_y_offset - 31
        
        # Create a radial gradient for the shadow
        gradient = QRadialGradient(
            shadow_x + shadow_width / 2,
            shadow_y + shadow_height / 2,
            shadow_width / 2
        )
        gradient.setColorAt(0, QColor(0, 0, 0, 255 * self.shadow_opacity))
        gradient.setColorAt(1, QColor(0, 0, 0, 0))
        
        # Draw the shadow
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(shadow_x, shadow_y, shadow_width, shadow_height)
        
        # Restore painter state after drawing shadow
        painter.restore()
        
        # Now call the base class to handle the selection highlight
        painter.save()
        super(ComponentBase, self).paint(painter, option, widget)
        
        # If selected, draw white highlight box around the component
        if self.isSelected():
            # Get the bounding rectangle with a small padding
            padding = 4
            highlight_rect = QRectF(
                rect.x() - padding/2,
                rect.y() - padding/2,
                rect.width() + padding,
                rect.height() + padding
            )
            # Set up the painter for the highlight
            painter.setPen(self.selection_pen)
            painter.setBrush(Qt.NoBrush)
            # Draw the highlight rectangle
            painter.drawRect(highlight_rect)
        painter.restore()
        
        # Get component dimensions for the bush image
        rect = self.boundingRect()
        
        # Calculate image area with 1:1 aspect ratio (square)
        # Bushes are shorter and wider than trees, so use different proportions
        image_height = rect.height() * 0.6  # Bushes are shorter than trees
        
        # Ensure width is a numeric value
        width = rect.width()
        if isinstance(width, tuple):
            width = width[0]  # Use first element if it's a tuple
        
        # Ensure height is a numeric value
        height = image_height
        if isinstance(height, tuple):
            height = height[0]  # Use first element if it's a tuple
            
        image_size = min(float(width), float(height))
        
        # Center the image horizontally
        x_offset = (rect.width() - image_size) / 2
        if isinstance(x_offset, tuple):
            x_offset = x_offset[0]
        
        # Create square image rect
        image_rect = QRectF(
            rect.x() + x_offset,
            rect.y() + (rect.height() * 0.1),  # Add a small top margin
            image_size,
            image_size
        )
        
        # Draw the image with transparent background and 1:1 aspect ratio
        if not self.image.isNull():
            painter.drawPixmap(
                image_rect,
                self.image,
                QRectF(0, 0, self.image.width(), self.image.height())
            )
    
    def mousePressEvent(self, event):
        # Call the base class mousePressEvent for selection functionality
        super().mousePressEvent(event)
        
        # Check if we're in connection creation mode
        scene = self.scene()
        if scene and hasattr(scene, 'parent'):
            parent = scene.parent()
            if parent and hasattr(parent, 'creating_connection') and parent.creating_connection:
                # If in connection mode, don't emit clicked signal to prevent connection
                # This makes the bush component "invisible" to connection mode
                return
            
        # Only emit the clicked signal if not in connection mode
        if hasattr(self.scene(), 'component_clicked'):
            self.scene().component_clicked.emit(self)
    
    def serialize(self):
        return {
            'type': 'bush',
            'x': self.x(),
            'y': self.y(),
            'name': self.name
        } 