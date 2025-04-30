from PyQt5.QtCore import QObject, QTimer
from PyQt5.QtGui import QColor

class StartupSequence(QObject):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.slider_animation_timer = None
        self.slider_direction = 1  # 1 = forward, -1 = backward
        self.slider_step = 0
        self.slider_steps_total = 100  # Number of steps for smooth animation
        self.saved_connections = None  # To store temporarily disconnected signals
        
    def run(self):
        """
        Run the startup sequence animations for a new project.
        This will be filled with animation code in future implementations.
        """
        print("Running startup sequence...")
        
        # Trigger the startup flash effect on the border
        self.main_window.centralWidget().trigger_startup_flash()
        
        # Flash component buttons after a 250ms delay
        QTimer.singleShot(250, self.flash_component_buttons)
        
        # Animate time slider after a 1000ms delay
        QTimer.singleShot(1000, self.animate_time_slider)
        
        # Add welcome text after a 1500ms delay
        QTimer.singleShot(1000, self.main_window.add_welcome_text)
    
    def flash_component_buttons(self):
        """
        Animate the component buttons by flashing their hover state.
        Sequence: normal (250ms) -> hover (250ms) -> normal (250ms) -> hover (250ms) -> normal
        """
        # Store original style sheet for all buttons
        if not hasattr(self.main_window, 'component_buttons'):
            return
        
        # Define hover style (same as in ui_initializer but with forced hover state)
        hover_style = """
            QPushButton { 
                background-color: #5E5E5E; 
                color: white; 
                border: 1px solid #666666; 
                border-radius: 3px; 
                padding: 5px; 
            }
        """
        
        # Button flash sequences with timing:
        # Default state is already active, wait 125ms
        QTimer.singleShot(125, lambda: self._apply_style_to_buttons(hover_style))
        # After 250ms total (125ms in hover state), set back to original state
        QTimer.singleShot(250, lambda: self._reset_button_styles())
        # After 375ms total (125ms more in original state), set to hover state again
        QTimer.singleShot(375, lambda: self._apply_style_to_buttons(hover_style))
        # After 500ms total (125ms more in hover state), set back to original state
        QTimer.singleShot(500, lambda: self._reset_button_styles())
    
    def animate_time_slider(self):
        """
        Animate the time slider to slide from left to right and back again smoothly.
        This animation lasts 4 seconds total and temporarily disables the slider's normal functionality.
        """
        slider = self.main_window.time_slider
        if not slider:
            return
            
        # Save original slider value
        self.original_slider_value = slider.value()
        
        # Temporarily disconnect slider signals to prevent scrubbing during animation
        self._disconnect_slider_signals()
        
        # Set initial animation state
        self.slider_step = 0
        self.slider_direction = 1  # Start moving forward
        slider.setValue(0)  # Start from the left
        
        # Calculate animation parameters for smooth movement
        # 4000ms total / slider_steps_total = ms per step
        step_interval = 4000 // (self.slider_steps_total * 2)  # *2 because we go forward and backward
        
        # Create timer for animation
        self.slider_animation_timer = QTimer(self)
        self.slider_animation_timer.timeout.connect(self._update_slider_animation)
        self.slider_animation_timer.start(step_interval)
    
    def _update_slider_animation(self):
        """Update the time slider position during the animation"""
        slider = self.main_window.time_slider
        
        # Calculate new position based on current step
        max_value = slider.maximum()
        position = int((self.slider_step / self.slider_steps_total) * max_value)
        
        # Set the slider value based on direction
        if self.slider_direction == 1:  # Forward
            slider.setValue(position)
        else:  # Backward
            slider.setValue(max_value - position)
        
        # Update step counter
        self.slider_step += 1
        
        # Check if we need to change direction or end animation
        if self.slider_step > self.slider_steps_total:
            if self.slider_direction == 1:
                # Change direction to backward
                self.slider_direction = -1
                self.slider_step = 0
            else:
                # Animation complete
                self._end_slider_animation()
    
    def _disconnect_slider_signals(self):
        """Temporarily disconnect the time slider signals"""
        slider = self.main_window.time_slider
        
        # Store original connections by disconnecting all signals
        try:
            # Disconnect value changed signal
            slider.valueChanged.disconnect()
        except TypeError:
            pass  # Signal was not connected
            
        try:
            # Disconnect slider pressed signal
            slider.sliderPressed.disconnect()
        except TypeError:
            pass  # Signal was not connected
            
        try:
            # Disconnect slider released signal
            slider.sliderReleased.disconnect()
        except TypeError:
            pass  # Signal was not connected
    
    def _reconnect_slider_signals(self):
        """Reconnect the time slider signals after animation"""
        slider = self.main_window.time_slider
        
        # Reconnect signals to their original handlers
        slider.valueChanged.connect(lambda value: self.main_window.time_slider_changed(value))
        slider.sliderPressed.connect(self.main_window.start_scrubbing)
        slider.sliderReleased.connect(self.main_window.stop_scrubbing)
    
    def _end_slider_animation(self):
        """End the slider animation and restore normal functionality"""
        if self.slider_animation_timer:
            self.slider_animation_timer.stop()
            self.slider_animation_timer = None
        
        # Reset slider to original position
        self.main_window.time_slider.setValue(self.original_slider_value)
        
        # Reconnect signals
        self._reconnect_slider_signals()
    
    def _apply_style_to_buttons(self, style):
        """Apply the given style to all component buttons"""
        for button in self.main_window.component_buttons:
            button.setStyleSheet(style)
    
    def _reset_button_styles(self):
        """Reset buttons to their default style"""
        # Let the buttons use their default style from the ui_initializer
        enabled_button_style = """
            QPushButton { 
                background-color: #3D3D3D; 
                color: white; 
                border: 1px solid #555555; 
                border-radius: 3px; 
                padding: 5px; 
            }
            QPushButton:hover { 
                background-color: #4D4D4D; 
                border: 1px solid #666666;
            }
            QPushButton:pressed { 
                background-color: #2D2D2D; 
                border: 2px solid #777777;
                padding: 4px; 
            }
        """
        self._apply_style_to_buttons(enabled_button_style) 