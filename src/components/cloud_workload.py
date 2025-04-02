from PyQt5.QtGui import QBrush, QColor, QPen, QPainter, QFont, QPixmap
from PyQt5.QtCore import Qt, QRectF
from .base import ComponentBase

class CloudWorkloadComponent(ComponentBase):
    def __init__(self, x, y):
        # Initialize with the same size as other components
        super().__init__(x, y, 300, 220)
        # Make brush transparent (no background)
        self.setBrush(Qt.transparent)
        # Load the image
        self.image = QPixmap("src/ui/assets/cloudworkload.png")
        
        # Disable shadow effect for this component only
        self.shadow_opacity = 0
        
        # Component properties
        self.operating_mode = "No Customer"  # "No Customer" or "Multi-Cloud Spot"
        
        # Resource parameters for Multi-Cloud Spot mode (not editable by user)
        self.traditional_cloud_power = 0.14  # kW per resource
        self.traditional_cloud_price = 0.05  # $ per resource hour
        
        self.gpu_intensive_power = 1.0  # kW per resource
        self.gpu_intensive_price = 1.25  # $ per resource hour
        
        self.crypto_asic_power = 5.0  # kW per resource
        self.crypto_asic_price = 1.00  # $ per resource hour
        
        # Track accumulated revenue
        self.accumulated_revenue = 0.00  # $ from cloud workload
    
    def paint(self, painter, option, widget):
        # Save painter state
        painter.save()
        
        # Call base class paint to handle the selection highlight
        super().paint(painter, option, widget)
        
        # Get component dimensions
        rect = self.boundingRect()
        
        # Calculate image area with 1:1 aspect ratio (square)
        # Using 80% of height for the image
        image_height = rect.height() * 0.7
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
            rect.y() + image_size + (rect.height() * 0.05),  # Position below image with margin
            rect.width(),
            rect.height() - image_size - (rect.height() * 0.05)
        )
        
        # Split the text area into two parts
        main_text_rect = QRectF(
            text_rect.x(),
            text_rect.y(),
            text_rect.width(),
            text_rect.height() * 0.7
        )
        
        revenue_rect = QRectF(
            text_rect.x(),
            text_rect.y() + text_rect.height() * 0.7,
            text_rect.width(), 
            text_rect.height() * 0.3
        )
        
        # Draw the text in white
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
        
        # Draw the component main text
        component_text = f"Cloud Workload ({self.operating_mode})"
        painter.drawText(main_text_rect, Qt.AlignCenter, component_text)
        
        # Draw the revenue text if in Multi-Cloud Spot mode
        if self.operating_mode == "Multi-Cloud Spot":
            revenue_text = f"Revenue: ${self.accumulated_revenue:.2f}"
            painter.drawText(revenue_rect, Qt.AlignCenter, revenue_text)
        
        # Restore painter state
        painter.restore()
    
    def calculate_cloud_revenue(self, load_component, energy_consumed, time_step=1.0):
        """Calculate cloud revenue based on load type and energy consumed
        
        Args:
            load_component: The load component to calculate revenue for
            energy_consumed: Energy consumed in kWh
            time_step: Time step in hours (default 1.0)
            
        Returns:
            Revenue generated in dollars
        """
        if self.operating_mode != "Multi-Cloud Spot" or load_component.profile_type != "Data Center":
            return 0.0
        
        # Determine resources used based on data center type
        if load_component.data_center_type == "Traditional Cloud":
            power_per_resource = self.traditional_cloud_power
            price_per_resource = self.traditional_cloud_price
        elif load_component.data_center_type == "GPU Intensive":
            power_per_resource = self.gpu_intensive_power
            price_per_resource = self.gpu_intensive_price
        elif load_component.data_center_type == "Crypto ASIC":
            power_per_resource = self.crypto_asic_power
            price_per_resource = self.crypto_asic_price
        else:
            return 0.0  # Unknown data center type
            
        # Calculate number of resources
        if power_per_resource > 0:
            # Energy (kWh) / power per resource (kW) = resource hours
            resource_hours = energy_consumed / power_per_resource
            # Revenue = resource hours * price per resource hour
            revenue = resource_hours * price_per_resource
            return revenue
        
        return 0.0
    
    def serialize(self):
        """Serialize the component data for saving"""
        return {
            'type': 'cloud_workload',
            'x': self.x(),
            'y': self.y(),
            'operating_mode': self.operating_mode,
            'accumulated_revenue': self.accumulated_revenue
        } 