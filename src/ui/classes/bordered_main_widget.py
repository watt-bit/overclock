from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QRectF, QTimer
from PyQt5.QtGui import QPainter, QColor, QPainterPath, QLinearGradient
import math
import random

class BorderedMainWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Initialize gradient colors for a cool, electric darkmode effect (same as GradientBorderText)
        self.default_colors = [
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
            QColor(120, 42, 50),    # Deep burgundy
            QColor(98, 32, 48),     # Dark wine red
            QColor(82, 28, 42),     # Shadowy crimson
            QColor(140, 52, 62),    # Muted raspberry
            QColor(108, 30, 52),    # Dark ruby
            QColor(90, 38, 58),     # Plum red
            QColor(72, 25, 45),     # Deep maroon
            QColor(120, 42, 50),    # Deep burgundy (for rhythm)
        ]
        
        # Dark green gradient colors for success flash
        self.flash_green_colors = [
            QColor(0, 120, 80),     # Neon deep green
            QColor(20, 140, 90),    # Dark neon green
            QColor(10, 100, 70),    # Shadowy neon emerald
            QColor(30, 160, 100),   # Bright neon jade
            QColor(15, 130, 85),    # Dark neon woodland
            QColor(25, 150, 95),    # Neon forest glow
            QColor(5, 110, 75),     # Deep neon green-blue
            QColor(0, 120, 80),     # Neon deep green (for rhythm)
        ]
        
        # Gray color list for gray flash
        self.flash_gray_colors = [
            QColor(50, 50, 50),     # Darkest gray
            QColor(60, 60, 60),     # Darker gray
            QColor(60, 60, 60),     # Dark gray
            QColor(80, 80, 80),     # Medium dark gray
            QColor(70, 70, 70),     # Medium gray
            QColor(100, 100, 100),  # Medium light gray
            QColor(110, 110, 110),  # Light gray
            QColor(50, 50, 50),     # Back to darkest gray (for rhythm)
        ]
        
        # Black color list for black flash
        self.flash_black_colors = [
            QColor(0, 0, 0),    # Black
            QColor(15, 15, 15), # Nearly black
            QColor(5, 5, 5),    # Very dark
            QColor(0, 0, 0),    # Black
        ]

        # Black color list for black flash
        self.colors = [
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
        
        self.original_colors = self.colors.copy()

        # Autocomplete state
        self.is_autocompleting = False
        # Dark green color for autocomplete mode
        self.autocomplete_color = QColor(0, 92, 92)  # Autocomplete color
        
        # Track the success flash sequence
        self.is_success_flash = False
        
        # Track the startup flash sequence
        self.is_startup_flash = False
        
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
            if is_autocompleting and self.is_flashing and self.is_startup_flash == False:
                self.is_flashing = False
                self.flash_timer.stop()
                self.colors = self.original_colors.copy()
            
            # Force update to reflect the new border style
            self.update()
        
    def trigger_gray_flash(self):
        """Start the gray flash animation sequence with the same pattern as gold flash"""
        # Only trigger flash if not in autocomplete mode
        if self.is_autocompleting:
            return
            
        self.is_flashing = True
        self.flash_step = 0
        # Start with the darkest gray color
        self.colors = [self.flash_gray_colors[0]] * len(self.colors)  # Darkest gray
        self.flash_timer.start(83)  # Flash each color for ~83ms (250ms / 3)
        
        # Force update to show the flash immediately
        self.update()
        
    def trigger_error_flash(self):
        """Start a single red flash for 250ms to indicate an error"""
        # Only trigger flash if not in autocomplete mode
        if self.is_autocompleting:
            return
            
        self.is_flashing = True
        self.flash_step = 0
        # Use a random color from the red palette for error indication
        random_red = random.choice(self.flash_red_colors)
        self.colors = [random_red] * len(self.colors)
        self.flash_timer.start(250)  # Flash for 250ms
        
        # Force update to show the flash immediately
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
        
    def trigger_success_flash(self):
        """Start a 4-step sequence showing different green colors for success"""
        # Only trigger flash if not in autocomplete mode
        if self.is_autocompleting:
            return
            
        self.is_flashing = True
        self.flash_step = 0
        self.is_success_flash = True
        
        # Use a random green color from the flash_green_colors
        random_green = random.choice(self.flash_green_colors)
        self.colors = [random_green] * len(self.colors)
        self.flash_timer.start(125)  # Flash each color for 125ms
        
        # Force update to show the flash immediately
        self.update()
        
    def trigger_dark_gray_flash(self):
        """Start a single dark gray flash for 250ms"""
        # Only trigger flash if not in autocomplete mode
        if self.is_autocompleting:
            return
            
        self.is_flashing = True
        self.flash_step = 0
        # Use the darkest gray color for the entire flash
        self.colors = [self.flash_gray_colors[0]] * len(self.colors)  # Darkest gray
        self.flash_timer.start(250)  # Flash for 250ms
        
        # Force update to show the flash immediately
        self.update()
        
    def trigger_startup_flash(self):
        """Start the startup flash animation sequence with specific pattern for app startup"""
        # Only trigger flash if not in autocomplete mode
        if self.is_autocompleting:
            return
            
        self.is_flashing = True
        self.is_startup_flash = True
        self.flash_step = 0
        
        self.flash_timer.start(1000)  # First flash for 1000ms
        
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
        
        # Handle the startup flash sequence
        if self.is_startup_flash:
            if self.flash_step == 1:
                # First black flash (1000ms) is done, switch to normal colors
                self.original_colors=self.default_colors.copy()
                self.colors = self.original_colors.copy()
                self.flash_timer.start(500)  # 500ms normal
            elif self.flash_step == 2:
                # Normal colors done, switch to random black
                random_black = random.choice(self.flash_black_colors)
                self.colors = [random_black] * len(self.colors)
                self.flash_timer.start(500)  # 500ms black
            elif self.flash_step == 3:
                # Black flash done, switch to normal colors
                self.colors = self.original_colors.copy()
                self.flash_timer.start(500)  # 500ms normal
            elif self.flash_step == 4:
                # Normal colors done, switch to random black
                random_black = random.choice(self.flash_black_colors)
                self.colors = [random_black] * len(self.colors)
                self.flash_timer.start(500)  # 500ms black
            elif self.flash_step == 5:
                # Black flash done, switch to normal colors
                self.colors = self.original_colors.copy()
                self.flash_timer.start(500)  # 500ms normal
            elif self.flash_step == 6:
                # Normal colors done, switch to random black
                random_black = random.choice(self.flash_black_colors)
                self.colors = [random_black] * len(self.colors)
                self.flash_timer.start(500)  # 500ms black
            elif self.flash_step == 7:
                # Black flash done, switch to normal colors
                self.colors = self.original_colors.copy()
                self.flash_timer.start(500)  # 500ms normal
            elif self.flash_step == 8:
                # Normal colors done, switch to random black
                random_black = random.choice(self.flash_black_colors)
                self.colors = [random_black] * len(self.colors)
                self.flash_timer.start(500)  # 500ms black
            elif self.flash_step == 9:
                # Final black flash is done, return to normal
                self.colors = self.original_colors.copy()
                self.is_flashing = False
                self.is_startup_flash = False
                self.flash_timer.stop()
        # Handle the success flash sequence (4 steps)
        elif self.is_success_flash:
            if self.flash_step == 1:
                # First green flash is done, switch to another random green
                random_green = random.choice(self.flash_green_colors)
                self.colors = [random_green] * len(self.colors)
            elif self.flash_step == 2:
                # Second green flash is done, switch to another random green
                random_green = random.choice(self.flash_green_colors)
                self.colors = [random_green] * len(self.colors)
            elif self.flash_step == 3:
                # Third green flash is done, switch to another random green
                random_green = random.choice(self.flash_green_colors)
                self.colors = [random_green] * len(self.colors)
            elif self.flash_step == 4:
                # Final green flash is done, return to normal
                self.colors = self.original_colors.copy()
                self.is_flashing = False
                self.is_success_flash = False
                self.flash_timer.stop()
        # Handle the gold flash sequence (3 steps)
        elif self.colors[0] == self.flash_gold_colors[2] or self.colors[0] == self.flash_gold_colors[0] or self.colors[0] == self.flash_gold_colors[1]:
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
        # Handle single dark gray flash (1 step, 250ms)
        elif self.colors[0] == self.flash_gray_colors[0] and all(color == self.colors[0] for color in self.colors) and self.flash_step == 1 and self.flash_timer.interval() == 250:
            # Single dark gray flash is done, return to normal colors
            self.colors = self.original_colors.copy()
            self.is_flashing = False
            self.flash_timer.stop()
        # Handle single error flash (1 step, 250ms)
        elif any(self.colors[0] == red_color for red_color in self.flash_red_colors) and all(color == self.colors[0] for color in self.colors) and self.flash_step == 1 and self.flash_timer.interval() == 250:
            # Single error flash is done, return to normal colors
            self.colors = self.original_colors.copy()
            self.is_flashing = False
            self.flash_timer.stop()
        # Handle the gray flash sequence (3 steps)
        elif self.colors[0] == self.flash_gray_colors[0] or self.colors[0] == self.flash_gray_colors[2] or self.colors[0] == self.flash_gray_colors[4]:
            if self.flash_step == 1:
                # First gray color (Darkest gray) is done, switch to Dark gray
                self.colors = [self.flash_gray_colors[2]] * len(self.colors)
            elif self.flash_step == 2:
                # Second gray color (Dark gray) is done, switch to Medium gray
                self.colors = [self.flash_gray_colors[4]] * len(self.colors)
            elif self.flash_step == 3:
                # Gray flash sequence is done, return to normal colors
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