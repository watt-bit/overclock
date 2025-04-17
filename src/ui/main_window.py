from PyQt5.QtWidgets import (QMainWindow, QGraphicsView, QMessageBox, QApplication)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor

from src.components.bus import BusComponent
from src.simulation.engine import SimulationEngine
from .properties_manager import ComponentPropertiesManager
from .connection_manager import ConnectionManager
from .component_adder import ComponentAdder
from src.models.model_manager import ModelManager
from .historian_manager import HistorianManager
from .particle_system import ParticleSystem
from .ui_initializer import UIInitializer
from .key_handler import KeyHandler
from .autocomplete_manager import AutocompleteManager
from .mode_toggle_manager import ModeToggleManager
from .simulation_controller import SimulationController
from .screenshot_manager import ScreenshotManager
from .custom_scene import CustomScene
from .simulator_initializer import SimulatorInitializer

# TODO: This file needs to be refactored to be more modular and easier to understand. A lot of the setup and initialization / UI code can be pushed to other separate files.

class PowerSystemSimulator(QMainWindow):
    def __init__(self):
        super().__init__()
        SimulatorInitializer.initialize(self)
        
    def center_on_screen(self):
        """Center the window on the screen"""
        screen_geometry = QApplication.desktop().screenGeometry()
        window_geometry = self.geometry()
        
        x = (screen_geometry.width() - window_geometry.width()) // 2
        y = (screen_geometry.height() - window_geometry.height()) // 2 - 50
        
        self.move(x, y)
    
    def validate_bus_states(self):
        """Ensure all bus components without load connections are set to ON"""
        for component in self.components:
            if isinstance(component, BusComponent):
                if not component.has_load_connections() and not component.is_on:
                    component.is_on = True
                    component.update()  # Redraw the component
    
    def add_welcome_text(self):
        """Add welcome text to the middle of the canvas"""
        # Create text item with welcome message
        self.welcome_text = self.scene.addText("")
        
        # Set font and style
        font = self.welcome_text.font()
        font.setPointSize(60)
        font.setBold(True)
        self.welcome_text.setFont(font)
        
        # Set text color to white with a semi-transparent look
        self.welcome_text.setDefaultTextColor(QColor(255, 255, 255, 200))
        
        # Set text width and center-align the text
        self.welcome_text.setTextWidth(300)
        self.welcome_text.setHtml("<div align='center'>Welcome<br>Build Here</div>")
        
        # Center the text (will be properly positioned after view is shown)
        QTimer.singleShot(100, self.center_welcome_text)
    
    def center_welcome_text(self):
        """Center the welcome text in the view after the view is shown"""
        if self.welcome_text and self.welcome_text.scene():
            # Get the center of the current viewport in scene coordinates
            view_center = self.view.mapToScene(self.view.viewport().rect().center())
            text_width = self.welcome_text.boundingRect().width()
            text_height = self.welcome_text.boundingRect().height()
            
            # Position text in the center
            self.welcome_text.setPos(view_center.x() - text_width/2, view_center.y() - text_height/2)
    
    def add_component(self, component_type):
        """Delegate to the ComponentAdder to handle component creation and addition"""
        self.component_adder.add_component(component_type)
    
    def start_connection(self):
        self.connection_manager.start_connection()
    
    def cancel_connection(self):
        """Cancel the current connection creation"""
        self.connection_manager.cancel_connection()
    
    def handle_connection_click(self, component):
        self.connection_manager.handle_connection_click(component)
    
    def eventFilter(self, obj, event):
        # Handle ESC key press
        if (obj is self.view and 
            event.type() == event.KeyPress and 
            event.key() == Qt.Key_Escape):
            if self.creating_connection:
                self.cancel_connection()
                return True
            # Check if sever connection button is disabled (indicating we're in sever mode)
            elif not self.sever_connection_btn.isEnabled():
                self.connection_manager.cancel_sever_connection()
                return True
        
        # Handle mouse movement for connection line
        if (obj is self.view.viewport() and 
            event.type() == event.MouseMove and 
            self.connection_manager.temp_connection and 
            self.connection_manager.connection_source):
            return self.connection_manager.handle_mouse_move_for_connection(event)
        return super().eventFilter(obj, event)
    
    def set_default_cursor(self):
        """Set the default cursor state when not in connection mode"""
        self.cursor_timer.stop()
        self.view.setCursor(Qt.ArrowCursor)
        self.view.viewport().setCursor(Qt.ArrowCursor)
    
    def check_network_connectivity(self):
        """Check if all components are connected in a single network"""
        if not self.components:
            return False
            
        # Use first component as starting point
        visited = set()
        to_visit = [self.components[0]]
        
        # Perform breadth-first search through connections
        while to_visit:
            current = to_visit.pop(0)
            if current not in visited:
                visited.add(current)
                # Add all connected components to visit
                for conn in current.connections:
                    if conn.source not in visited:
                        to_visit.append(conn.source)
                    if conn.target not in visited:
                        to_visit.append(conn.target)
        
        # Check if all components were visited
        return len(visited) == len(self.components)

    def start_scrubbing(self):
        """Enter scrub mode when slider is pressed"""
        self.is_scrubbing = True
        
        # Cancel any pending scrub timer
        if self.scrub_timer:
            self.scrub_timer.stop()
    
    def stop_scrubbing(self):
        """Exit scrub mode when slider is released"""
        # Update simulation immediately when slider is released
        self.is_scrubbing = False
        self.update_simulation()
    
    def time_slider_changed(self, value):
        # Check network connectivity before updating
        if not self.simulation_engine.simulation_running and not self.check_network_connectivity():
            # Show the same warning as when trying to play with unconnected components
            QMessageBox.warning(self, "Simulation Error",
                              "All components must be connected in a single network to run the simulation.\n\n"
                              "Please ensure all generators and loads are connected before starting.")
            # Reset the slider to 0 since we can't run the simulation
            self.time_slider.setValue(0)
            return
            
        self.simulation_engine.current_time_step = value
        
        # Update time label in the analytics panel even during scrubbing
        # But only show minimal time update info without rendering data
        self.minimal_analytics_update()
        
        # Only update full simulation if not playing, scrubbing, or autocompleting
        if not self.simulation_engine.simulation_running and not self.is_scrubbing and not self.is_autocompleting:
            self.update_simulation()
    
    def minimal_analytics_update(self):
        """Update only the time display in analytics during scrubbing"""
        if self.is_scrubbing:
            # Pass is_scrubbing=True to prevent chart updates
            self.analytics_panel.update_analytics(
                0,  # power_produced
                0,  # power_consumed
                self.simulation_engine.current_time_step,  # current_time
                0,  # total_capacity
                is_scrubbing=True
            )
    
    def cycle_simulation_speed(self):
        """Cycle through simulation speeds and update the button text"""
        # Get current speed setting (default is 1)
        # Map speeds [1, 2, 3] to indices [0, 1, 2]
        current_index = self.simulation_speed - 1
        
        # Cycle to next speed: 0->1->2->0
        next_index = (current_index + 1) % 3
        
        # Update button text with appropriate number of arrows
        speed_texts = ["▶▷▷", "▶▶▷", "▶▶▶"]
        self.speed_selector.setText(speed_texts[next_index])
        
        # Call the existing change_simulation_speed method with the new index
        self.change_simulation_speed(next_index)
    
    def change_simulation_speed(self, index):
        """Change the simulation speed based on the selected option"""
        speeds = [1, 2, 3]  # Maps to 1x, 2x, 3x
        self.simulation_speed = speeds[index]
        
        # If simulation is running, restart the timer with the new interval
        if self.simulation_engine.simulation_running:
            self.sim_timer.stop()
            # Base interval is 100ms (0.1 second) for 1x speed - twice as fast as the original
            # Faster speeds use shorter intervals, slower speeds use longer intervals
            interval = int(100 / self.simulation_speed)
            self.sim_timer.start(interval)
    
    def toggle_simulation(self):
        """Toggle the simulation between running and paused"""
        self.simulation_controller.toggle_simulation()
    
    def step_simulation(self, steps):
        self.simulation_controller.step_simulation(steps)
    
    def update_simulation(self):
        self.simulation_controller.update_simulation()
    
    def reset_simulation(self):
        self.simulation_controller.reset_simulation()
    
    def new_scenario(self):
        """Create a new blank scenario"""
        # First reset the simulation state
        self.reset_simulation()
        
        # Safely handle welcome text before clearing the scene
        self.welcome_text = None  # Clear reference first
        
        # Then create a new blank scenario
        self.model_manager.new_scenario()
        
        # Add new welcome text after the scene has been cleared
        self.add_welcome_text()
        
        # Explicitly center the welcome text to ensure it's properly positioned
        QTimer.singleShot(150, self.center_welcome_text)
    
    def save_scenario(self):
        """Save the current scenario to a file"""
        self.model_manager.save_scenario()
    
    def load_scenario(self):
        """Load a scenario from a file"""
        # Stop autocomplete if it's running before loading
        if self.is_autocompleting:
            self.autocomplete_manager.stop_autocomplete()
            # Update main window state to match autocomplete manager state
            self.is_autocompleting = self.autocomplete_manager.is_autocompleting
            self.autocomplete_timer = self.autocomplete_manager.autocomplete_timer
            print("Autocomplete interrupted by load scenario.")
        
        self.model_manager.load_scenario()

    def create_connection_cursor(self, phase):
        """Create a custom cursor for connection mode with pulsing effect"""
        return self.connection_manager.create_connection_cursor(phase)

    def update_cursor(self):
        """Update the cursor appearance for the pulsing effect"""
        self.connection_manager.update_cursor()

    def autoconnect_all_components(self):
        """Automatically connect all components in the scene to form a valid network"""
        self.connection_manager.autoconnect_all_components()

    def start_sever_connection(self):
        """Start the sever connection mode"""
        self.connection_manager.start_sever_connection()
    
    def handle_sever_connection(self, component):
        """Remove all connections from the selected component"""
        self.connection_manager.handle_sever_connection(component)
    
    def cancel_sever_connection(self):
        """Cancel the sever connection mode"""
        self.connection_manager.cancel_sever_connection()

    def keyPressEvent(self, event):
        """Handle key press events for hotkeys"""
        # Use the KeyHandler class to process the event
        if not self.key_handler.handle_key_press(event):
            # If the event wasn't handled by our key handler, pass it to the parent class
            super().keyPressEvent(event) 

    def disable_component_buttons(self, disabled):
        """Disable or enable all component and connection manipulation buttons"""
        # Define disabled button style with grey text
        disabled_button_style = "QPushButton { background-color: #3D3D3D; color: #999999; border: 1px solid #555555; border-radius: 3px; padding: 5px; }"
        
        # Full enabled button style with hover and pressed states
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
        
        # Use stored references
        for button in self.component_buttons:
            button.setEnabled(not disabled)
            # Update style based on disabled state
            if disabled:
                button.setStyleSheet(disabled_button_style)
            else:
                button.setStyleSheet(enabled_button_style)

    def closeEvent(self, event):
        """Handle application close event with confirmation dialogs"""
        # First check if simulation is running and confirm exit
        if self.simulation_engine.simulation_running:
            reply = QMessageBox.question(
                self, 
                "Confirm Exit", 
                "The simulation is still running. Are you sure you want to quit?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                event.ignore()
                return
                
        # Then prompt to save the scenario
        reply = QMessageBox.question(
            self, 
            "Save Before Exit", 
            "Would you like to save your scenario before exiting?",
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
            QMessageBox.Yes
        )
        
        if reply == QMessageBox.Cancel:
            event.ignore()
        elif reply == QMessageBox.Yes:
            self.save_scenario()
            event.accept()
        else:  # QMessageBox.No
            event.accept() 

    def zoom_changed(self, value):
        """Handle zoom slider value changes"""
        # Convert slider value (40-100) to zoom factor (0.4-1.0)
        zoom_factor = value / 100.0
        
        # Save the current zoom level
        self.current_zoom = zoom_factor
        
        # Create a transform for scaling
        transform = self.view.transform()
        
        # Reset the transform first
        transform.reset()
        
        # Create a new transform with the zoom factor
        transform.scale(zoom_factor, zoom_factor)
        
        # Apply the transform to the view
        self.view.setTransform(transform)
        
        # Update the scene
        self.view.update()
        
        # Re-center welcome text if it exists and is valid
        if hasattr(self, 'welcome_text') and self.welcome_text and self.welcome_text.scene():
            self.center_welcome_text()

    def take_screenshot(self):
        """Take a screenshot of the modeling view area and copy to clipboard"""
        self.screenshot_manager.take_screenshot()

    def toggle_background(self):
        """Cycle through background options"""
        # Cycle through background modes: 0 -> 1 -> 2 -> 0
        self.background_mode = (self.background_mode + 1) % 3
        
        # Update background
        self.scene.set_background(self.background_mode)
        
        # Update button text
        if self.background_mode == 0:
            self.background_toggle_btn.setText("🌄 Background 1")
        elif self.background_mode == 1:
            self.background_toggle_btn.setText("🌄 Background 2")
        else:  # mode == 2
            self.background_toggle_btn.setText("🌄 Background Off")
        
        # Update view
        self.view.update()

    def show_components_panel(self):
        """Show the components panel if it's hidden"""
        self.component_dock.setVisible(True)
    
    def position_properties_panel_if_needed(self):
        """Position the properties panel 475px up and 725px right from the center of the screen if not already positioned"""
        if not self.properties_panel_positioned and self.properties_dock.isFloating():
            # Get the screen geometry
            screen_rect = QApplication.desktop().screenGeometry()
            screen_center = screen_rect.center()
            
            # Calculate the new position 
            panel_width = self.properties_dock.width()
            panel_height = self.properties_dock.height()
            new_x = screen_center.x() + 525 - panel_width // 2
            new_y = screen_center.y() - 475 - panel_height // 2
            
            # Ensure the panel stays within the screen boundaries
            new_x = max(0, min(new_x, screen_rect.width() - panel_width))
            new_y = max(0, min(new_y, screen_rect.height() - panel_height))
            
            # Set the position
            self.properties_dock.move(new_x, new_y)
            
            # Mark as positioned
            self.properties_panel_positioned = True
    
    def toggle_properties_panel(self):
        """Toggle the properties panel visibility"""
        
        self.properties_dock.setVisible(not self.properties_dock.isVisible())
        if self.properties_dock.isVisible():
            self.position_properties_panel_if_needed()

    def toggle_analytics_panel(self):
        """Toggle the analytics panel visibility"""
        self.analytics_dock.setVisible(not self.analytics_dock.isVisible())
        if self.analytics_dock.isVisible():
            self.position_properties_panel_if_needed()

    def update_properties_menu_text(self, visible):
        """Update the properties panel menu text based on visibility"""
        if visible:
            self.properties_action.setText("Hide Properties Panel")
        else:
            self.properties_action.setText("Show Properties Panel")

    def update_analytics_menu_text(self, visible):
        """Update the analytics panel menu text based on visibility"""
        if visible:
            self.analytics_action.setText("Hide Analytics (P)anel")
        else:
            self.analytics_action.setText("Show Analytics (P)anel")

    def show_properties_panel(self):
        """Show the properties panel if it's hidden"""
        # When in fullscreen mode, don't use floating properties panel
        if self.isFullScreen() and self.properties_dock.isFloating():
            self.properties_dock.setFloating(False)
        
        self.properties_dock.setVisible(True)
        self.position_properties_panel_if_needed()
    
    def show_analytics_panel(self):
        """Show the analytics panel if it's hidden"""
        self.analytics_dock.setVisible(True)

    def on_view_resize(self, event):
        """Handle resize events to reposition the logo overlay and historian chart"""
        if hasattr(self, 'logo_overlay') and not self.logo_overlay.pixmap().isNull():
            # Reposition logo in bottom right when view is resized
            logo_width = self.logo_overlay.pixmap().width()
            logo_height = self.logo_overlay.pixmap().height()
            self.logo_overlay.move(self.view.width() - logo_width - 10, self.view.height() - logo_height - 10)
        
        # Reposition mode toggle button in top left corner
        if hasattr(self, 'mode_toggle_btn'):
            self.mode_toggle_btn.move(10, 10)
            
        # Reposition analytics toggle button in top right corner
        if hasattr(self, 'analytics_toggle_btn'):
            self.analytics_toggle_btn.move(self.view.width() - 85, 0)
        
        # Resize historian chart if in historian view
        if not self.is_model_view and hasattr(self, 'historian_manager'):
            view_size = self.view.viewport().size()
            self.historian_manager.resize_chart_widget(view_size.width(), view_size.height())
        
        # Call original resize event if it was saved
        if hasattr(self, 'original_resize_event'):
            self.original_resize_event(event)
        else:
            # Call base QGraphicsView implementation
            QGraphicsView.resizeEvent(self.view, event)

    def toggle_mode_button(self):
        """Toggle the mode button text between Model and Historian"""
        self.mode_toggle_manager.toggle_mode_button()

    def switch_to_historian_view(self):
        """Switch from model view to historian view"""
        self.mode_toggle_manager.switch_to_historian_view()

    def switch_to_model_view(self):
        """Switch from historian view back to model view"""
        self.mode_toggle_manager.switch_to_model_view()

    def run_autocomplete(self):
        """Run the simulation from the current time to the end asynchronously"""
        # Update main window state to match autocomplete manager state
        self.is_autocompleting = self.autocomplete_manager.is_autocompleting
        self.autocomplete_timer = self.autocomplete_manager.autocomplete_timer
        self.autocomplete_end_time = self.autocomplete_manager.autocomplete_end_time
        
        # Delegate to the autocomplete manager
        self.autocomplete_manager.run_autocomplete()
        
        # Update main window state after autocomplete manager runs
        self.is_autocompleting = self.autocomplete_manager.is_autocompleting
        self.autocomplete_timer = self.autocomplete_manager.autocomplete_timer
        self.autocomplete_end_time = self.autocomplete_manager.autocomplete_end_time
    
    def _step_autocomplete(self):
        """This method is kept for compatibility but now delegates to the AutocompleteManager"""
        # This method should never be called directly anymore as the timer connects to the manager's method
        pass 