from PyQt5.QtWidgets import (QMainWindow, QWidget, QGraphicsView, QGraphicsScene, QMessageBox, QApplication)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject, QPointF
from PyQt5.QtGui import QPainter, QPen, QPixmap, QColor, QBrush

from src.components.generator import GeneratorComponent
from src.components.load import LoadComponent
from src.components.bus import BusComponent
from src.components.grid_import import GridImportComponent
from src.components.grid_export import GridExportComponent
from src.components.battery import BatteryComponent
from src.components.cloud_workload import CloudWorkloadComponent
from src.simulation.engine import SimulationEngine
from .properties_manager import ComponentPropertiesManager
from .connection_manager import ConnectionManager
from .component_adder import ComponentAdder
from src.models.model_manager import ModelManager
from .historian_manager import HistorianManager
from .particle_system import ParticleSystem
from .ui_initializer import UIInitializer
from .key_handler import KeyHandler

# TODO: This file needs to be refactored to be more modular and easier to understand. A lot of the setup and initialization / UI code can be pushed to other separate files.

class CustomScene(QGraphicsScene, QObject):
    component_clicked = pyqtSignal(object)
    
    def __init__(self):
        QGraphicsScene.__init__(self)
        QObject.__init__(self)
        
        # Load the background image
        self.background_image = QPixmap("src/ui/assets/background.png")
        # Set the background brush to tile the image
        if not self.background_image.isNull():
            self.setBackgroundBrush(QBrush(self.background_image))
        
        # Background mode: 0 = image1, 1 = image2, 2 = solid color
        self.background_mode = 0
        # Grey color for solid background matching other windows
        self.background_color = QColor("#1E1E1E")
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release events on the scene background"""
        items = self.items(event.scenePos())
        if not items:
            # If clicked on empty space (no items at the position)
            if hasattr(self, 'parent') and self.parent() and hasattr(self.parent(), 'properties_manager'):
                # Clear the properties panel
                self.parent().properties_manager.clear_properties_panel()
                # Also hide the properties panel
                if hasattr(self.parent(), 'properties_dock'):
                    self.parent().properties_dock.setVisible(False)
        super().mouseReleaseEvent(event)
    
    def set_background(self, mode):
        """Change the background based on the specified mode
        mode: 0 = image1, 1 = image2, 2 = solid color
        """
        self.background_mode = mode
        
        if mode == 0:
            # Background 1 (default texture)
            self.background_image = QPixmap("src/ui/assets/background.png")
            if not self.background_image.isNull():
                self.setBackgroundBrush(QBrush(self.background_image))
        elif mode == 1:
            # Background 2 (alternate texture)
            self.background_image = QPixmap("src/ui/assets/background2.png")
            if not self.background_image.isNull():
                self.setBackgroundBrush(QBrush(self.background_image))
        elif mode == 2:
            # Solid color background
            self.setBackgroundBrush(QBrush(self.background_color))
        
        self.update()
    
    def drawBackground(self, painter, rect):
        # Call the base implementation to clear the background
        super().drawBackground(painter, rect)
        
        # If using solid color, draw dotted gridlines
        if self.background_mode == 2:
            # Set up a dotted pen for the grid
            gridPen = QPen(QColor(80, 80, 80, 180))  # Less transparent grey (alpha increased from 100 to 180)
            # Use custom dash pattern for sparser dashes: [dash length, space length]
            gridPen.setDashPattern([8, 12])  # Longer dashes with more space between them
            gridPen.setWidth(2)
            painter.setPen(gridPen)
            
            # Grid size (200x200 pixels)
            grid_size = 200
            
            # Calculate the grid based on the view rect
            left = int(rect.left()) - (int(rect.left()) % grid_size)
            top = int(rect.top()) - (int(rect.top()) % grid_size)
            
            # Draw vertical grid lines
            for x in range(left, int(rect.right()) + grid_size, grid_size):
                painter.drawLine(QPointF(x, rect.top()), QPointF(x, rect.bottom()))
                
            # Draw horizontal grid lines  
            for y in range(top, int(rect.bottom()) + grid_size, grid_size):
                painter.drawLine(QPointF(rect.left(), y), QPointF(rect.right(), y))
                
            return
            
        # Only proceed with background drawing if we have a valid background image
        if self.background_image.isNull():
            return
            
        # Tile size (300x300 pixels at 1x resolution)
        tile_size = 200
        
        # Calculate the grid based on the view rect
        left = int(rect.left()) - (int(rect.left()) % tile_size)
        top = int(rect.top()) - (int(rect.top()) % tile_size)
        
        # Draw the tiled background
        for x in range(left, int(rect.right()) + tile_size, tile_size):
            for y in range(top, int(rect.bottom()) + tile_size, tile_size):
                painter.drawPixmap(x, y, tile_size, tile_size, self.background_image)

class TiledBackgroundWidget(QWidget):
    """Widget that supports a tiled background image"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.background_image = None
        self.tile_size = 300  # Fixed tile size of 100x100 pixels
        
    def set_background(self, image_path):
        """Set the background image from a file path"""
        self.background_image = QPixmap(image_path)
        self.update()
        
    def paintEvent(self, event):
        """Override paintEvent to draw the tiled background"""
        painter = QPainter(self)
        
        # First call the base implementation to clear the background
        super().paintEvent(event)
        
        # Only proceed if we have a valid background image
        if not self.background_image or self.background_image.isNull():
            return
            
        # Get the size of the widget
        rect = self.rect()
        
        # Scale the background image to our fixed tile size
        scaled_image = self.background_image.scaled(self.tile_size, self.tile_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        
        # Calculate the grid based on the view rect
        left = int(rect.left()) - (int(rect.left()) % self.tile_size)
        top = int(rect.top()) - (int(rect.top()) % self.tile_size)
        
        # Draw the tiled background
        for x in range(left, int(rect.right()) + self.tile_size, self.tile_size):
            for y in range(top, int(rect.bottom()) + self.tile_size, self.tile_size):
                painter.drawPixmap(x, y, self.tile_size, self.tile_size, scaled_image)

class PowerSystemSimulator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OVERCLOCK | Watt-Bit Research | https://watt-bit.com | research preview presented by Augur VC | https://augurvc.com")
        self.resize(2400, 1200)
        
        # Initialize variables
        self.components = []
        self.connections = []
        self.creating_connection = False
        self.connection_source = None
        self.temp_connection = None
        self.cursor_phase = 0
        self.is_scrubbing = False
        self.scrub_timer = None
        
        # Create particle system for visual effects
        self.particle_system = None  # Will initialize after scene is created
        
        # Autocomplete state
        self.is_autocompleting = False
        self.autocomplete_timer = None
        self.autocomplete_end_time = 0
        
        # Track if the properties panel has been positioned yet
        self.properties_panel_positioned = False
        
        # Background mode: 0 = background1, 1 = background2, 2 = solid color
        self.background_mode = 2  # Set default to solid color (Background Off)
        
        # Create simulation engine
        self.simulation_engine = SimulationEngine(self)
        
        # Create properties manager
        self.properties_manager = ComponentPropertiesManager(self)
        
        # Create model manager
        self.model_manager = ModelManager(self)
        
        # Create historian manager
        self.historian_manager = HistorianManager(self)
        
        # Cursor animation
        self.cursor_timer = QTimer()
        self.cursor_timer.timeout.connect(self.update_cursor)
        self.cursor_size = 32
        
        # Create scene with custom signal
        self.scene = CustomScene()
        self.scene.parent = lambda: self
        self.scene.component_clicked.connect(self.properties_manager.show_component_properties)
        
        # Initialize particle system now that scene exists
        self.particle_system = ParticleSystem(self.scene)
        
        # Initialize the component adder
        self.component_adder = ComponentAdder(self)
        
        # Set the initial background mode to solid color
        self.scene.set_background(self.background_mode)
        
        # Flag to track whether we're in model or historian view
        self.is_model_view = True
        
        # Store the previous zoom value when switching to historian
        self.previous_zoom_value = None
        
        # Initialize the UI using the new UIInitializer
        UIInitializer.initialize_ui(self)
        
        # Setup simulation timer
        self.sim_timer = QTimer()
        self.sim_timer.timeout.connect(lambda: self.step_simulation(1))
        self.simulation_speed = 1
        
        # Create connection manager
        self.connection_manager = ConnectionManager(self)
        
        # Welcome text for new users
        self.welcome_text = None
        self.add_welcome_text()
         
        # Center the window on the screen
        self.center_on_screen()
        
        # Create KeyHandler instance
        self.key_handler = KeyHandler(self)
    
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
        # Check network connectivity before starting simulation
        if not self.simulation_engine.simulation_running and not self.check_network_connectivity():
            QMessageBox.warning(self, "Simulation Error",
                              "All components must be connected in a single network to run the simulation.\n\n"
                              "Please ensure all generators and loads are connected before starting.")
            return
        
        # Make sure we're not in scrub mode when starting playback
        if not self.simulation_engine.simulation_running:
            self.simulation_engine.is_scrubbing = False
            
        self.simulation_engine.simulation_running = not self.simulation_engine.simulation_running
        if self.simulation_engine.simulation_running:
            interval = int(100 / self.simulation_speed)
            self.sim_timer.start(interval)
            self.play_btn.setText("Pause (Space)")
            self.disable_component_buttons(True)
            
            # Disable autocomplete button during simulation and gray out text
            self.autocomplete_btn.setEnabled(False)
            self.autocomplete_btn.setStyleSheet("""
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
            self.sim_timer.stop()
            self.play_btn.setText("Run (Space)")
            self.disable_component_buttons(False)
            
            # Re-enable autocomplete button when simulation is paused and restore style
            self.autocomplete_btn.setEnabled(True)
            self.autocomplete_btn.setStyleSheet("""
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
        if not self.simulation_engine.simulation_running and self.play_btn.text() == "Pause (Space)":
            # Update UI to reflect that simulation has stopped
            self.play_btn.setText("Run (Space)")
            self.sim_timer.stop()
            self.disable_component_buttons(False)
            
            # Re-enable autocomplete button when simulation ends and restore style
            self.autocomplete_btn.setEnabled(True)
            self.autocomplete_btn.setStyleSheet("""
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
        self.simulation_engine.update_simulation()
        
        # Then increment to the next time step (time t+1)
        # Only if we successfully performed the step
        if self.simulation_engine.step_simulation(steps):
            # Update the time slider to show the new position
            self.time_slider.setValue(self.simulation_engine.current_time_step)
    
    def update_simulation(self):
        self.simulation_engine.update_simulation()
    
    def reset_simulation(self):
        # Check if simulation was running and stop it
        was_running = self.simulation_engine.simulation_running
        
        if was_running:
            # Stop the timer if running
            self.sim_timer.stop()
        
        # Stop autocomplete if it's running
        if self.is_autocompleting:
            if self.autocomplete_timer:
                self.autocomplete_timer.stop()
            self.is_autocompleting = False
            
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
            self.play_btn.setEnabled(True)
            self.play_btn.setStyleSheet(play_btn_style)
            
            self.reset_btn.setEnabled(True)
            self.time_slider.setEnabled(True)
            self.autocomplete_btn.setEnabled(True)
            
            self.speed_selector.setEnabled(True)
            self.speed_selector.setStyleSheet(speed_selector_style)
            
            self.disable_component_buttons(False)
            print("Autocomplete interrupted by reset.")
        
        # Set simulation state variables
        self.simulation_engine.current_time_step = 0
        self.simulation_engine.simulation_running = False
        self.simulation_engine.total_energy_imported = 0
        self.simulation_engine.total_energy_exported = 0
        self.simulation_engine.last_time_step = 0
        
        # Reset the gross revenue data
        self.simulation_engine.gross_revenue_data = [0.0] * 8761
        
        # Also reset accumulated revenue in all load components
        for item in self.scene.items():
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
        self.play_btn.setText("Run (Space)")
        self.time_slider.setValue(0)
        
        # Re-enable component buttons if they were disabled
        if was_running:
            self.disable_component_buttons(False)
        
        # Clear the analytics chart history
        self.analytics_panel.clear_chart_history()
        
        # Reset Historian data and clear its chart
        self.simulation_engine.reset_historian()
        self.historian_manager.clear_chart()
        
        # Always ensure autocomplete button is re-enabled and properly styled after reset
        self.autocomplete_btn.setEnabled(True)
        self.autocomplete_btn.setStyleSheet("""
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
            if self.autocomplete_timer:
                self.autocomplete_timer.stop()
            self.is_autocompleting = False
            
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
            
            # Reset the button styles
            self.play_btn.setStyleSheet(play_btn_style)
            self.speed_selector.setStyleSheet(speed_selector_style)
            
            # Controls will be re-enabled after successful load by model_manager
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
        # Create a pixmap the size of the viewport
        pixmap = QPixmap(self.view.viewport().size())
        pixmap.fill(Qt.transparent)
        
        # Create painter for the pixmap
        painter = QPainter(pixmap)
        
        # Render the view onto the pixmap
        self.view.render(painter)
        
        # Add the Overclock logo overlay if it exists
        if hasattr(self, 'logo_overlay') and not self.logo_overlay.pixmap().isNull():
            # Get the logo position and pixmap
            logo_pos = self.logo_overlay.pos()
            logo_pixmap = self.logo_overlay.pixmap()
            
            # Draw the logo at its current position
            painter.drawPixmap(logo_pos, logo_pixmap)
        
        # Add the mode toggle button if it exists
        if hasattr(self, 'mode_toggle_btn'):
            # Create a pixmap from the mode toggle button
            mode_btn_pixmap = QPixmap(self.mode_toggle_btn.size())
            mode_btn_pixmap.fill(Qt.transparent)
            self.mode_toggle_btn.render(mode_btn_pixmap)
            
            # Get the button position
            mode_btn_pos = self.mode_toggle_btn.pos()
            
            # Draw the button at its current position
            painter.drawPixmap(mode_btn_pos, mode_btn_pixmap)
        
        # End painting
        painter.end()
        
        # Copy pixmap to clipboard
        clipboard = QApplication.clipboard()
        clipboard.setPixmap(pixmap)
        
        # Show confirmation to user
        QMessageBox.information(self, "Screenshot", "Screenshot copied to clipboard") 

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
        if self.is_model_view:
            # Switching to Historian mode
            self.mode_toggle_btn.setText("💾 Historian (TAB)")
            
            # Hide the properties panel if it's open
            if self.properties_dock.isVisible():
                self.properties_dock.setVisible(False)
            
            # Hide the analytics panel if it's open
            if self.analytics_dock.isVisible():
                self.analytics_dock.setVisible(False)
            
            # Hide the analytics toggle button in historian view
            if hasattr(self, 'analytics_toggle_btn'):
                self.analytics_toggle_btn.hide()
            
            # Disable the toolbar menu buttons for properties and analytics
            self.properties_action.setEnabled(False)
            self.analytics_action.setEnabled(False)
            
            # Disable all component buttons
            self.disable_component_buttons(True)
            
            # Disable background toggle button in historian view and apply disabled style
            self.background_toggle_btn.setEnabled(False)
            self.background_toggle_btn.setStyleSheet("""
                QPushButton { 
                    background-color: #3D3D3D; 
                    color: #999999; 
                    border: 1px solid #555555; 
                    border-radius: 3px; 
                    padding: 5px; 
                }
            """)
            
            # Switch to the historian view
            self.switch_to_historian_view()
        else:
            # Switching back to Model mode
            self.mode_toggle_btn.setText("🧩 Model (TAB)")
            
            # Show the analytics toggle button when returning to model view
            if hasattr(self, 'analytics_toggle_btn'):
                self.analytics_toggle_btn.show()
            
            # Re-enable the toolbar menu buttons
            self.properties_action.setEnabled(True)
            self.analytics_action.setEnabled(True)
            
            # Re-enable all component buttons
            self.disable_component_buttons(False)
            
            # Re-enable background toggle button in model view with original style
            self.background_toggle_btn.setEnabled(True)
            self.background_toggle_btn.setStyleSheet("""
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
            """)
            
            # Switch back to the model view
            self.switch_to_model_view()

    def switch_to_historian_view(self):
        """Switch from model view to historian view"""
        if self.is_model_view:
            # Store the current zoom slider value
            self.previous_zoom_value = self.zoom_slider.value()
            
            # Set flag to indicate we're now in historian view
            self.is_model_view = False
            
            # Hide the analytics panel if it's open
            if self.analytics_dock.isVisible():
                self.analytics_dock.setVisible(False)
            
            # Hide the analytics toggle button in historian view
            if hasattr(self, 'analytics_toggle_btn'):
                self.analytics_toggle_btn.hide()
            
            # Disable the toolbar menu buttons for properties and analytics
            self.properties_action.setEnabled(False)
            self.analytics_action.setEnabled(False)
            
            # Update the historian chart with current data
            self.historian_manager.update_chart()
            
            # Change the view to show the historian scene
            self.view.setScene(self.historian_manager.historian_scene)
            
            # Disable scrolling and movement in historian view
            self.view.setDragMode(QGraphicsView.NoDrag)
            self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            
            # Resize the chart widget to fit the current view size
            view_size = self.view.viewport().size()
            self.historian_manager.resize_chart_widget(view_size.width(), view_size.height())
            
            # Set zoom to 1x and disable slider
            self.zoom_slider.setValue(100)  # Set slider to 1.0x
            self.zoom_slider.setEnabled(False)
            
            # Ensure background toggle is disabled with gray text
            self.background_toggle_btn.setEnabled(False)
            self.background_toggle_btn.setStyleSheet("""
                QPushButton { 
                    background-color: #3D3D3D; 
                    color: #999999; 
                    border: 1px solid #555555; 
                    border-radius: 3px; 
                    padding: 5px; 
                }
            """)
            
            # Note: Setting the slider value automatically triggers zoom_changed,
            # which applies the transform and updates the view.

    def switch_to_model_view(self):
        """Switch from historian view back to model view"""
        if not self.is_model_view:
            # Set flag to indicate we're now in model view
            self.is_model_view = True
            
            # Change the view back to show the model scene
            self.view.setScene(self.scene)
            
            # Re-enable scrolling and movement in model view
            self.view.setDragMode(QGraphicsView.ScrollHandDrag)
            self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            
            # Re-enable zoom slider and restore previous value
            self.zoom_slider.setEnabled(True)
            if self.previous_zoom_value is not None:
                self.zoom_slider.setValue(self.previous_zoom_value)
            
            # Re-enable background toggle button with original style
            self.background_toggle_btn.setEnabled(True)
            self.background_toggle_btn.setStyleSheet("""
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
            """)
            
            # Reset the stored previous value
            self.previous_zoom_value = None
            
            # Note: Setting the slider value automatically triggers zoom_changed,
            # which applies the transform and updates the view. 

    def run_autocomplete(self):
        """Run the simulation from the current time to the end asynchronously"""
        
        # Check if already running
        if self.simulation_engine.simulation_running or self.is_autocompleting:
            return
        
        # Check network connectivity first
        if not self.check_network_connectivity():
            QMessageBox.warning(self, "Simulation Error",
                              "All components must be connected in a single network to run the simulation.\n\n"
                              "Please ensure all generators and loads are connected before starting.")
            return
        
        # Switch to historian view if currently in model view
        if self.is_model_view:
            self.switch_to_historian_view()
            self.mode_toggle_btn.setText("💾 Historian (TAB)")
        
        # Ensure we're not in scrub mode
        self.simulation_engine.is_scrubbing = False
        
        # Get current and end times
        start_time = self.simulation_engine.current_time_step
        self.autocomplete_end_time = self.time_slider.maximum()
        
        # If already at the end, do nothing
        if start_time >= self.autocomplete_end_time:
            return
            
        print("Starting Autocomplete simulation...")
        self.is_autocompleting = True
        
        # Define disabled styles for buttons
        disabled_play_btn_style = "QPushButton { background-color: #2196F3; color: #99CCFF; border: 1px solid #555555; border-radius: 3px; padding: 5px; font-weight: bold; font-size: 16px; }"
        disabled_speed_selector_style = "QPushButton { background-color: #3D3D3D; color: #999999; border: 1px solid #555555; border-radius: 3px; padding: 4px; font-weight: bold; font-size: 14px;}"
        
        # Save original button text for restoration
        self.play_btn_text = self.play_btn.text()
        self.speed_selector_text = self.speed_selector.text()
        
        # Disable controls during autocomplete
        self.play_btn.setEnabled(False)
        self.play_btn.setStyleSheet(disabled_play_btn_style)
        
        self.reset_btn.setEnabled(False)
        self.time_slider.setEnabled(False)
        self.autocomplete_btn.setEnabled(False)
        
        self.speed_selector.setEnabled(False)
        self.speed_selector.setStyleSheet(disabled_speed_selector_style)
        
        self.disable_component_buttons(True) # Also disable component add/connect buttons

        # Create and start the timer if it doesn't exist
        if not self.autocomplete_timer:
            self.autocomplete_timer = QTimer(self)
            self.autocomplete_timer.timeout.connect(self._step_autocomplete)
            
        # Start timer with 0 interval for maximum speed while yielding
        self.autocomplete_timer.start(0) 
        
    def _step_autocomplete(self):
        """Perform a single step of the autocomplete process"""
        current_time = self.simulation_engine.current_time_step
        
        if current_time < self.autocomplete_end_time:
            # Process the current time step first (including time step 0)
            self.simulation_engine.update_simulation(skip_ui_updates=True)
            
            # Then increment for the next iteration
            self.simulation_engine.current_time_step += 1
            
            # Update only the time slider during the loop
            self.time_slider.setValue(self.simulation_engine.current_time_step)
            
            # Keep timer running for the next step
        else:
            # Reached the end
            self.autocomplete_timer.stop()
            self.is_autocompleting = False
            
            # Perform one final update to refresh UI elements and charts
            # This call will not skip UI updates
            self.simulation_engine.update_simulation()
            # Explicitly update historian chart if needed
            if not self.is_model_view:
                self.historian_manager.update_chart()
            
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
            self.play_btn.setEnabled(True)
            self.play_btn.setStyleSheet(play_btn_style)
            
            self.reset_btn.setEnabled(True)
            self.time_slider.setEnabled(True)
            self.autocomplete_btn.setEnabled(True)
            
            self.speed_selector.setEnabled(True)
            self.speed_selector.setStyleSheet(speed_selector_style)
            
            self.disable_component_buttons(False)
            
            print("Autocomplete simulation finished.") 