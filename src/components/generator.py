from PyQt5.QtGui import QPen, QFont, QPixmap
from PyQt5.QtCore import Qt, QRectF, QPointF
from .base import ComponentBase
from src.utils.resource import resource_path

class GeneratorComponent(ComponentBase):
    def __init__(self, x, y):
        # Initialize with a larger size to accommodate bigger image
        super().__init__(x, y, 300, 220)  # Increase component size
        # Make brush transparent (no background)
        self.setBrush(Qt.transparent)
        # Load the image
        self.image = QPixmap(resource_path("src/ui/assets/generator.png"))
        
        self.capacity = 1000  # kW
        self.operating_mode = "BTF Droop (Auto)"  # Static (Auto), BTF Unit Commitment (Auto), or BTF Droop (Auto)
        self.output_level = 1.0  # Fraction of capacity (0-1) for static mode
        self.ramp_rate_enabled = False  # Whether ramp rate limiting is enabled
        self.ramp_rate_limit = 0.2  # Maximum change in output per hour (20% - slowest)
        self.last_output = 0  # Track the last output for ramp rate limiting
        self.auto_charging = True  # Whether this generator can be used to charge batteries
        
        # Gas consumption and cost properties
        self.conversion_constant = 277.78  # 1 GJ of gas = 277.78 kWh of electricity
        self.efficiency = 0.40  # 40% efficiency by default
        self.cost_per_gj = 3.00  # $3.00 per GJ by default
        self.accumulated_cost = 0.00  # Track accumulated cost in dollars
        self.previous_cost = 0.00  # Track previous cost for milestone detection
        
        # Capital expenditure (CAPEX) property
        self.capex_per_kw = 2000  # $2,000 per kW default for gas generator
        
        # Maintenance parameters
        self.frequency_per_10000_hours = 5.0  # Default: 5 occurrences per 10,000 operating hours
        self.minimum_downtime = 4  # Default: 4 hours minimum downtime per maintenance event
        self.maximum_downtime = 96  # Default: 96 hours maximum downtime per maintenance event
        self.cooldown_time = 2000  # Default: 2000 hours between maintenance events
        
        # Maintenance state tracking
        self.is_in_maintenance = False  # Whether generator is currently in maintenance
        self.maintenance_time_remaining = 0  # Hours remaining in current maintenance event
        self.cooldown_time_remaining = 0  # Hours remaining in cooldown period
        self.total_operating_hours = 0  # Total hours generator has been operating
        
        # Smoke emission point (will be calculated in paint)
        self.smoke_point = QPointF(0, 0)
        # Timer for smoke emission
        self.smoke_timer = None
    
    def paint(self, painter, option, widget):
        # Call base class paint to handle the selection highlight
        painter.save()
        super().paint(painter, option, widget)
        painter.restore()
        
        # Get component dimensions
        rect = self.boundingRect()
        
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
        
        # Calculate text area (remaining space below the image)
        text_rect = QRectF(
            rect.x(),
            rect.y() + image_size + (rect.height() * 0.05),  # Position below image with margin
            rect.width(),
            rect.height() - image_size - (rect.height() * 0.05)
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
        scaled_text_height = text_rect.height() * scale_factor
        vertical_spacing = 2 * scale_factor
        
        # Create scaled text rectangle
        scaled_text_rect = QRectF(
            text_rect.x(),
            text_rect.y(),
            text_rect.width(),
            scaled_text_height
        )
        
        # Scale cost rectangle
        scaled_cost_rect = QRectF(
            rect.x(),
            rect.y() + rect.height() + vertical_spacing,  # Position at bottom with margin
            rect.width(),
            25 * scale_factor
        )
        
        # Set font with size adjusted for current zoom level
        font = QFont('Arial', int(14 * scale_factor))
        painter.setFont(font)
        
        # Get the current output percentage based on actual output
        # First get the current time step from the simulation engine
        current_time = 0
        if self.scene() and hasattr(self.scene(), 'parent'):
            parent = self.scene().parent()
            if hasattr(parent, 'simulation_engine') and hasattr(parent.simulation_engine, 'current_time_step'):
                current_time = parent.simulation_engine.current_time_step
        
        # Add maintenance status text if generator is in maintenance
        if self.is_in_maintenance:
            output_percentage = 0  # Output is 0 during maintenance
            # Draw capacity info with maintenance status
            capacity_text = f"{self.capacity/1000:.1f} MW (gas) | MAINTENANCE ({self.maintenance_time_remaining}h)"
        else:
            # In Static (Auto) mode, use output_level as percentage
            # In BTF Unit Commitment (Auto) mode, calculate actual output based on system load
            # In BTF Droop (Auto) mode, share load equally with other droop-mode generators
            if self.operating_mode == "Static (Auto)":
                output_percentage = int(self.output_level * 100)
            else:
                # Instead of recalculating the output, use the last_output value
                # which is set correctly by the simulation engine
                output_percentage = int((self.last_output / self.capacity) * 100) if self.capacity > 0 else 0
            
            # Draw the capacity, generation level and type text centered below the image
            capacity_text = f"{self.capacity/1000:.1f} MW (gas) | {output_percentage}%"
        
        painter.drawText(scaled_text_rect, Qt.AlignCenter, capacity_text)
        
        # Add cost display (always visible, even when cost is 0)
        cost_text = f"Cost: ${int(self.accumulated_cost):,}"
        painter.drawText(scaled_cost_rect, Qt.AlignCenter, cost_text)
        
        # Calculate and store the smoke emission point (top-center of the image)
        self.smoke_point = QPointF(
            self.x() + rect.width() / 2 - 25,  # Center X with offset
            self.y() + rect.y() + (rect.height() * 0.05) + image_size * 0.2 - 25  # Near top of image with offset
        )
    
    def emit_smoke(self):
        """Emit smoke particles based on current generation level"""
        if not self.scene() or not hasattr(self.scene(), 'parent'):
            return
        
        # Get the parent window to access particle system
        parent = self.scene().parent()
        if not hasattr(parent, 'particle_system') or not parent.particle_system:
            return
            
        # Don't emit smoke if generator is in maintenance
        if self.is_in_maintenance:
            return
            
        # Only emit smoke if generator is actually producing power
        if self.capacity <= 0 or self.last_output <= 0:
            return
            
        # Calculate intensity based on generation percentage (0.0 to 1.0)
        intensity = self.last_output / self.capacity
        
        # Create smoke particles at the emission point with calculated intensity
        parent.particle_system.create_generator_smoke(
            self.smoke_point.x(), 
            self.smoke_point.y(), 
            intensity
        )
    
    def calculate_output(self, total_load):
        # Update maintenance status based on operating hours
        self._update_maintenance_status()
        
        # If the generator is in maintenance, output is 0
        if self.is_in_maintenance:
            self.last_output = 0
            return 0
        
        # Only increment operating hours if we're actually generating power
        if self.last_output > 0:
            self.total_operating_hours += 1
            
        # Calculate target output based on operating mode
        if self.operating_mode == "Static (Auto)":
            target_output = self.capacity * self.output_level
        elif self.operating_mode == "BTF Unit Commitment (Auto)":
            # Return the minimum of total load or generator capacity
            target_output = min(total_load, self.capacity)
            # If in BTF Unit Commitment (Auto) mode and total_load is 0, we should return 0
            # This ensures generators correctly report no output when no load remains
            if total_load == 0:
                target_output = 0
        elif self.operating_mode == "BTF Droop (Auto)":
            # This mode is handled differently in the simulation engine
            # as all droop generators need to coordinate together
            # Just return the current output - the engine will update it
            return self.last_output
        
        # Apply ramp rate limiting if enabled
        if self.ramp_rate_enabled and self.last_output > 0:
            # Calculate maximum change allowed (as kW)
            max_change = self.capacity * self.ramp_rate_limit
            
            # Limit the change in output
            if target_output > self.last_output:
                # Ramping up
                actual_output = min(target_output, self.last_output + max_change)
            else:
                # Ramping down
                actual_output = max(target_output, self.last_output - max_change)
        else:
            actual_output = target_output
        
        # Save this output for next time step
        self.last_output = actual_output
        return actual_output
        
    def _update_maintenance_status(self):
        """Update the maintenance status of the generator based on current state and random factors."""
        import random
        
        # If the generator is already in maintenance, decrease the remaining time
        if self.is_in_maintenance:
            self.maintenance_time_remaining -= 1
            
            # Check if maintenance is finished
            if self.maintenance_time_remaining <= 0:
                self.is_in_maintenance = False
                self.maintenance_time_remaining = 0
                # Start cooldown period
                self.cooldown_time_remaining = self.cooldown_time
        
        # If the generator is in cooldown, decrease the remaining time
        elif self.cooldown_time_remaining > 0:
            self.cooldown_time_remaining -= 1
        
        # If not in maintenance or cooldown, check for random outage
        elif self.last_output > 0:  # Only check if generator is operating
            # Calculate hourly probability of maintenance from frequency per 10,000 hours
            hourly_probability = self.frequency_per_10000_hours / 10000.0
            
            # Generate random number and check against probability
            if random.random() < hourly_probability:
                # Start a maintenance event
                self.is_in_maintenance = True
                
                # Calculate random maintenance duration within allowed range
                self.maintenance_time_remaining = random.randint(
                    self.minimum_downtime, 
                    self.maximum_downtime
                )
                
    def update(self):
        """Called when the component needs to be updated"""
        # Call the parent's update method
        super().update()
        
        # Check for cost milestones
        self.check_cost_milestone()
    
    def calculate_gas_consumption(self, electricity_kwh):
        """Calculate gas consumption in GJ based on electricity generated"""
        if self.efficiency <= 0:
            return 0
        
        # Convert kWh of electricity to GJ of gas considering efficiency
        # 1 GJ = 277.78 kWh at 100% efficiency
        # At lower efficiency, more gas is needed
        gas_gj = electricity_kwh / (self.conversion_constant * self.efficiency)
        return gas_gj
    
    def calculate_gas_cost(self, gas_gj):
        """Calculate cost of gas consumption"""
        return gas_gj * self.cost_per_gj
    
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
            center_y = self.y() + rect.height() / 3  # Position near the top of the component
            
            # Get the particle system
            if hasattr(parent, 'particle_system'):
                # Create a popup for each $1000 increment (in case we spent multiple $1000 in one step)
                for _ in range(current_thousands - previous_thousands):
                    parent.particle_system.create_cost_popup(center_x, center_y, 1000)
        
        # Store current cost for next check
        self.previous_cost = self.accumulated_cost
    
    def serialize(self):
        return {
            'type': 'generator',
            'x': self.x(),
            'y': self.y(),
            'capacity': self.capacity,
            'operating_mode': self.operating_mode,
            'output_level': self.output_level,
            'ramp_rate_enabled': self.ramp_rate_enabled,
            'ramp_rate_limit': self.ramp_rate_limit,
            'auto_charging': self.auto_charging,
            'efficiency': self.efficiency,
            'cost_per_gj': self.cost_per_gj,
            'accumulated_cost': self.accumulated_cost,
            'capex_per_kw': self.capex_per_kw,
            'frequency_per_10000_hours': self.frequency_per_10000_hours,
            'minimum_downtime': self.minimum_downtime,
            'maximum_downtime': self.maximum_downtime,
            'cooldown_time': self.cooldown_time
        } 