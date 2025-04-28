import numpy as np
import random
import csv
import os
from PyQt5.QtGui import QBrush, QColor, QPen, QFont, QPixmap
from PyQt5.QtCore import Qt, QRectF
from .base import ComponentBase
from .bus import BusComponent
from src.utils.resource import resource_path

class LoadComponent(ComponentBase):
    def __init__(self, x, y):
        # Initialize with the same size as the generator component
        super().__init__(x, y, 300, 220)
        # Make brush transparent (no background)
        self.setBrush(Qt.transparent)
        # Load the image
        self.image = QPixmap(resource_path("src/ui/assets/load.png"))
        
        self.demand = 2000  # kW
        self.price_per_kwh = 0.00  # Default price per kWh in dollars
        self.operating_mode = "Demand Droop (Auto)"  # Fixed operating mode
        self.accumulated_revenue = 0.00  # Track accumulated revenue in dollars
        self.previous_revenue = 0.00  # Track previous revenue for milestone detection
        self.profile_type = "Data Center"  # Constant, Sine Wave, Custom, Random 8760, Data Center, Powerlandia 60CF
        self.custom_profile = None
        self.profile_name = None
        self.time_offset = 0  # Hours to offset the time series
        self.frequency = 1.0  # Cycles per day (for Sine Wave mode)
        self.random_profile = None  # For Random 8760 mode
        self.max_ramp_rate = 0.25  # Maximum change in output per hour (25% default)
        self.data_center_type = "GPU Dense"  # Traditional Cloud, GPU Dense, Crypto ASIC
        self.graphics_enabled = True  # Flag to control whether graphics are shown
        self.powerlandia_profile = None  # For Powerlandia 60CF profile
        
        # Capital expenditure (CAPEX) property
        self.capex_per_kw = 17000  # $17,000 per kW default for load
    
    def paint(self, painter, option, widget):
        # Get component dimensions
        rect = self.boundingRect()
        
        if self.graphics_enabled:
            # Call base class paint to handle the shadow and selection highlight
            painter.save()
            super().paint(painter, option, widget)
            painter.restore()
            
            # Draw the image only if graphics are enabled
            # Calculate image area with 1:1 aspect ratio (square)
            # Using 80% of height for the larger image
            image_height = rect.height() * 0.8
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
                
            # Get current time step and calculate load factor (percent of demand)
            current_time = 0
            if self.scene() and hasattr(self.scene(), 'parent'):
                parent = self.scene().parent()
                if hasattr(parent, 'simulation_engine') and hasattr(parent.simulation_engine, 'current_time_step'):
                    current_time = parent.simulation_engine.current_time_step
            
            current_demand = self.calculate_demand(current_time)
            load_factor = current_demand / self.demand if self.demand > 0 else 0
            
            # Draw vertical load factor indicator in top right corner
            # Set indicator size relative to image size (smaller than before)
            indicator_width = image_size * 0.08
            indicator_height = image_size * 0.45
            indicator_padding = image_size * 0.04
            
            # Position indicator in top right corner with padding
            indicator_x = image_rect.x() + image_rect.width() - indicator_width - indicator_padding
            indicator_y = image_rect.y() + indicator_padding
            
            # Draw load factor frame (outline)
            painter.setPen(QPen(Qt.white, 1.5))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(int(indicator_x), int(indicator_y), int(indicator_width), int(indicator_height))
            
            # Determine fill color based on load factor - use gold with varying brightness
            # Darker gold for lower load, brighter gold for higher load
            if load_factor < 0.25:
                # Dark gold for low load (0-25%)
                fill_color = QColor("#8B6914")  # Dark gold
            elif load_factor < 0.5:
                # Medium gold for medium load (25-50%)
                fill_color = QColor("#B8860B")  # Medium gold
            elif load_factor < 0.75:
                # Regular gold for high load (50-75%)
                fill_color = QColor("#DAA520")  # Standard gold
            else:
                # Bright gold for maximum load (75-100%)
                fill_color = QColor("#FFD700")  # Bright gold
            
            # Draw filled portion representing current load factor (from bottom to top)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(fill_color))
            
            fill_height = indicator_height * load_factor
            # Calculate y-position for fill (starting from bottom of indicator)
            fill_y = indicator_y + (indicator_height - fill_height)
            
            painter.drawRect(int(indicator_x), int(fill_y), int(indicator_width), int(fill_height))
            
        else:
            # When graphics are disabled, still handle selection highlight but not shadow
            painter.save()
            
            # We need to handle the selection highlight manually
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
        
        # Calculate text area (remaining space below the image)
        text_rect = QRectF(
            rect.x(),
            rect.y() + (rect.height() * 0.7),  # Position text near bottom regardless of graphics state
            rect.width(),
            rect.height() * 0.3
        )
        
        # Split the text area into two parts for demand and revenue
        demand_rect = QRectF(
            text_rect.x(),
            text_rect.y(),
            text_rect.width(),
            text_rect.height() * 0.5
        )
        
        revenue_rect = QRectF(
            text_rect.x(),
            text_rect.y() + text_rect.height() * 0.5,
            text_rect.width(), 
            text_rect.height() * 0.5
        )
        
        # Draw the text in white
        painter.setPen(QPen(Qt.white))
        
        # Get the current view scale factor to adjust text size
        scale_factor = 1.0
        if self.scene() and self.scene().views():
            view = self.scene().views()[0]
            if hasattr(view, 'transform'):
                scale_factor = 1.0 / view.transform().m11()  # Get inverse of horizontal scale
        
        # Adjust text rectangles based on scale factor to prevent text clipping
        # Scale vertical spacing based on zoom level
        vertical_spacing = text_rect.height() * 0.5 * scale_factor
        
        # Recalculate text rectangles with adjusted dimensions
        scaled_text_height = text_rect.height() * scale_factor
        
        # Calculate the new width while maintaining the center position
        new_width = text_rect.width() * max(1.0, scale_factor)
        center_x = text_rect.x() + text_rect.width() / 2
        
        demand_rect = QRectF(
            center_x - new_width / 2,  # Position to maintain center alignment
            text_rect.y(),
            new_width,
            scaled_text_height * 0.5
        )
        
        revenue_rect = QRectF(
            center_x - new_width / 2,  # Position to maintain center alignment
            text_rect.y() + vertical_spacing,
            new_width,
            scaled_text_height * 0.5
        )
        
        # Set font with size adjusted for current zoom level
        font = QFont('Arial', int(14 * scale_factor))
        painter.setFont(font)
        
        # Draw the demand text centered below the image
        # Get current time step and calculate actual demand
        current_time = 0
        if self.scene() and hasattr(self.scene(), 'parent'):
            parent = self.scene().parent()
            if hasattr(parent, 'simulation_engine') and hasattr(parent.simulation_engine, 'current_time_step'):
                current_time = parent.simulation_engine.current_time_step
                
        current_demand = self.calculate_demand(current_time)
        demand_percentage = int((current_demand / self.demand) * 100) if self.demand > 0 else 0
        
        demand_text = f"{self.demand/1000:.1f} MW (Load) | {demand_percentage}%"
        painter.drawText(demand_rect, Qt.AlignCenter, demand_text)
        
        # Draw the revenue text
        revenue_text = f"Revenue: ${int(self.accumulated_revenue):,}"
        painter.drawText(revenue_rect, Qt.AlignCenter, revenue_text)
    
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
    
    def get_connected_bus(self):
        """Find the bus this load is connected to"""
        for connection in self.connections:
            if isinstance(connection.source, BusComponent):
                return connection.source
            if isinstance(connection.target, BusComponent):
                return connection.target
        return None
    
    def generate_random_profile(self):
        """Generate a random 8760 profile with ramp rate limiting"""
        if self.random_profile is None:
            # Initialize with random value between 0.3 and 1.0
            self.random_profile = [random.uniform(0.3, 1.0)]
            
            # Generate the rest of the values respecting max ramp rate
            for i in range(1, 8760):
                prev_value = self.random_profile[i-1]
                # Calculate max change allowed up or down
                max_change = self.max_ramp_rate
                # Random value within allowed range
                min_value = max(0.1, prev_value - max_change)
                max_value = min(1.0, prev_value + max_change)
                new_value = random.uniform(min_value, max_value)
                self.random_profile.append(new_value)
        
        return self.random_profile
    
    def generate_data_center_profile(self):
        """Generate a data center profile based on the selected type"""
        if self.profile_type != "Data Center":
            return None
            
        profile = []
        
        if self.data_center_type == "Traditional Cloud":
            # 80-90% annual load factor
            # 5-10% max inter-hourly ramp
            # Day/night cycle with day bias
            base_load_factor = random.uniform(0.8, 0.9)
            max_ramp = random.uniform(0.05, 0.1)
            
            # Initialize with day time value around the base load factor
            current_value = random.uniform(base_load_factor - 0.05, base_load_factor + 0.05)
            profile.append(current_value)
            
            for hour in range(1, 8760):
                time_of_day = hour % 24
                
                # Add day/night cycle pattern
                if 8 <= time_of_day <= 20:  # Daytime (8am-8pm)
                    # During the day, bias load higher
                    target = random.uniform(base_load_factor, min(1.0, base_load_factor + 0.1))
                else:  # Nighttime
                    # During the night, bias load lower
                    target = random.uniform(max(0.7, base_load_factor - 0.1), base_load_factor)
                
                # Apply ramp rate limitation
                max_change = max_ramp
                if target > current_value:
                    # Ramping up
                    current_value = min(target, current_value + max_change)
                else:
                    # Ramping down
                    current_value = max(target, current_value - max_change)
                
                profile.append(current_value)
        
        elif self.data_center_type == "GPU Dense":
            # 55% annual load factor
            # Up to 75% max inter-hourly ramp
            # Day/night cycle with lower usage at night
            base_load_factor = 0.6
            max_ramp = 0.75
            
            # Initialize with a value around the base load factor
            current_value = random.uniform(base_load_factor - 0.1, base_load_factor + 0.1)
            profile.append(current_value)
            
            for hour in range(1, 8760):
                time_of_day = hour % 24
                
                # Add day/night cycle pattern
                if 8 <= time_of_day <= 20:  # Daytime (8am-8pm)
                    # During the day, bias load higher for GPU workloads
                    target = random.uniform(0.6, 0.8)  # Higher range during day
                else:  # Nighttime
                    # During the night, bias load lower
                    target = random.uniform(0.3, 0.5)  # Lower range at night
                
                # Apply ramp rate limitation
                max_change = max_ramp
                if target > current_value:
                    # Ramping up
                    current_value = min(target, current_value + max_change)
                else:
                    # Ramping down
                    current_value = max(target, current_value - max_change)
                
                profile.append(current_value)
        
        elif self.data_center_type == "Crypto ASIC":
            # 90-100% load factor
            # Max 2% hourly change
            # No day/night cycle
            base_load_factor = random.uniform(0.9, 1.0)
            max_ramp = 0.02
            
            # Initialize with high value
            current_value = random.uniform(0.95, 1.0)
            profile.append(current_value)
            
            for _ in range(1, 8760):
                # Very small random changes to maintain high utilization
                target = random.uniform(0.9, 1.0)
                
                # Apply tight ramp rate limitation
                max_change = max_ramp
                if target > current_value:
                    # Ramping up
                    current_value = min(target, current_value + max_change)
                else:
                    # Ramping down
                    current_value = max(target, current_value - max_change)
                
                profile.append(current_value)
        
        self.random_profile = profile
        return profile
    
    def load_powerlandia_profile(self):
        """Load the Powerlandia 60CF profile from the CSV file"""
        # Clear any existing profile data
        self.powerlandia_profile = None
        
        try:
            # Path to the CSV file
            filepath = "src/data/Powerlandia-Load-60CF.csv"
            
            if not os.path.exists(filepath):
                print(f"Error: Could not find Powerlandia profile file at {filepath}")
                return None
                
            # Read the CSV file
            data = []
            with open(filepath, 'r') as f:
                reader = csv.reader(f)
                next(reader)  # Skip header row
                for row in reader:
                    if row and len(row) > 0:
                        data.append(float(row[0]))  # Assume first column is load factor
            
            if len(data) > 0:
                self.powerlandia_profile = data
                self.profile_name = "Powerlandia-Load-60CF.csv"
                return data
            else:
                print("Error: No data found in Powerlandia profile file")
                return None
                
        except Exception as e:
            print(f"Error loading Powerlandia profile: {str(e)}")
            return None
    
    def calculate_demand(self, time_step):
        # Check if connected to a bus
        bus = self.get_connected_bus()
        if bus is not None:
            # If connected to a bus, only draw power if the bus is on
            if not bus.is_on:
                return 0
        
        # Apply time offset if using Sine Wave or Custom profile
        adjusted_time_step = time_step
        if self.profile_type in ["Sine Wave", "Custom", "Powerlandia 60CF"] and self.time_offset != 0:
            adjusted_time_step = (time_step + self.time_offset) % 8760  # Wrap around at 8760 hours
        
        # Calculate normal demand based on profile
        if self.profile_type == "Constant":
            return self.demand
        elif self.profile_type == "Sine Wave":
            # Apply frequency adjustment (cycles per day)
            # Default is 1 cycle per day (24 hour period)
            period = 24 / max(0.1, self.frequency)  # Prevent division by zero or negative values
            return self.demand * (0.5 + 0.5 * np.sin(2 * np.pi * adjusted_time_step / period))
        elif self.profile_type == "Custom" and self.custom_profile is not None:
            # Use custom time series if available
            if adjusted_time_step < len(self.custom_profile):
                return self.custom_profile[adjusted_time_step] * self.demand  # Scale by demand
            return self.demand  # Default to constant if beyond data range
        elif self.profile_type == "Random 8760":
            # Generate random profile if not already generated
            profile = self.generate_random_profile()
            if time_step < len(profile):
                return profile[time_step] * self.demand  # Scale by demand
            return self.demand  # Default to constant if beyond data range
        elif self.profile_type == "Data Center":
            # Generate data center profile if not already generated
            if not self.random_profile:
                self.generate_data_center_profile()
            
            if self.random_profile and time_step < len(self.random_profile):
                return self.random_profile[time_step] * self.demand
            return self.demand
        elif self.profile_type == "Powerlandia 60CF":
            # Load Powerlandia profile if not already loaded
            if not self.powerlandia_profile:
                self.load_powerlandia_profile()
            
            if self.powerlandia_profile and adjusted_time_step < len(self.powerlandia_profile):
                return self.powerlandia_profile[adjusted_time_step] * self.demand
            return self.demand
        return self.demand
    
    def serialize(self):
        """Serialize the component data for saving"""
        data = {
            'type': 'load',
            'x': self.x(),
            'y': self.y(),
            'demand': self.demand,
            'price_per_kwh': self.price_per_kwh,
            'operating_mode': self.operating_mode,
            'accumulated_revenue': self.accumulated_revenue,
            'previous_revenue': self.previous_revenue,  # Save previous revenue state
            'profile_type': self.profile_type,
            'custom_profile': self.custom_profile,
            'profile_name': self.profile_name,
            'time_offset': self.time_offset,
            'frequency': self.frequency,
            'max_ramp_rate': self.max_ramp_rate,
            'random_profile': self.random_profile,
            'data_center_type': self.data_center_type,
            'graphics_enabled': self.graphics_enabled,  # Save graphics state
            'powerlandia_profile': self.powerlandia_profile,  # Save Powerlandia profile
            'capex_per_kw': self.capex_per_kw
        } 
        return data 