from PyQt5.QtGui import QBrush, QColor, QPen, QPainter, QFont, QPixmap
from PyQt5.QtCore import Qt, QRectF
from .base import ComponentBase

class GeneratorComponent(ComponentBase):
    def __init__(self, x, y):
        # Initialize with a larger size to accommodate bigger image
        super().__init__(x, y, 300, 220)  # Increase component size
        # Make brush transparent (no background)
        self.setBrush(Qt.transparent)
        # Load the image
        self.image = QPixmap("src/ui/assets/generator.png")
        
        self.capacity = 1000  # kW
        self.operating_mode = "BTF Droop (Auto)"  # Static (Auto), BTF Unit Commitment (Auto), or BTF Droop (Auto)
        self.output_level = 1.0  # Fraction of capacity (0-1) for static mode
        self.ramp_rate_enabled = False  # Whether ramp rate limiting is enabled
        self.ramp_rate_limit = 0.2  # Maximum change in output per hour (20% - slowest)
        self.last_output = 0  # Track the last output for ramp rate limiting
        self.auto_charging = True  # Whether this generator can be used to charge batteries
    
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
        
        # Set font with size adjusted for current zoom level
        font = QFont('Arial', 14 * scale_factor)
        painter.setFont(font)
        
        # Get the current output percentage based on actual output
        # First get the current time step from the simulation engine
        current_time = 0
        if self.scene() and hasattr(self.scene(), 'parent'):
            parent = self.scene().parent()
            if hasattr(parent, 'simulation_engine') and hasattr(parent.simulation_engine, 'current_time_step'):
                current_time = parent.simulation_engine.current_time_step
        
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
        capacity_text = f"{self.capacity} kW (gas) | {output_percentage}%"
        painter.drawText(text_rect, Qt.AlignCenter, capacity_text)
    
    def calculate_output(self, total_load):
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
            # Return last_output to avoid recalculation
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
            'auto_charging': self.auto_charging
        } 