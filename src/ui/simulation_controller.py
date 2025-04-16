from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QTimer

from src.components.generator import GeneratorComponent
from src.components.load import LoadComponent
from src.components.battery import BatteryComponent
from src.components.grid_import import GridImportComponent
from src.components.grid_export import GridExportComponent
from src.components.cloud_workload import CloudWorkloadComponent

class SimulationController:
    """
    SimulationController handles simulation control logic (toggling, stepping, resetting)
    while maintaining exact compatibility with the existing UI and component system.
    """
    
    def __init__(self, main_window):
        self.main_window = main_window  # Keep reference to access UI components
    
    def toggle_simulation(self):
        """Toggle the simulation between running and paused"""
        # Check network connectivity before starting simulation
        if not self.main_window.simulation_engine.simulation_running and not self.main_window.check_network_connectivity():
            QMessageBox.warning(self.main_window, "Simulation Error",
                              "All components must be connected in a single network to run the simulation.\n\n"
                              "Please ensure all generators and loads are connected before starting.")
            return
        
        # Make sure we're not in scrub mode when starting playback
        if not self.main_window.simulation_engine.simulation_running:
            self.main_window.simulation_engine.is_scrubbing = False
            
        self.main_window.simulation_engine.simulation_running = not self.main_window.simulation_engine.simulation_running
        if self.main_window.simulation_engine.simulation_running:
            interval = int(100 / self.main_window.simulation_speed)
            self.main_window.sim_timer.start(interval)
            self.main_window.play_btn.setText("Pause (Space)")
            self.main_window.disable_component_buttons(True)
            
            # Disable autocomplete button during simulation and gray out text
            self.main_window.autocomplete_btn.setEnabled(False)
            self.main_window.autocomplete_btn.setStyleSheet("""
                QPushButton { 
                    background-color: #1B5E20; 
                    color: #99CCAA; 
                    border: 1px solid #555555; 
                    border-radius: 3px; 
                    padding: 5px; 
                    font-weight: bold; 
                    font-size: 16px; 
                }
            """)
        else:
            self.main_window.sim_timer.stop()
            self.main_window.play_btn.setText("Run (Space)")
            self.main_window.disable_component_buttons(False)
            
            # Re-enable autocomplete button when simulation is paused and restore style
            self.main_window.autocomplete_btn.setEnabled(True)
            self.main_window.autocomplete_btn.setStyleSheet("""
                QPushButton { 
                    background-color: #1B5E20; 
                    color: white; 
                    border: 1px solid #555555; 
                    border-radius: 3px; 
                    padding: 5px; 
                    font-weight: bold; 
                    font-size: 16px; 
                }
                QPushButton:hover { 
                    background-color: #2E7D32; 
                }
                QPushButton:pressed { 
                    background-color: #154919; 
                    border: 2px solid #777777;
                    padding: 4px; 
                }
            """)
    
    def step_simulation(self, steps):
        # Check if simulation was running but has been stopped (end of timeline)
        if not self.main_window.simulation_engine.simulation_running and self.main_window.play_btn.text() == "Pause (Space)":
            # Update UI to reflect that simulation has stopped
            self.main_window.play_btn.setText("Run (Space)")
            self.main_window.sim_timer.stop()
            self.main_window.disable_component_buttons(False)
            
            # Re-enable autocomplete button when simulation ends and restore style
            self.main_window.autocomplete_btn.setEnabled(True)
            self.main_window.autocomplete_btn.setStyleSheet("""
                QPushButton { 
                    background-color: #1B5E20; 
                    color: white; 
                    border: 1px solid #555555; 
                    border-radius: 3px; 
                    padding: 5px; 
                    font-weight: bold; 
                    font-size: 16px; 
                }
                QPushButton:hover { 
                    background-color: #2E7D32; 
                }
                QPushButton:pressed { 
                    background-color: #154919; 
                    border: 2px solid #777777;
                    padding: 4px; 
                }
            """)
            return
            
        # First, process the current time step (time t)
        self.main_window.simulation_engine.update_simulation()
        
        # Then increment to the next time step (time t+1)
        # Only if we successfully performed the step
        if self.main_window.simulation_engine.step_simulation(steps):
            # Update the time slider to show the new position
            self.main_window.time_slider.setValue(self.main_window.simulation_engine.current_time_step)
    
    def update_simulation(self):
        self.main_window.simulation_engine.update_simulation()
    
    def reset_simulation(self):
        # Check if simulation was running and stop it
        was_running = self.main_window.simulation_engine.simulation_running
        
        if was_running:
            # Stop the timer if running
            self.main_window.sim_timer.stop()
        
        # Stop autocomplete if it's running
        if self.main_window.is_autocompleting:
            self.main_window.autocomplete_manager.stop_autocomplete()
            # Update main window state to match autocomplete manager state
            self.main_window.is_autocompleting = self.main_window.autocomplete_manager.is_autocompleting
            self.main_window.autocomplete_timer = self.main_window.autocomplete_manager.autocomplete_timer
            print("Autocomplete interrupted by reset.")
        
        # Set simulation state variables
        self.main_window.simulation_engine.current_time_step = 0
        self.main_window.simulation_engine.simulation_running = False
        self.main_window.simulation_engine.total_energy_imported = 0
        self.main_window.simulation_engine.total_energy_exported = 0
        self.main_window.simulation_engine.last_time_step = 0
        
        # Reset the gross revenue data
        self.main_window.simulation_engine.gross_revenue_data = [0.0] * 8761
        
        # Also reset accumulated revenue in all load components
        for item in self.main_window.scene.items():
            if isinstance(item, LoadComponent):
                item.accumulated_revenue = 0.0
                item.update()  # Refresh the visual display
            # Reset accumulated revenue for Cloud Workload components as well
            elif isinstance(item, CloudWorkloadComponent):
                item.accumulated_revenue = 0.0
                item.update()  # Refresh the visual display
            # Reset accumulated revenue for Grid Export components
            elif isinstance(item, GridExportComponent):
                item.accumulated_revenue = 0.0
                item.previous_revenue = 0.0
                item.update()  # Refresh the visual display
            # Reset accumulated cost for Grid Import components
            elif isinstance(item, GridImportComponent):
                item.accumulated_cost = 0.0
                item.previous_cost = 0.0
                item.update()  # Refresh the visual display
            # Reset accumulated cost for Generator components
            elif isinstance(item, GeneratorComponent):
                item.accumulated_cost = 0.0
                item.previous_cost = 0.0
                item.update()  # Refresh the visual display
            # Reset all batteries to 100% charge
            elif isinstance(item, BatteryComponent):
                item.current_charge = item.energy_capacity  # Set to 100% charge
                item.update()  # Refresh the visual display
        
        # Update UI to match paused state
        self.main_window.play_btn.setText("Run (Space)")
        self.main_window.time_slider.setValue(0)
        
        # Re-enable component buttons if they were disabled
        if was_running:
            self.main_window.disable_component_buttons(False)
        
        # Clear the analytics chart history
        self.main_window.analytics_panel.clear_chart_history()
        
        # Reset Historian data and clear its chart
        self.main_window.simulation_engine.reset_historian()
        self.main_window.historian_manager.clear_chart()
        
        # Always ensure autocomplete button is re-enabled and properly styled after reset
        self.main_window.autocomplete_btn.setEnabled(True)
        self.main_window.autocomplete_btn.setStyleSheet("""
            QPushButton { 
                background-color: #1B5E20; 
                color: white; 
                border: 1px solid #555555; 
                border-radius: 3px; 
                padding: 5px; 
                font-weight: bold; 
                font-size: 16px; 
            }
            QPushButton:hover { 
                background-color: #2E7D32; 
            }
            QPushButton:pressed { 
                background-color: #154919; 
                border: 2px solid #777777;
                padding: 4px; 
            }
        """)
        
        self.update_simulation() 