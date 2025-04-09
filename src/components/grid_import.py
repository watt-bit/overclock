from PyQt5.QtGui import QBrush, QColor, QPen, QPainter, QFont, QPixmap
from PyQt5.QtCore import Qt, QRectF
from .base import ComponentBase

class GridImportComponent(ComponentBase):
    def __init__(self, x, y):
        # Initialize with the same size as other components
        super().__init__(x, y, 300, 220)
        # Make brush transparent (no background)
        self.setBrush(Qt.transparent)
        # Load the image
        self.image = QPixmap("src/ui/assets/grid_import.png")
        
        self.capacity = 2000  # kW - maximum import capacity
        self.operating_mode = "Last Resort Unit (Auto)"  # Only Auto mode for now
        self.auto_charge_batteries = False  # Whether this component will charge batteries with grid power
        self.last_import = 0  # Track the last import amount for display
    
    def paint(self, painter, option, widget):
        # Save painter state
        painter.save()
        
        # Call base class paint to handle the selection highlight
        super().paint(painter, option, widget)
        
        # Get component dimensions
        rect = self.boundingRect()
        
        # Calculate image area with 1:1 aspect ratio (square)
        # Using 100% of height for the image
        image_height = rect.height() * 1.0
        image_size = min(rect.width(), image_height)
        
        # Center the image horizontally
        x_offset = (rect.width() - image_size) / 2
        
        # Create square image rect
        image_rect = QRectF(
            rect.x() + x_offset,
            rect.y() + (rect.height() * 0.05) - 40,  # Add a small top margin
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
            
            # Calculate import percentage
            if self.capacity > 0:
                import_percentage = self.last_import / self.capacity
            else:
                import_percentage = 0
            
            # Draw vertical import indicator in top right corner
            # Set indicator size relative to image size
            indicator_width = image_size * 0.08
            indicator_height = image_size * 0.45
            indicator_padding = image_size * 0.04
            
            # Position indicator in top right corner with padding
            indicator_x = image_rect.x() + image_rect.width() - indicator_width - indicator_padding
            indicator_y = image_rect.y() + indicator_padding
            
            # Draw import indicator frame (outline)
            painter.setPen(QPen(Qt.white, 1.5))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(indicator_x, indicator_y, indicator_width, indicator_height)
            
            # Determine fill color based on import percentage - use blue with varying brightness
            # Darker blue for lower import, brighter blue for higher import
            if import_percentage < 0.25:
                # Dark blue for low import (0-25%)
                fill_color = QColor("#00008B")  # Dark blue
            elif import_percentage < 0.5:
                # Medium-dark blue for medium-low import (25-50%)
                fill_color = QColor("#0000CD")  # Medium blue
            elif import_percentage < 0.75:
                # Medium blue for medium-high import (50-75%)
                fill_color = QColor("#0000FF")  # Blue
            else:
                # Bright blue for maximum import (75-100%)
                fill_color = QColor("#1E90FF")  # Dodger blue
            
            # Draw filled portion representing current import percentage (from bottom to top)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(fill_color))
            
            fill_height = indicator_height * import_percentage
            # Calculate y-position for fill (starting from bottom of indicator)
            fill_y = indicator_y + (indicator_height - fill_height)
            
            painter.drawRect(indicator_x, fill_y, indicator_width, fill_height)
        
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
        
        # Draw the capacity text
        capacity_text = f"{self.capacity} kW (import)"
        painter.drawText(text_rect, Qt.AlignCenter, capacity_text)
        
        # Restore painter state
        painter.restore()
    
    def calculate_output(self, deficit):
        """Calculate grid import based on system deficit"""
        # Provide power up to capacity to meet deficit
        import_amount = min(deficit, self.capacity)
        self.last_import = import_amount  # Track the last import amount
        return import_amount
    
    def serialize(self):
        return {
            'type': 'grid_import',
            'x': self.x(),
            'y': self.y(),
            'capacity': self.capacity,
            'operating_mode': self.operating_mode,
            'auto_charge_batteries': self.auto_charge_batteries,
            'last_import': self.last_import
        } 