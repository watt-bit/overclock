from PyQt5.QtGui import QBrush, QColor, QPen, QFont, QPixmap
from PyQt5.QtCore import Qt, QRectF
from .base import ComponentBase
import os
from src.utils.resource import resource_path

class GridImportComponent(ComponentBase):
    def __init__(self, x, y):
        # Initialize with the same size as other components
        super().__init__(x, y, 300, 220)
        # Make brush transparent (no background)
        self.setBrush(Qt.transparent)
        # Load the image
        self.image = QPixmap(resource_path("src/ui/assets/grid_import.png"))
        
        self.capacity = 2000  # kW - maximum import capacity
        self.operating_mode = "Last Resort Unit (Auto)"  # Only Auto mode for now
        self.auto_charge_batteries = False  # Whether this component will charge batteries with grid power
        self.cost_per_kwh = 0.00  # $/kWh - cost paid for imported power
        self.accumulated_cost = 0.00  # Track accumulated cost in dollars
        self.previous_cost = 0.00  # Track previous cost for milestone detection
        self.last_import = 0  # Track the last import amount for display
        
        # Market import prices properties
        self.market_prices_mode = "None"  # Default mode - no market prices
        self.market_prices = None  # Will hold data from CSV file
        self.custom_profile = None  # Will hold custom profile data
        self.profile_name = None  # Will store the name of the loaded profile
    
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
                import_percentage = min(1.0, self.last_import / self.capacity)
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
            painter.drawRect(int(indicator_x), int(indicator_y), int(indicator_width), int(indicator_height))
            
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
            
            painter.drawRect(int(indicator_x), int(fill_y), int(indicator_width), int(fill_height))
        
        # Calculate text area (remaining space below the image)
        text_rect = QRectF(
            rect.x(),
            rect.y() + image_size + (rect.height() * 0.05) - 40,  # Position below image with margin
            rect.width(),
            rect.height() - image_size - (rect.height() * 0.05) + 40
        )
        
        # Split the text area into two parts for capacity and cost
        capacity_rect = QRectF(
            text_rect.x(),
            text_rect.y(),
            text_rect.width(),
            text_rect.height() * 0.5
        )
        
        cost_rect = QRectF(
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
        
        # Adjust text rectangles based on scale factor to prevent text clipping
        # Scale vertical spacing based on zoom level
        vertical_spacing = 20 * scale_factor
        
        # Recalculate text rectangles with adjusted dimensions
        scaled_text_height = text_rect.height() * scale_factor
        
        capacity_rect = QRectF(
            text_rect.x(),
            text_rect.y(),
            text_rect.width(),
            scaled_text_height * 0.5
        )
        
        cost_rect = QRectF(
            text_rect.x(),
            text_rect.y() + (scaled_text_height * 0.5) + vertical_spacing,
            text_rect.width(), 
            scaled_text_height * 0.5
        )
        
        # Set font with size adjusted for current zoom level
        font = QFont('Arial', int(14 * scale_factor))
        painter.setFont(font)
        
        # Draw the capacity text
        capacity_text = f"{self.capacity/1000:.1f} MW (import)"
        painter.drawText(capacity_rect, Qt.AlignCenter, capacity_text)
        
        # Draw the cost text if price is set
        if self.cost_per_kwh > 0 or self.market_prices_mode != "None":
            cost_text = f"Cost: ${int(self.accumulated_cost):,}"
            painter.drawText(cost_rect, Qt.AlignCenter, cost_text)
        
        # Restore painter state
        painter.restore()
    
    def load_market_prices(self):
        """Load market prices from CSV file"""
        if self.market_prices is None and self.market_prices_mode == "Powerlandia 8760 Wholesale - Year 1":
            # Load data from CSV file
            csv_path = "src/data/Powerlandia-poolprices-year1.csv"
            
            if os.path.exists(csv_path):
                try:
                    self.market_prices = []
                    with open(csv_path, 'r', encoding='utf-8-sig') as file:  # utf-8-sig handles BOM character
                        # Read each line and convert to float
                        for line in file:
                            line = line.strip()
                            if line:  # Skip empty lines
                                try:
                                    self.market_prices.append(float(line))
                                except ValueError:
                                    # Skip lines that can't be converted to float
                                    print(f"Warning: Could not convert '{line}' to float, skipping.")
                            
                    # Ensure we have enough data (8760 hours)
                    if len(self.market_prices) < 8760:
                        print(f"Warning: CSV file has only {len(self.market_prices)} entries, expected 8760.")
                        # Pad with zeros if needed
                        self.market_prices.extend([0.0] * (8760 - len(self.market_prices)))
                except Exception as e:
                    print(f"Error loading market prices: {e}")
                    self.market_prices = [0.0] * 8760  # Default to zero on error
            else:
                print(f"File not found: {csv_path}")
                self.market_prices = [0.0] * 8760  # Default to zero if file not found
    
    def get_current_market_price(self, current_time):
        """Get the current market price for the given time step"""
        # If not using market prices, return 0
        if self.market_prices_mode == "None":
            return 0.0
            
        # If using Powerlandia 8760 market prices, use the CSV data
        if self.market_prices_mode == "Powerlandia 8760 Wholesale - Year 1":
            # Load market prices if not already loaded
            if self.market_prices is None:
                self.load_market_prices()
                
            # Get price for current hour (wrap around if beyond 8760)
            hour_index = current_time % len(self.market_prices)
            return self.market_prices[hour_index]
        
        # If using Custom mode, use custom profile data    
        if self.market_prices_mode == "Custom" and self.custom_profile is not None:
            # Get price for current hour (wrap around if beyond profile length)
            if current_time < len(self.custom_profile):
                return self.custom_profile[current_time]
            else:
                # Wrap around if needed
                hour_index = current_time % len(self.custom_profile)
                return self.custom_profile[hour_index]
            
        # Default case (should not reach here)
        return 0.0
    
    def calculate_output(self, deficit):
        """Calculate grid import based on system deficit"""
        # Provide power up to capacity to meet deficit
        import_amount = min(deficit, self.capacity)
        self.last_import = import_amount  # Track the last import amount
        return import_amount
    
    def update(self):
        """Called when the component needs to be updated"""
        # Call the parent's update method
        super().update()
        
        # Check for cost milestones
        self.check_cost_milestone()
    
    def check_cost_milestone(self):
        """Check if cost has crossed a $1000 milestone and create a particle if needed"""
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
            # Store current cost as previous and exit
            self.previous_cost = self.accumulated_cost
            return
        
        # Calculate how many $1000 increments we've crossed
        previous_thousands = int(self.previous_cost / 1000)
        current_thousands = int(self.accumulated_cost / 1000)
        
        if current_thousands > previous_thousands:
            # We've crossed at least one $1000 milestone
            # Get the center point of the component for particle origin
            rect = self.boundingRect()
            center_x = self.x() + rect.width() / 2
            center_y = self.y() + rect.height() / 3-50  # Position near the top of the component
            
            # Get the particle system
            if hasattr(parent, 'particle_system'):
                # Create a popup for each $1000 increment (in case we spent multiple $1000 in one step)
                for _ in range(current_thousands - previous_thousands):
                    parent.particle_system.create_cost_popup(center_x, center_y-75, 1000)
        
        # Store current cost for next check
        self.previous_cost = self.accumulated_cost
    
    def serialize(self):
        return {
            'type': 'grid_import',
            'x': self.x(),
            'y': self.y(),
            'capacity': self.capacity,
            'operating_mode': self.operating_mode,
            'auto_charge_batteries': self.auto_charge_batteries,
            'cost_per_kwh': self.cost_per_kwh,
            'accumulated_cost': self.accumulated_cost,
            'previous_cost': self.previous_cost,
            'last_import': self.last_import,
            'market_prices_mode': self.market_prices_mode,
            'custom_profile': self.custom_profile,
            'profile_name': self.profile_name
        } 