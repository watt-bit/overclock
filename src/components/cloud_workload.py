from PyQt5.QtGui import QPen, QFont, QPixmap
from PyQt5.QtCore import Qt, QRectF
from .base import ComponentBase
from src.utils.resource import resource_path

class CloudWorkloadComponent(ComponentBase):
    def __init__(self, x, y):
        # Initialize with the same size as other components
        super().__init__(x, y, 300, 220)
        # Make brush transparent (no background)
        self.setBrush(Qt.transparent)
        # Load the image
        self.image = QPixmap(resource_path("src/ui/assets/cloudworkload.png"))
        
        # Disable shadow effect for this component only
        self.shadow_opacity = 0
        
        # Component properties
        self.operating_mode = "No Customer"  # "No Customer", "Multi-Cloud Spot", or "Dedicated Capacity"
        
        # Resource parameters for Multi-Cloud Spot mode (not editable by user)
        self.traditional_cloud_power = 0.14  # kW per resource
        self.traditional_cloud_price = 0.05  # $ per resource hour
        
        self.gpu_intensive_power = 0.77  # kW per resource
        self.gpu_intensive_price = 2.00  # $ per resource hour
        
        self.crypto_asic_power = 5.0  # kW per resource
        self.crypto_asic_price = 1.00  # $ per resource hour
        
        # Resource parameters for Dedicated Capacity mode (editable by user)
        self.dedicated_power_per_resource = 1.20  # kW per resource
        self.dedicated_power_use_efficiency = 1.15  # Efficiency factor (1.0-2.0)
        self.dedicated_price_per_resource = 2.50  # $ per resource hour
        
        # Track accumulated revenue
        self.accumulated_revenue = 0.00  # $ from cloud workload
        self.previous_revenue = 0.00  # Track previous revenue for milestone detection
    
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
        font = QFont('Arial', int(14 * scale_factor))
        painter.setFont(font)
        
        # Draw the component main text
        component_text = f"Cloud Workload ({self.operating_mode})"
        painter.drawText(main_text_rect, Qt.AlignCenter, component_text)
        
        # Draw the revenue text if in revenue-generating mode
        if self.operating_mode in ["Multi-Cloud Spot", "Dedicated Capacity"]:
            revenue_text = f"Revenue: ${int(self.accumulated_revenue):,}"
            painter.drawText(revenue_rect, Qt.AlignCenter, revenue_text)
        
        # Restore painter state
        painter.restore()
    
    def is_directly_connected_to_load(self, load_component):
        """Check if this cloud workload is directly connected to a specific load component
        
        Args:
            load_component: The load component to check
            
        Returns:
            bool: True if directly connected, False otherwise
        """
        for connection in self.connections:
            if connection.source == load_component or connection.target == load_component:
                return True
        return False
    
    def calculate_cloud_revenue(self, load_component, energy_consumed, time_step=1.0):
        """Calculate cloud revenue based on load type and energy consumed
        
        Args:
            load_component: The load component to calculate revenue for
            energy_consumed: Energy consumed in kWh
            time_step: Time step in hours (default 1.0)
            
        Returns:
            Revenue generated in dollars
        """
        # Check if the load component is directly connected to this cloud workload
        if not self.is_directly_connected_to_load(load_component):
            return 0.0
            
        if self.operating_mode == "Multi-Cloud Spot" and load_component.profile_type == "Data Center":
            # Determine resources used based on data center type
            if load_component.data_center_type == "Traditional Cloud":
                power_per_resource = self.traditional_cloud_power
                price_per_resource = self.traditional_cloud_price
            elif load_component.data_center_type == "GPU Dense":
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

        elif self.operating_mode == "Dedicated Capacity" and load_component.profile_type == "Data Center":
            # For Dedicated Capacity mode, apply the power use efficiency factor
            # This makes it less efficient, requiring more power per resource
            effective_power_per_resource = self.dedicated_power_per_resource * self.dedicated_power_use_efficiency
            
            if effective_power_per_resource > 0:
                # For dedicated capacity, we charge for full utilization regardless of actual usage
                # This reflects real-world dedicated GPU pricing where customers pay for the full reserved capacity
                # Use the load component's full capacity (demand) instead of actual energy consumed
                
                # Calculate max potential energy for 1 hour at full capacity
                max_energy = load_component.demand * 1.0  # demand (kW) * 1 hour = energy (kWh)
                
                # Calculate resource hours based on full capacity
                resource_hours = max_energy / effective_power_per_resource
                
                # Revenue = resource hours * price per resource hour
                revenue = resource_hours * self.dedicated_price_per_resource
                return revenue
            
            return 0.0
        
        return 0.0
    
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
            center_y = self.y() + rect.height() / 3-75  # Position near the top of the component
            
            # Get the particle system
            if hasattr(parent, 'particle_system'):
                # Create a popup for each $1000 increment (in case we earned multiple $1000 in one step)
                for _ in range(current_thousands - previous_thousands):
                    parent.particle_system.create_revenue_popup(center_x, center_y, 1000)
        
        # Store current revenue for next check
        self.previous_revenue = self.accumulated_revenue
    
    def serialize(self):
        """Serialize the component data for saving"""
        data = {
            'type': 'cloud_workload',
            'x': self.x(),
            'y': self.y(),
            'operating_mode': self.operating_mode,
            'accumulated_revenue': self.accumulated_revenue,
            'previous_revenue': self.previous_revenue
        }
        
        # Add dedicated capacity parameters if in that mode
        if self.operating_mode == "Dedicated Capacity":
            data.update({
                'dedicated_power_per_resource': self.dedicated_power_per_resource,
                'dedicated_power_use_efficiency': self.dedicated_power_use_efficiency,
                'dedicated_price_per_resource': self.dedicated_price_per_resource
            })
            
        return data 