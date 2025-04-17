"""
AutocompleteManager module for OVERCLOCK

This module provides the AutocompleteManager class, which encapsulates the autocomplete functionality
for the power system simulation. It handles running the simulation from the current time step to the end
of the simulation timeframe asynchronously, while providing appropriate UI feedback.

This code was extracted from the main_window.py file to improve modularity without changing functionality.
"""

from PyQt5.QtCore import QTimer
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
            
    def _update_irr_display(self):
        """Calculate and update the IRR display with 12, 18, and 36 month values"""
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
            
            # Create display text with all IRR values
            irr_text = f"Refresh Cycle IRR: {irr_12:.2f}% (12 Mo.)"
            
            # Add 18-month value
            if irr_18 is not None:
                irr_text += f" | {irr_18:.2f}% (18 Mo.)"
            else:
                irr_text += " | --.--% (18 Mo.)"
                
            # Add 36-month value
            if irr_36 is not None:
                irr_text += f" | {irr_36:.2f}% (36 Mo.)"
            else:
                irr_text += " | --.--% (36 Mo.)"
                
            self.main_window.irr_label.setText(irr_text)
        else:
            self.main_window.irr_label.setText("Refresh Cycle IRR: --.--% (12 Mo.) | --.--% (18 Mo.) | --.--% (36 Mo.)")
        
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
            
            # Re-enable controls that were disabled by autocomplete
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