from PyQt5.QtGui import QBrush, QColor, QPen, QFont, QPixmap
from PyQt5.QtCore import Qt, QRectF
from .base import ComponentBase
import os
from src.utils.resource import resource_path

class WindTurbineComponent(ComponentBase):
    def __init__(self, x, y):
        # Initialize with a larger size to accommodate bigger image
        super().__init__(x, y, 300, 220)  # Same size as other components
        # Make brush transparent (no background)
        self.setBrush(Qt.transparent)
        # Load the image
        self.image = QPixmap(resource_path("src/ui/assets/windturbine.png"))
        
        # Wind turbine properties
        self.capacity = 5000  # kW - default capacity
        self.operating_mode = "Disabled"  # Start in disabled mode
        self.capacity_factors = None  # Will hold data from CSV file
        self.last_output = 0  # Track the last output for display
        self.custom_profile = None  # Will hold custom profile data
        self.profile_name = None  # Will store the name of the loaded profile
        
        # Capital expenditure (CAPEX) property
        self.capex_per_kw = 2000  # $2,000 per kW default for wind turbine
    
    def paint(self, painter, option, widget):
        # Call base class paint to handle the selection highlight
        painter.save()
        super().paint(painter, option, widget)
        painter.restore()
        
        # Get component dimensions
        rect = self.boundingRect()
        
        # Calculate image area with 1:1 aspect ratio (square)
        # Using 80% of height for the larger image
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
        
        # Draw the image with transparent background and 1:1 aspect ratio
        if not self.image.isNull():
            painter.drawPixmap(
                image_rect,
                self.image,
                QRectF(0, 0, self.image.width(), self.image.height())
            )
            
            # Calculate output percentage
            if self.capacity > 0:
                output_percentage = self.last_output / self.capacity
            else:
                output_percentage = 0
            
            # Draw vertical output indicator in top right corner
            # Set indicator size relative to image size
            indicator_width = image_size * 0.08
            indicator_height = image_size * 0.45
            indicator_padding = image_size * 0.04
            
            # Position indicator in top right corner with padding
            indicator_x = image_rect.x() + image_rect.width() - indicator_width - indicator_padding
            indicator_y = image_rect.y() + indicator_padding
            
            # Draw output indicator frame (outline)
            painter.setPen(QPen(Qt.white, 1.5))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(int(indicator_x), int(indicator_y), int(indicator_width), int(indicator_height))
            
            # Determine fill color based on output percentage - use green with varying brightness
            # Darker green for lower output, brighter green for higher output
            if output_percentage < 0.25:
                # Dark green for low output (0-25%)
                fill_color = QColor("#006400")  # Dark green
            elif output_percentage < 0.5:
                # Medium-dark green for medium-low output (25-50%)
                fill_color = QColor("#228B22")  # Forest green
            elif output_percentage < 0.75:
                # Medium green for medium-high output (50-75%)
                fill_color = QColor("#32CD32")  # Lime green
            else:
                # Bright green for maximum output (75-100%)
                fill_color = QColor("#7CFC00")  # Lawn green
            
            # Draw filled portion representing current output percentage (from bottom to top)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(fill_color))
            
            fill_height = indicator_height * output_percentage
            # Calculate y-position for fill (starting from bottom of indicator)
            fill_y = indicator_y + (indicator_height - fill_height)
            
            painter.drawRect(int(indicator_x), int(fill_y), int(indicator_width), int(fill_height))
        
        # Calculate text area (remaining space below the image)
        text_rect = QRectF(
            rect.x(),
            rect.y() + image_size + (rect.height() * 0.05),  # Position below image with margin
            rect.width(),
            rect.height() * 0.2
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
        
        # Get current output percentage
        if self.capacity > 0:
            output_percentage = int((self.last_output / self.capacity) * 100)
        else:
            output_percentage = 0
        
        # Draw the operating mode text
        status_text = f"{self.capacity/1000:.1f} MW (wind) | {output_percentage}%"
        painter.drawText(text_rect, Qt.AlignCenter, status_text)
    
    def load_capacity_factors(self):
        """Load capacity factors from CSV file"""
        if self.capacity_factors is None:
            # Load data from CSV file
            csv_path = "src/data/Powerlandia-WindGen-Year1.csv"
            
            if os.path.exists(csv_path):
                try:
                    self.capacity_factors = []
                    with open(csv_path, 'r', encoding='utf-8-sig') as file:  # utf-8-sig handles BOM character
                        # Read each line and convert to float
                        for line in file:
                            line = line.strip()
                            if line:  # Skip empty lines
                                try:
                                    self.capacity_factors.append(float(line))
                                except ValueError:
                                    # Skip lines that can't be converted to float
                                    print(f"Warning: Could not convert '{line}' to float, skipping.")
                            
                    # Ensure we have enough data (8760 hours)
                    if len(self.capacity_factors) < 8760:
                        print(f"Warning: CSV file has only {len(self.capacity_factors)} entries, expected 8760.")
                        # Pad with zeros if needed
                        self.capacity_factors.extend([0.0] * (8760 - len(self.capacity_factors)))
                except Exception as e:
                    print(f"Error loading capacity factors: {e}")
                    self.capacity_factors = [0.0] * 8760  # Default to zero on error
            else:
                print(f"File not found: {csv_path}")
                self.capacity_factors = [0.0] * 8760  # Default to zero if file not found
    
    def calculate_output(self, total_load):
        """Calculate wind turbine output based on capacity and capacity factors"""
        # If in disabled mode, return 0
        if self.operating_mode == "Disabled":
            self.last_output = 0
            return 0
            
        # If in Powerlandia mode, calculate output based on capacity factors
        if self.operating_mode == "Powerlandia 8760 - Midwest 1":
            # Load capacity factors if not already loaded
            if self.capacity_factors is None:
                self.load_capacity_factors()
                
            # Get current time step from the simulation engine
            current_time = 0
            if self.scene() and hasattr(self.scene(), 'parent'):
                parent = self.scene().parent()
                if hasattr(parent, 'simulation_engine') and hasattr(parent.simulation_engine, 'current_time_step'):
                    current_time = parent.simulation_engine.current_time_step
            
            # Get capacity factor for current hour (wrap around if beyond 8760)
            hour_index = current_time % len(self.capacity_factors)
            capacity_factor = self.capacity_factors[hour_index] / 10 # divide by 10 to scale down to 0-1, fix because data file is 0-10 not 0-1
            
            # Calculate output based on capacity and capacity factor
            self.last_output = self.capacity * capacity_factor
            return self.last_output
        
        # If in Custom mode, use custom profile data    
        if self.operating_mode == "Custom" and self.custom_profile is not None:
            # Get current time step from the simulation engine
            current_time = 0
            if self.scene() and hasattr(self.scene(), 'parent'):
                parent = self.scene().parent()
                if hasattr(parent, 'simulation_engine') and hasattr(parent.simulation_engine, 'current_time_step'):
                    current_time = parent.simulation_engine.current_time_step
            
            # Get capacity factor for current hour (wrap around if beyond profile length)
            if current_time < len(self.custom_profile):
                capacity_factor = self.custom_profile[current_time]
            else:
                # Wrap around if needed
                hour_index = current_time % len(self.custom_profile)
                capacity_factor = self.custom_profile[hour_index]
            
            # Calculate output based on capacity and capacity factor
            self.last_output = self.capacity * capacity_factor
            return self.last_output
            
        # Default case (should not reach here)
        return 0
    
    def serialize(self):
        return {
            'type': 'wind_turbine',
            'x': self.x(),
            'y': self.y(),
            'capacity': self.capacity,
            'operating_mode': self.operating_mode,
            'custom_profile': self.custom_profile,
            'profile_name': self.profile_name,
            'capex_per_kw': self.capex_per_kw
        } 