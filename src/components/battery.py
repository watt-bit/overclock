from PyQt5.QtGui import QBrush, QColor, QPen, QFont, QPixmap, QRadialGradient
from PyQt5.QtCore import Qt, QRectF
from .base import ComponentBase

class BatteryComponent(ComponentBase):
    def __init__(self, x, y):
        # Initialize with the same size as other components
        super().__init__(x, y, 300, 220)
        # Make brush transparent (no background)
        self.setBrush(Qt.transparent)
        # Load the image
        self.image = QPixmap("src/ui/assets/battery.png")
        
        # Battery properties
        self.power_capacity = 1000  # kW - maximum charge/discharge rate
        self.energy_capacity = 4000  # kWh - total storage capacity
        self.current_charge = self.energy_capacity  # Start at 100% charge
        self.operating_mode = "BTF Basic Unit (Auto)"  # "Off" or "BTF Basic Unit (Auto)"
        
    def paint(self, painter, option, widget):
        # Save painter state
        painter.save()
        
        # Draw the shadow first (before the component)
        rect = self.boundingRect()
        
        # Create a shadow ellipse at the bottom of the component - 75% as wide for battery
        shadow_width = rect.width() * 0.675    # 75% of normal (0.9 * 0.75)
        shadow_height = rect.height() * 0.3   # 75% of normal height (0.4 * 0.75)
        
        # Position the shadow beneath the component with offset
        shadow_x = rect.x() + (rect.width() - shadow_width) / 2 + 15
        shadow_y = rect.y() + rect.height() - shadow_height / 2 + self.shadow_y_offset - 5
        
        # Create a radial gradient for the shadow
        gradient = QRadialGradient(
            shadow_x + shadow_width / 2,
            shadow_y + shadow_height / 2,
            shadow_width / 2
        )
        gradient.setColorAt(0, QColor(0, 0, 0, 255 * self.shadow_opacity))
        gradient.setColorAt(1, QColor(0, 0, 0, 0))
        
        # Draw the shadow
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(shadow_x, shadow_y, shadow_width, shadow_height)
        
        # Restore painter state after drawing shadow
        painter.restore()
        
        # Now call the base class to handle the selection highlight
        painter.save()
        super(ComponentBase, self).paint(painter, option, widget)
        
        # If selected, draw white highlight box around the component
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
        
        # Draw battery level indicator in top right corner
        # Ensure current charge never exceeds energy capacity
        if self.current_charge > self.energy_capacity:
            self.current_charge = self.energy_capacity
            
        # Calculate charge percentage
        charge_percent = self.current_charge / self.energy_capacity if self.energy_capacity > 0 else 0
        
        # Set indicator size relative to image size
        indicator_width = image_size * 0.3
        indicator_height = image_size * 0.1
        indicator_padding = image_size * 0.04
        
        # Position indicator in top right corner with padding
        indicator_x = image_rect.x() + image_rect.width() - indicator_width - indicator_padding
        indicator_y = image_rect.y() + indicator_padding
        
        # Draw battery level frame (outline)
        painter.setPen(QPen(Qt.white, 1.5))
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(indicator_x, indicator_y, indicator_width, indicator_height)
        
        # Determine fill color based on charge level
        if charge_percent < 0.25:
            # Dark red for low charge (0-25%)
            fill_color = QColor("#B71C1C")
        elif charge_percent < 0.5:
            # Gold/amber for medium charge (25-50%)
            fill_color = QColor("#FFC107")
        else:
            # Dark green for high charge (50-100%)
            fill_color = QColor("#1B5E20")
        
        # Draw filled portion representing current charge
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(fill_color))
        fill_width = indicator_width * charge_percent
        painter.drawRect(indicator_x, indicator_y, fill_width, indicator_height)
        
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
        
        # Calculate charge percentage
        if self.energy_capacity > 0:
            charge_percent_display = int((self.current_charge / self.energy_capacity) * 100)
        else:
            charge_percent_display = 0  # Default to 0% if energy capacity is zero
        
        # Draw the battery information
        battery_text = f"{self.power_capacity} kW (battery) | {charge_percent_display}% charge"
        painter.drawText(text_rect, Qt.AlignCenter, battery_text)
    
    def has_energy(self):
        """Check if battery has any stored energy"""
        return self.current_charge > 0
    
    def has_capacity(self):
        """Check if battery has any remaining capacity for charging"""
        return self.current_charge < self.energy_capacity
    
    def calculate_max_discharge(self, time_step=1.0):
        """Calculate maximum potential discharge in kWh for the given time step"""
        # Limited by both power capacity and available energy
        max_power_output = self.power_capacity  # kW
        max_energy_output = max_power_output * time_step  # kWh
        
        return min(max_energy_output, self.current_charge)
    
    def calculate_max_charge(self, time_step=1.0):
        """Calculate maximum potential charge in kWh for the given time step"""
        # Limited by both power capacity and remaining capacity
        max_power_input = self.power_capacity  # kW
        max_energy_input = max_power_input * time_step  # kWh
        remaining_capacity = self.energy_capacity - self.current_charge
        
        return min(max_energy_input, remaining_capacity)
    
    def discharge(self, amount, time_step=1.0):
        """Discharge the battery by the specified amount (kWh)"""
        max_discharge = self.calculate_max_discharge(time_step)
        actual_discharge = min(amount, max_discharge)
        
        self.current_charge -= actual_discharge
        return actual_discharge  # Return actual amount discharged
    
    def charge(self, amount, time_step=1.0):
        """Charge the battery by the specified amount (kWh)"""
        max_charge = self.calculate_max_charge(time_step)
        actual_charge = min(amount, max_charge)
        
        self.current_charge += actual_charge
        return actual_charge  # Return actual amount charged
    
    def serialize(self):
        return {
            'type': 'battery',
            'x': self.x(),
            'y': self.y(),
            'power_capacity': self.power_capacity,
            'energy_capacity': self.energy_capacity, 
            'current_charge': self.current_charge,
            'operating_mode': self.operating_mode
        } 