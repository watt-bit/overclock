from PyQt5.QtGui import QBrush, QColor, QPen, QFont, QPixmap, QRadialGradient
from PyQt5.QtCore import Qt, QRectF
from .base import ComponentBase

class BusComponent(ComponentBase):
    def __init__(self, x, y):
        # Initialize with the same size as other components
        super().__init__(x, y, 300, 220)
        # Make brush transparent (no background)
        self.setBrush(Qt.transparent)
        # Load the images
        self.loaded_image = QPixmap("src/ui/assets/busloaded.png")
        self.auto_image = QPixmap("src/ui/assets/busauto")  # Remove .png extension
        
        self.is_on = True  # Default state is on
        self.name = "Bus"  # Default name
        
    def has_load_connections(self):
        """Check if this bus is connected to any LoadComponent instances.
        
        Returns:
            bool: True if connected to at least one load, False otherwise
        """
        from .load import LoadComponent  # Import here to avoid circular imports
        
        for connection in self.connections:
            # Check if either end of the connection is a LoadComponent
            if connection.source != self and isinstance(connection.source, LoadComponent):
                return True
            if connection.target != self and isinstance(connection.target, LoadComponent):
                return True
        
        return False
        
    def paint(self, painter, option, widget):
        # Save painter state
        painter.save()
        
        # Draw the shadow first (before the component)
        rect = self.boundingRect()
        
        # Create a shadow ellipse at the bottom of the component - 75% as wide for bus
        shadow_width = rect.width() * 0.675    # 75% of normal (0.9 * 0.75)
        shadow_height = rect.height() * 0.3   # 75% of normal height (0.4 * 0.75)
        
        # Position the shadow beneath the component with offset
        shadow_x = rect.x() + (rect.width() - shadow_width) / 2 + 15
        shadow_y = rect.y() + rect.height() - shadow_height / 2 + self.shadow_y_offset - 23
        
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
        
        # Get component dimensions
        rect = self.boundingRect()
        
        # Calculate image area with 1:1 aspect ratio (square)
        # Using 80% of height for the image
        image_height = rect.height() * 0.65
        image_size = min(rect.width(), image_height)
        
        # Center the image horizontally
        x_offset = (rect.width() - image_size) / 2
        
        # Create square image rect
        image_rect = QRectF(
            rect.x() + x_offset,
            rect.y() + (rect.height() * 0.05),  # Add a small top margin
            image_size,
            image_size
        )
        
        # Determine which image to use based on load connections
        has_loads = self.has_load_connections()
        current_image = self.loaded_image if has_loads else self.auto_image
        
        # Draw the image with transparent background and 1:1 aspect ratio
        if not current_image.isNull():
            painter.drawPixmap(
                image_rect,
                current_image,
                QRectF(0, 0, current_image.width(), current_image.height())
            )
        
        # Calculate text area (remaining space below the image)
        text_rect = QRectF(
            rect.x(),
            rect.y() + image_size + (rect.height() * 0.05),  # Position below image with margin
            rect.width(),
            rect.height() - image_size - (rect.height() * 0.05)
        )
        
        # Set text color to white
        painter.setPen(QPen(Qt.white))
        
        # Get the current view scale factor to adjust text size
        scale_factor = 1.0
        if self.scene() and self.scene().views():
            view = self.scene().views()[0]
            if hasattr(view, 'transform'):
                scale_factor = 1.0 / view.transform().m11()  # Get inverse of horizontal scale
        
        # Set font with size adjusted for current zoom level
        font = QFont('Arial', 14 * scale_factor)
        painter.setFont(font)
        
        # Determine status text based on load connections
        if not has_loads:
            # Show AUTO instead of ON for buses with no loads
            status_text = "AUTO"
        else:
            # Show LOAD ON/OFF for buses with loads for clarity
            status_text = "LOAD ON" if self.is_on else "LOAD OFF"
            
        # Draw the name and status text centered below the image
        combined_text = f"{self.name} ({status_text})"
        painter.drawText(text_rect, Qt.AlignCenter, combined_text)
    
    def serialize(self):
        return {
            'type': 'bus',
            'x': self.x(),
            'y': self.y(),
            'is_on': self.is_on,
            'name': self.name
        } 