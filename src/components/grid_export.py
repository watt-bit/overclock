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
        self.previous_revenue = 0.00  # Track previous revenue for milestone detection
        self.last_export = 0  # Track the last export amount for display
    
    def paint(self, painter, option, widget):
        # Save painter state
        painter.save()
        
        # Call base class paint to handle the selection highlight
        super().paint(painter, option, widget)
        
        # Get component dimensions
        rect = self.boundingRect()
        
        # Calculate image area with 1:1 aspect ratio (square)
        # Using 80% of height for the image
        image_height = rect.height() * 0.8
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
            
            # Calculate export percentage
            if self.capacity > 0:
                export_percentage = self.last_export / self.capacity
            else:
                export_percentage = 0
            
            # Draw vertical export indicator in top right corner
            # Set indicator size relative to image size
            indicator_width = image_size * 0.08
            indicator_height = image_size * 0.45
            indicator_padding = image_size * 0.04
            
            # Position indicator in top right corner with padding
            indicator_x = image_rect.x() + image_rect.width() - indicator_width - indicator_padding
            indicator_y = image_rect.y() + indicator_padding
            
            # Draw export indicator frame (outline)
            painter.setPen(QPen(Qt.white, 1.5))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(indicator_x, indicator_y, indicator_width, indicator_height)
            
            # Determine fill color based on export percentage - use red with varying brightness
            # Darker red for lower export, brighter red for higher export
            if export_percentage < 0.25:
                # Dark red for low export (0-25%)
                fill_color = QColor("#8B0000")  # Dark red
            elif export_percentage < 0.5:
                # Medium-dark red for medium-low export (25-50%)
                fill_color = QColor("#B22222")  # Firebrick
            elif export_percentage < 0.75:
                # Medium red for medium-high export (50-75%)
                fill_color = QColor("#DC143C")  # Crimson
            else:
                # Bright red for maximum export (75-100%)
                fill_color = QColor("#FF0000")  # Red
            
            # Draw filled portion representing current export percentage (from bottom to top)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(fill_color))
            
            fill_height = indicator_height * export_percentage
            # Calculate y-position for fill (starting from bottom of indicator)
            fill_y = indicator_y + (indicator_height - fill_height)
            
            painter.drawRect(indicator_x, fill_y, indicator_width, fill_height)
        
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
        export_amount = min(surplus, self.capacity)
        self.last_export = export_amount  # Track the last export amount
        return export_amount
    
    def update(self):
        """Called when the component needs to be updated"""
        # Call the parent's update method
        super().update()
        
        # Check for revenue milestones
        self.check_revenue_milestone()
    
    def check_revenue_milestone(self):
        """Check if revenue has crossed a $1000 milestone and create a particle if needed"""
        # Skip if simulation isn't running or if we're not in a scene
        scene = self.scene()
        if not scene or not hasattr(scene, 'parent'):
            return
        
        parent = scene.parent()
        if not parent or not hasattr(parent, 'simulation_engine'):
            return
            
        # Only create popups if simulation is running or autocompleting
        is_running = parent.simulation_engine.simulation_running
        is_autocompleting = False
        if hasattr(parent, 'is_autocompleting'):
            is_autocompleting = parent.is_autocompleting
            
        if not (is_running or is_autocompleting):
            # Store current revenue as previous and exit
            self.previous_revenue = self.accumulated_revenue
            return
        
        # Calculate how many $1000 increments we've crossed
        previous_thousands = int(self.previous_revenue / 1000)
        current_thousands = int(self.accumulated_revenue / 1000)
        
        if current_thousands > previous_thousands:
            # We've crossed at least one $1000 milestone
            # Get the center point of the component for particle origin
            rect = self.boundingRect()
            center_x = self.x() + rect.width() / 2
            center_y = self.y() + rect.height() / 3  # Position near the top of the component
            
            # Get the particle system
            if hasattr(parent, 'particle_system'):
                # Create a popup for each $1000 increment (in case we earned multiple $1000 in one step)
                for _ in range(current_thousands - previous_thousands):
                    parent.particle_system.create_revenue_popup(center_x, center_y, 1000)
        
        # Store current revenue for next check
        self.previous_revenue = self.accumulated_revenue
    
    def serialize(self):
        return {
            'type': 'grid_export',
            'x': self.x(),
            'y': self.y(),
            'capacity': self.capacity,
            'operating_mode': self.operating_mode,
            'bulk_ppa_price': self.bulk_ppa_price,
            'accumulated_revenue': self.accumulated_revenue,
            'previous_revenue': self.previous_revenue,
            'last_export': self.last_export
        } 