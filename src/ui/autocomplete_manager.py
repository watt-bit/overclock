"""
AutocompleteManager module for OVERCLOCK

This module provides the AutocompleteManager class, which encapsulates the autocomplete functionality
for the power system simulation. It handles running the simulation from the current time step to the end
of the simulation timeframe asynchronously, while providing appropriate UI feedback.

This code was extracted from the main_window.py file to improve modularity without changing functionality.
"""

from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import QMessageBox
from src.utils.irr_calculator import calculate_irr, calculate_extended_irr

class AutocompleteManager:
    """
    Manages the autocomplete functionality of the simulation.
    This class encapsulates the logic for running the simulation from the current time to the end asynchronously.
    """
    
    def __init__(self, main_window):
        """Initialize with a reference to the main window"""
        self.main_window = main_window
        self.is_autocompleting = False
        self.autocomplete_timer = None
        self.autocomplete_end_time = 0
        
    def run_autocomplete(self):
        """Run the simulation from the current time to the end asynchronously"""
        
        # Reset the simulation first to ensure we capture the entire timeline
        # Skip the flash animation to prevent it from interfering with autocomplete state
        self.main_window.reset_simulation(skip_flash=True)
        
        # Check if already running
        if self.main_window.simulation_engine.simulation_running or self.is_autocompleting:
            return
        
        # Check network connectivity first
        if not self.main_window.check_network_connectivity():
            QMessageBox.warning(self.main_window, "Simulation Error",
                              "All components must be connected in a single network to run the simulation.\n\n"
                              "Please ensure all generators and loads are connected before starting.")
            return
        
        # Switch to historian view if currently in model view
        if self.main_window.is_model_view:
            self.main_window.switch_to_historian_view()
            self.main_window.mode_toggle_btn.setText("💾 Historian (TAB)")
            # Ensure component buttons are disabled regardless of how we enter historian view
            self.main_window.disable_component_buttons(True)
        
        # Ensure we're not in scrub mode
        self.main_window.simulation_engine.is_scrubbing = False
        
        # Get current and end times
        start_time = self.main_window.simulation_engine.current_time_step
        self.autocomplete_end_time = self.main_window.time_slider.maximum()
        
        # If already at the end, do nothing
        if start_time >= self.autocomplete_end_time:
            return
            
        print("Starting Autocomplete simulation...")
        self.is_autocompleting = True
        # Ensure main window has same autocomplete state
        self.main_window.is_autocompleting = True
        
        # Update bordered widget to use solid border during autocomplete
        if hasattr(self.main_window, 'centralWidget') and hasattr(self.main_window.centralWidget(), 'set_autocomplete_state'):
            self.main_window.centralWidget().set_autocomplete_state(True)
        
        # Update delete button state in properties manager
        if hasattr(self.main_window, 'properties_manager'):
            self.main_window.properties_manager.update_delete_button_state()
        
        # Define disabled styles for buttons
        disabled_play_btn_style = "QPushButton { background-color: #2196F3; color: #99CCFF; border: 1px solid #555555; border-radius: 3px; padding: 5px; font-weight: bold; font-size: 16px; }"
        disabled_speed_selector_style = "QPushButton { background-color: #3D3D3D; color: #999999; border: 1px solid #555555; border-radius: 3px; padding: 4px; font-weight: bold; font-size: 14px;}"
        
        # Save original button text for restoration
        self.main_window.play_btn_text = self.main_window.play_btn.text()
        self.main_window.speed_selector_text = self.main_window.speed_selector.text()
        
        # Disable controls during autocomplete
        self.main_window.play_btn.setEnabled(False)
        self.main_window.play_btn.setStyleSheet(disabled_play_btn_style)
        
        self.main_window.reset_btn.setEnabled(False)
        self.main_window.time_slider.setEnabled(False)
        self.main_window.autocomplete_btn.setEnabled(False)
        
        self.main_window.speed_selector.setEnabled(False)
        self.main_window.speed_selector.setStyleSheet(disabled_speed_selector_style)
        
        # Ensure component buttons are disabled (redundant but safe)
        self.main_window.disable_component_buttons(True)

        # Create and start the timer if it doesn't exist
        if not self.autocomplete_timer:
            self.autocomplete_timer = QTimer(self.main_window)
            self.autocomplete_timer.timeout.connect(self._step_autocomplete)
            
        # Start timer with 0 interval for maximum speed while yielding
        self.autocomplete_timer.start(0)
        
    def _step_autocomplete(self):
        """Perform a single step of the autocomplete process"""
        current_time = self.main_window.simulation_engine.current_time_step
        
        if current_time < self.autocomplete_end_time:
            # Process the current time step first (including time step 0)
            self.main_window.simulation_engine.update_simulation(skip_ui_updates=True)
            
            # Then increment for the next iteration
            self.main_window.simulation_engine.current_time_step += 1
            
            # Update only the time slider during the loop
            self.main_window.time_slider.setValue(self.main_window.simulation_engine.current_time_step)
            
            # Keep timer running for the next step
        else:
            # Reached the end
            self.autocomplete_timer.stop()
            self.is_autocompleting = False
            # Ensure main window also has autocomplete flag set to false
            self.main_window.is_autocompleting = False
            
            # Restore normal border animation
            if hasattr(self.main_window, 'centralWidget') and hasattr(self.main_window.centralWidget(), 'set_autocomplete_state'):
                self.main_window.centralWidget().set_autocomplete_state(False)
            
            # Update delete button state in properties manager
            if hasattr(self.main_window, 'properties_manager'):
                self.main_window.properties_manager.update_delete_button_state()
            
            # Perform one final update to refresh UI elements and charts
            # This call will not skip UI updates
            self.main_window.simulation_engine.update_simulation()
            # Explicitly update historian chart if needed
            if not self.main_window.is_model_view:
                self.main_window.historian_manager.update_chart()
            
            # Calculate and display IRR
            self._update_irr_display()
            
            # Define original styles for buttons with hover and pressed states
            play_btn_style = """
                QPushButton { 
                    border: 1px solid #555555; 
                    border-radius: 3px; 
                    padding: 5px; 
                    background-color: #0D47A1; 
                    color: white; 
                    font-weight: bold; 
                    font-size: 16px; 
                }
                QPushButton:hover { 
                    background-color: #1565C0; 
                }
                QPushButton:pressed { 
                    background-color: #0A367B; 
                    border: 2px solid #777777;
                    padding: 4px; 
                }
            """
            
            speed_selector_style = """
                QPushButton { 
                    background-color: #3D3D3D; 
                    color: white; 
                    border: 1px solid #555555; 
                    border-radius: 3px; 
                    padding: 4px; 
                    font-weight: bold; 
                    font-size: 14px;
                }
                QPushButton:hover { 
                    background-color: #4D4D4D; 
                    border: 1px solid #666666;
                }
                QPushButton:pressed { 
                    background-color: #2D2D2D; 
                    border: 2px solid #777777;
                    padding: 3px; 
                }
            """
            
            # Re-enable controls
            self.main_window.play_btn.setEnabled(True)
            self.main_window.play_btn.setStyleSheet(play_btn_style)
            
            self.main_window.reset_btn.setEnabled(True)
            self.main_window.time_slider.setEnabled(True)
            self.main_window.autocomplete_btn.setEnabled(True)
            
            self.main_window.speed_selector.setEnabled(True)
            self.main_window.speed_selector.setStyleSheet(speed_selector_style)
            
            # Only re-enable component buttons if we're in model view
            # Otherwise, they should stay disabled when in historian view
            if self.main_window.is_model_view:
                self.main_window.disable_component_buttons(False)
            
            print("Autocomplete simulation finished.")
            
    def _get_irr_color(self, irr_value):
        """
        Calculate color for IRR value based on range:
        - Below -75%: Bright red
        - At 0%: White with lower alpha
        - Above 100%: Bright green
        - Interpolate between these points
        
        Args:
            irr_value: IRR value as a percentage (e.g., 15.23 for 15.23%)
            
        Returns:
            HTML color string for the IRR value
        """
        if irr_value is None:
            # Default color for missing values
            return "rgba(255, 255, 255, 0.8)"
            
        # Define color stops
        red_stop = -50.0  # Below this is bright red
        neutral_stop = 0.0  # This is white (with lower alpha)
        green_stop = 100.0  # Above this is bright green
        
        # Define colors at each stop (r, g, b, a)
        red_color = (255, 50, 50, 0.9)  # Bright red
        neutral_color = (255, 255, 255, 1.0)  # White
        green_color = (139, 255, 74, 0.9)  # Bright green
        
        # Clamp irr_value between red_stop and green_stop for interpolation
        clamped_value = max(red_stop, min(green_stop, irr_value))
        
        # Interpolate colors based on where the value falls
        if clamped_value <= neutral_stop:
            # Interpolate between red and neutral
            t = (clamped_value - red_stop) / (neutral_stop - red_stop)
            r = int(red_color[0] + t * (neutral_color[0] - red_color[0]))
            g = int(red_color[1] + t * (neutral_color[1] - red_color[1]))
            b = int(red_color[2] + t * (neutral_color[2] - red_color[2]))
            a = red_color[3] + t * (neutral_color[3] - red_color[3])
        else:
            # Interpolate between neutral and green
            t = (clamped_value - neutral_stop) / (green_stop - neutral_stop)
            r = int(neutral_color[0] + t * (green_color[0] - neutral_color[0]))
            g = int(neutral_color[1] + t * (green_color[1] - neutral_color[1]))
            b = int(neutral_color[2] + t * (green_color[2] - neutral_color[2]))
            a = neutral_color[3] + t * (green_color[3] - neutral_color[3])
            
        # Return as rgba string
        return f"rgba({r}, {g}, {b}, {a})"
            
    def _update_irr_display(self):
        """Calculate and update the IRR display with 12, 18, and 36 month values"""
        # Check if the main window still exists and has a valid irr_label
        if not hasattr(self.main_window, 'irr_label') or not self.main_window.irr_label:
            return
            
        # Get CAPEX and revenue/cost data
        total_capex = self.main_window.calculate_total_capex()
        hourly_revenue = self.main_window.simulation_engine.gross_revenue_data
        hourly_cost = self.main_window.simulation_engine.gross_cost_data
        current_hour = self.main_window.simulation_engine.current_time_step
        
        # Calculate extended IRR values (12, 18, and 36 months)
        irr_results = calculate_extended_irr(total_capex, hourly_revenue, hourly_cost, current_hour)
        
        # Update the IRR display
        if irr_results[12] is not None:
            # Format all IRR values with 2 decimal places
            irr_12 = irr_results[12] * 100
            irr_18 = irr_results[18] * 100 if irr_results[18] is not None else None
            irr_36 = irr_results[36] * 100 if irr_results[36] is not None else None
            
            # Get colors for IRR values
            color_12 = self._get_irr_color(irr_12)
            color_18 = self._get_irr_color(irr_18)
            color_36 = self._get_irr_color(irr_36)
            
            # Create display text with all IRR values using HTML for color
            irr_text = f'Refresh Cycle IRR: <span style="color: {color_12}">{irr_12:.1f}%</span> (12 Mo.)'
            
            # Add 18-month value
            if irr_18 is not None:
                irr_text += f' | <span style="color: {color_18}">{irr_18:.1f}%</span> (18 Mo.)'
            else:
                irr_text += ' | <span style="color: rgba(255, 255, 255, 0.8)">--.-</span>% (18 Mo.)'
                
            # Add 36-month value
            if irr_36 is not None:
                irr_text += f' | <span style="color: {color_36}">{irr_36:.1f}%</span> (36 Mo.)'
            else:
                irr_text += ' | <span style="color: rgba(255, 255, 255, 0.8)">--.-</span>% (36 Mo.)'
                
            # Check if the irr_label is still valid before setting text
            if self.main_window.irr_label.isVisible():
                # Set rich text in the label
                self.main_window.irr_label.setText(irr_text)
                # Allow HTML formatting in the label
                self.main_window.irr_label.setTextFormat(Qt.RichText)
        else:
            # Default placeholder text with standard color
            irr_text = 'Refresh Cycle IRR: <span style="color: rgba(255, 255, 255, 0.8)">--.-</span>% (12 Mo.) | <span style="color: rgba(255, 255, 255, 0.8)">--.-</span>% (18 Mo.) | <span style="color: rgba(255, 255, 255, 0.8)">--.-</span>% (36 Mo.)'
            
            # Check if the irr_label is still valid before setting text
            if self.main_window.irr_label.isVisible():
                self.main_window.irr_label.setText(irr_text)
                self.main_window.irr_label.setTextFormat(Qt.RichText)
        
        # Only adjust size and position if the label is still valid and visible
        if self.main_window.irr_label.isVisible():
            # Adjust size to fit new content
            self.main_window.irr_label.adjustSize()
            
            # Ensure it stays in the correct position
            if hasattr(self.main_window, 'view') and self.main_window.view:
                self.main_window.irr_label.move(10, self.main_window.view.height() - self.main_window.irr_label.height() - 25)
        
    def stop_autocomplete(self):
        """Stop the autocomplete process if it's running"""
        if self.is_autocompleting:
            if self.autocomplete_timer:
                self.autocomplete_timer.stop()
            self.is_autocompleting = False
            # Ensure main window also has autocomplete flag set to false
            self.main_window.is_autocompleting = False
            
            # Restore normal border animation
            if hasattr(self.main_window, 'centralWidget') and hasattr(self.main_window.centralWidget(), 'set_autocomplete_state'):
                self.main_window.centralWidget().set_autocomplete_state(False)
            
            # Update delete button state in properties manager
            if hasattr(self.main_window, 'properties_manager'):
                self.main_window.properties_manager.update_delete_button_state()
            
            # Define original styles for buttons with hover and pressed states
            play_btn_style = """
                QPushButton { 
                    border: 1px solid #555555; 
                    border-radius: 3px; 
                    padding: 5px; 
                    background-color: #0D47A1; 
                    color: white; 
                    font-weight: bold; 
                    font-size: 16px; 
                }
                QPushButton:hover { 
                    background-color: #1565C0; 
                }
                QPushButton:pressed { 
                    background-color: #0A367B; 
                    border: 2px solid #777777;
                    padding: 4px; 
                }
            """
            
            speed_selector_style = """
                QPushButton { 
                    background-color: #3D3D3D; 
                    color: white; 
                    border: 1px solid #555555; 
                    border-radius: 3px; 
                    padding: 4px; 
                    font-weight: bold; 
                    font-size: 14px;
                }
                QPushButton:hover { 
                    background-color: #4D4D4D; 
                    border: 1px solid #666666;
                }
                QPushButton:pressed { 
                    background-color: #2D2D2D; 
                    border: 2px solid #777777;
                    padding: 3px; 
                }
            """
            
            # Re-enable controls
            self.main_window.play_btn.setEnabled(True)
            self.main_window.play_btn.setStyleSheet(play_btn_style)
            
            self.main_window.reset_btn.setEnabled(True)
            self.main_window.time_slider.setEnabled(True)
            self.main_window.autocomplete_btn.setEnabled(True)
            
            self.main_window.speed_selector.setEnabled(True)
            self.main_window.speed_selector.setStyleSheet(speed_selector_style)
            
            # Only re-enable component buttons if we're in model view
            # Otherwise, they should stay disabled when in historian view
            if self.main_window.is_model_view:
                self.main_window.disable_component_buttons(False)
                
            print("Autocomplete interrupted.")
            
    def cleanup(self):
        """Clean up resources before shutdown - call this when the application is closing"""
        if self.autocomplete_timer:
            try:
                # Disconnect the timer signal first to prevent callbacks
                self.autocomplete_timer.timeout.disconnect(self._step_autocomplete)
            except (TypeError, RuntimeError):
                # Signal might not be connected, that's okay
                pass
            # Stop the timer
            self.autocomplete_timer.stop()
            self.autocomplete_timer = None
        
        # Reset state
        self.is_autocompleting = False
        self.autocomplete_end_time = 0
        
        # Clear any referenced objects
        self.main_window = None 