from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QRectF, QTimer
from PyQt5.QtGui import QPainter, QColor, QPainterPath, QLinearGradient
import math

class BorderedMainWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Initialize gradient colors for a cool, electric darkmode effect (same as GradientBorderText)
        self.colors = [
            QColor(58, 78, 178),    # Bright starlight electric blue
            QColor(46, 135, 175),   # Cool bright cyan
            QColor(30, 155, 145),   # Celestial teal
            QColor(20, 175, 185),   # Bright neon cyan
            QColor(18, 110, 190),   # Luminous sky blue
            QColor(75, 85, 195),    # Soft space indigo
            QColor(55, 95, 175),    # Twilight blue
            QColor(70, 145, 200),   # Arctic sky
            QColor(95, 170, 210),   # Distant pale cyan star
            QColor(40, 85, 150),    # Deep steel blue   
            QColor(65, 50, 135),    # Cosmic violet
            QColor(58, 78, 178),    # Bright starlight electric blue (for rhythm)
        ]
        
        # Animation properties
        self.animation_offset = 0
        self.animation_speed = 1
        self.border_width = 4
        self.corner_radius = 4
        
        # Set up animation timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.animate)
        self.timer.start(50)  # Update every 50ms
        
        # Make the widget's border transparent to mouse events
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        # Set style to ensure proper appearance
        self.setStyleSheet("background: transparent;")
        
        # Flash animation properties
        self.is_flashing = False
        self.flash_step = 0
        self.flash_timer = QTimer()
        self.flash_timer.timeout.connect(self.update_flash)
        
        # Dark red gradient colors for flash
        self.flash_red_colors = [
            QColor(178, 58, 58),    # Dark red
            QColor(175, 46, 46),    # Darker red
            QColor(155, 30, 30),    # Deep red
            QColor(195, 75, 75),    # Medium red
            QColor(190, 18, 18),    # Bright red
            QColor(175, 55, 55),    # Moderate red
            QColor(150, 40, 40),    # Steel red
            QColor(178, 58, 58),    # Dark red (for rhythm)
        ]
        
        # Black color list for black flash
        self.flash_black_colors = [
            QColor(0, 0, 0),    # Black
            QColor(15, 15, 15), # Nearly black
            QColor(5, 5, 5),    # Very dark
            QColor(0, 0, 0),    # Black
        ]
        
        # Gold color list for gold flash
        self.flash_gold_colors = [
            QColor("#FFCA28"),    # Base gold color
            QColor("#FFD54F"),    # Lighter gold
            QColor("#FFB300"),    # Darker gold
            QColor("#FFC107"),    # Amber
            QColor("#FFD740"),    # Light amber
            QColor("#FFAB00"),    # Dark amber
            QColor("#FFC400"),    # Amber accent
            QColor("#FFCA28"),    # Base gold color (for rhythm)
        ]
        
        # Store the original colors for restoration
        self.original_colors = self.colors.copy()
        
        # Autocomplete state
        self.is_autocompleting = False
        # Dark green color for autocomplete mode
        self.autocomplete_color = QColor(0, 92, 92)  # Autocomplete color
        
    def animate(self):
        """Update animation and trigger redraw"""
        # Only animate if not in autocomplete mode
        if not self.is_autocompleting:
            self.animation_offset = (self.animation_offset + self.animation_speed) % 100
            self.update()
        
    def set_autocomplete_state(self, is_autocompleting):
        """
        Set the autocomplete state and update border style accordingly
        
        Args:
            is_autocompleting: Boolean indicating if autocomplete is active
        """
        if self.is_autocompleting != is_autocompleting:
            self.is_autocompleting = is_autocompleting
            
            # Stop any ongoing flash if autocomplete is starting
            if is_autocompleting and self.is_flashing:
                self.is_flashing = False
                self.flash_timer.stop()
                self.colors = self.original_colors.copy()
            
            # Force update to reflect the new border style
            self.update()
        
    def trigger_flash(self):
        """Start the flash animation sequence"""
        # Only trigger flash if not in autocomplete mode
        if self.is_autocompleting:
            return
            
        self.is_flashing = True
        self.flash_step = 0
        self.colors = self.flash_red_colors.copy()  # Start with red
        self.flash_timer.start(250)  # First flash for 250ms
        
    def trigger_gold_flash(self):
        """Start the gold flash animation sequence"""
        # Only trigger flash if not in autocomplete mode
        if self.is_autocompleting:
            return
            
        self.is_flashing = True
        self.flash_step = 0
        # Start with the 3rd color in the gold list
        self.colors = [self.flash_gold_colors[2]] * len(self.colors)  # Fill with the 3rd gold color
        self.flash_timer.start(83)  # Flash each color for ~83ms (250ms / 3)
        
        # Force update to show the flash immediately
        self.update()
        
    def update_flash(self):
        """Progress through the flash animation steps"""
        # If we entered autocomplete mode, stop flashing
        if self.is_autocompleting:
            self.is_flashing = False
            self.flash_timer.stop()
            return
            
        self.flash_step += 1
        
        # Handle the gold flash sequence (3 steps)
        if self.colors[0] == self.flash_gold_colors[2] or self.colors[0] == self.flash_gold_colors[0] or self.colors[0] == self.flash_gold_colors[1]:
            if self.flash_step == 1:
                # First gold color (3rd in list) is done, switch to second gold color (1st in list)
                self.colors = [self.flash_gold_colors[0]] * len(self.colors)
            elif self.flash_step == 2:
                # Second gold color (1st in list) is done, switch to third gold color (2nd in list)
                self.colors = [self.flash_gold_colors[1]] * len(self.colors)
            elif self.flash_step == 3:
                # Gold flash sequence is done, return to normal colors
                self.colors = self.original_colors.copy()
                self.is_flashing = False
                self.flash_timer.stop()
        # Handle the regular red/black flash sequence
        elif self.flash_step == 1:
            # First red flash is done, switch to black
            self.colors = self.flash_black_colors.copy()
        elif self.flash_step == 2:
            # Black flash is done, switch to red again
            self.colors = self.flash_red_colors.copy()
        elif self.flash_step == 3:
            # Second red flash is done, switch to black again
            self.colors = self.flash_black_colors.copy()
        elif self.flash_step == 4:
            # Final black flash is done, return to normal colors
            self.colors = self.original_colors.copy()
            self.is_flashing = False
            self.flash_timer.stop()
            
        self.update()  # Trigger a repaint
        
    def paintEvent(self, event):
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        # First, fill the entire widget with black background
        painter.fillRect(self.rect(), QColor("#000000"))
        
        # Draw the border path
        rect = QRectF(self.rect())  # Convert QRect to QRectF
        path = QPainterPath()
        path.addRoundedRect(rect, self.corner_radius, self.corner_radius)
        
        if self.is_autocompleting:
            # Use solid dark green border during autocomplete
            painter.save()
            painter.setClipPath(path)
            painter.fillRect(rect, self.autocomplete_color)
            
            # Draw inner frame (creating a border effect)
            inner_rect = QRectF(
                rect.x() + self.border_width, 
                rect.y() + self.border_width,
                rect.width() - 2 * self.border_width,
                rect.height() - 2 * self.border_width
            )
            inner_path = QPainterPath()
            inner_path.addRoundedRect(inner_rect, self.corner_radius-self.border_width, self.corner_radius-self.border_width)
            
            # Set clipping to the inside area to create the border
            painter.setClipPath(inner_path, Qt.IntersectClip)
            painter.fillRect(rect, Qt.transparent)  # Clear the inner area
            painter.restore()
        else:
            # Create gradient for the border - use a rotated linear gradient for better performance
            angle = self.animation_offset * 3.6  # Convert percentage to degrees (0-100 to 0-360)
            radians = angle * 3.14159 / 180.0  # Convert to radians
            
            # Calculate endpoint based on angle to create rotating linear gradient
            length = max(self.width(), self.height()) * 2
            end_x = self.width() / 2 + length * math.cos(radians)
            end_y = self.height() / 2 + length * math.sin(radians)
            
            gradient = QLinearGradient(
                self.width() / 2 - length * math.cos(radians),
                self.height() / 2 - length * math.sin(radians),
                end_x, end_y
            )
            
            # Set gradient colors
            num_colors = len(self.colors)
            for i in range(num_colors):
                pos = i / (num_colors - 1)
                gradient.setColorAt(pos, self.colors[i])
            
            # Draw outer border
            painter.save()
            painter.setClipPath(path)
            painter.fillRect(rect, gradient)
            
            # Draw inner frame (creating a border effect)
            inner_rect = QRectF(
                rect.x() + self.border_width, 
                rect.y() + self.border_width,
                rect.width() - 2 * self.border_width,
                rect.height() - 2 * self.border_width
            )
            inner_path = QPainterPath()
            inner_path.addRoundedRect(inner_rect, self.corner_radius-self.border_width, self.corner_radius-self.border_width)
            
            # Set clipping to the inside area to create the border
            painter.setClipPath(inner_path, Qt.IntersectClip)
            painter.fillRect(rect, Qt.transparent)  # Clear the inner area
            painter.restore() 