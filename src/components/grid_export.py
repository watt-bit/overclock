from PyQt5.QtGui import QBrush, QColor, QPen, QPainter, QFont, QPixmap
from PyQt5.QtCore import Qt, QRectF
from .base import ComponentBase

class GridExportComponent(ComponentBase):
    def __init__(self, x, y):
        # Initialize with the same size as other components
        super().__init__(x, y, 300, 220)
        # Make brush transparent (no background)
        self.setBrush(Qt.transparent)
        # Load the image
        self.image = QPixmap("src/ui/assets/grid_export.png")
        
        self.capacity = 1500  # kW - maximum export capacity
        self.operating_mode = "Last Resort Unit (Auto)"  # Only Auto mode for now
        self.bulk_ppa_price = 0.00  # $/kWh - price received for exported power
        self.accumulated_revenue = 0.00  # Track accumulated revenue in dollars
    
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
        
        # Calculate text area (remaining space below the image)
        text_rect = QRectF(
            rect.x(),
            rect.y() + image_size + (rect.height() * 0.05) - 40,  # Adjust position to account for the -40 image offset
            rect.width(),
            rect.height() - image_size - (rect.height() * 0.05) + 40  # Add 40 to the height to account for the offset
        )
        
        # Split the text area into two parts for capacity and revenue
        capacity_rect = QRectF(
            text_rect.x(),
            text_rect.y(),
            text_rect.width(),
            text_rect.height() * 0.5
        )
        
        revenue_rect = QRectF(
            text_rect.x(),
            text_rect.y() + text_rect.height() * 0.5 + 20,
            text_rect.width(), 
            text_rect.height() * 0.5
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
        capacity_text = f"{self.capacity} kW (export)"
        painter.drawText(capacity_rect, Qt.AlignCenter, capacity_text)
        
        # Draw the revenue text if price is set
        if self.bulk_ppa_price > 0:
            revenue_text = f"Revenue: ${self.accumulated_revenue:.2f}"
            painter.drawText(revenue_rect, Qt.AlignCenter, revenue_text)
        
        # Restore painter state
        painter.restore()
    
    def calculate_export(self, surplus):
        """Calculate how much surplus power can be exported"""
        # Export as much surplus as possible up to capacity
        return min(surplus, self.capacity)
    
    def serialize(self):
        return {
            'type': 'grid_export',
            'x': self.x(),
            'y': self.y(),
            'capacity': self.capacity,
            'operating_mode': self.operating_mode,
            'bulk_ppa_price': self.bulk_ppa_price,
            'accumulated_revenue': self.accumulated_revenue
        } 