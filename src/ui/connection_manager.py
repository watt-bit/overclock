from PyQt6.QtWidgets import (QGraphicsLineItem, QApplication)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QPen, QCursor, QPixmap, QColor
import math

from src.components.bus import BusComponent
from src.components.generator import GeneratorComponent
from src.components.load import LoadComponent
from src.components.grid_import import GridImportComponent
from src.components.grid_export import GridExportComponent
from src.components.connection import Connection
from src.components.tree import TreeComponent
from src.components.bush import BushComponent
from src.components.pond import PondComponent
from src.components.house1 import House1Component
from src.components.house2 import House2Component
from src.components.factory import FactoryComponent
from src.components.cloud_workload import CloudWorkloadComponent
from src.components.traditional_data_center import TraditionalDataCenterComponent
from src.components.distribution_pole import DistributionPoleComponent
from src.ui.terminal_widget import TerminalWidget

class ConnectionManager:
    def __init__(self, main_window):
        self.main_window = main_window
        self.scene = main_window.scene
        self.view = main_window.view
        
        # Connection state variables
        self.creating_connection = False
        self.connection_source = None
        self.temp_connection = None
        self.cursor_phase = 0
        
        # Reference to UI elements
        self.connection_btn = main_window.connection_btn
        self.cursor_timer = main_window.cursor_timer
        self.cursor_size = main_window.cursor_size
        
    def start_connection(self):
        if not self.creating_connection:
            # Clean up any existing state
            self.cursor_timer.stop()
            self.view.setCursor(Qt.CursorShape.ArrowCursor)
            self.view.viewport().setCursor(Qt.CursorShape.ArrowCursor)
            
            # Reset all connection state variables
            self.connection_source = None
            if self.temp_connection:
                self.scene.removeItem(self.temp_connection)
                self.temp_connection = None
            
            self.creating_connection = True
            self.main_window.creating_connection = True
            # Disable connection button
            self.connection_btn.setEnabled(False)
            # Start cursor animation
            self.cursor_phase = 0
            self.cursor_timer.start(50)  # Update every 50ms
            # Set initial cursor
            cursor = self.create_connection_cursor(self.cursor_phase)
            self.view.setCursor(cursor)  # Set cursor on both view
            self.view.viewport().setCursor(cursor)  # and viewport
            # Disconnect component clicked from properties
            self.scene.component_clicked.disconnect(self.main_window.properties_manager.show_component_properties)
            # Connect to handle_connection_click instead
            self.scene.component_clicked.connect(self.handle_connection_click)
    
    def cancel_connection(self):
        """Cancel the current connection creation"""
        if self.creating_connection:
            # Clean up temporary connection if it exists
            if self.temp_connection:
                self.scene.removeItem(self.temp_connection)
                self.temp_connection = None
            
            self.connection_source = None
            self.creating_connection = False
            self.main_window.creating_connection = False
            # Stop cursor animation and restore default cursor
            self.cursor_timer.stop()
            self.view.setCursor(Qt.CursorShape.ArrowCursor)
            self.view.viewport().setCursor(Qt.CursorShape.ArrowCursor)
            # Re-enable connection button
            self.connection_btn.setEnabled(True)
            self.view.setMouseTracking(False)
            self.view.viewport().removeEventFilter(self.main_window)
            # Restore original click behavior
            if self.scene.receivers(self.scene.component_clicked) > 0:
                self.scene.component_clicked.disconnect(self.handle_connection_click)
            self.scene.component_clicked.connect(self.main_window.properties_manager.show_component_properties)
    
    def validate_cloud_workload_connection(self, source, target):
        """
        Validate that cloud workload components can only connect to data center loads
        
        Args:
            source: The source component
            target: The target component
            
        Returns:
            (bool, str): Tuple of (is_valid, error_message)
        """
        # Check if either component is a CloudWorkloadComponent
        is_cloud_source = isinstance(source, CloudWorkloadComponent)
        is_cloud_target = isinstance(target, CloudWorkloadComponent)
        
        # If neither is a cloud component, connection is valid
        if not is_cloud_source and not is_cloud_target:
            return True, ""
        
        # We have a cloud workload component, check the other component
        cloud_component = source if is_cloud_source else target
        other_component = target if is_cloud_source else source
        
        # Cloud workload can only connect to Data Center load
        if isinstance(other_component, LoadComponent) and other_component.profile_type == "Data Center":
            return True, ""
        
        # Connection is invalid - return error message
        return False, "Cloud Workload components can only connect to Load components in Data Center mode."
    
    def handle_connection_click(self, component):
        """Handle clicks on components for connection creation"""
        # Ignore decorative components
        if isinstance(component, (TreeComponent, BushComponent, PondComponent, House1Component, House2Component, FactoryComponent, TraditionalDataCenterComponent, DistributionPoleComponent)):
            return
            
        if not self.connection_source:
            # First click - set source
            self.connection_source = component
            # Create temporary visual connection that follows mouse
            self.temp_connection = QGraphicsLineItem()
            self.temp_connection.setPen(QPen(Qt.GlobalColor.darkGray, 2, Qt.PenStyle.DashLine))
            self.scene.addItem(self.temp_connection)
            # Enable mouse tracking
            self.view.setMouseTracking(True)
            self.view.viewport().installEventFilter(self.main_window)
        else:
            # Second click - create final connection
            if component != self.connection_source:  # Prevent self-connection
                # Create a temporary set for tracking connections
                connected_pairs = set()
                
                # Call the shared connection creation method
                connection_created = self.create_connection_between(
                    self.connection_source, component, connected_pairs, show_errors=True
                )
                
                if connection_created:
                    self.main_window.update_simulation()
                    
                    # Validate bus states after creating a connection
                    self.main_window.validate_bus_states()
                    
                    # Create connection spark effect at the cursor position
                    if hasattr(self.main_window, 'particle_system'):
                        # Get the current cursor position in view coordinates
                        cursor_pos = self.view.mapFromGlobal(QCursor.pos())
                        # Convert to scene coordinates
                        scene_pos = self.view.mapToScene(cursor_pos)
                        # Create spark effect
                        self.main_window.particle_system.create_connection_success_sparks(
                            scene_pos.x(), scene_pos.y()
                        )
                    
                    # Trigger success flash for successful connection
                    bordered_widget = self.main_window.centralWidget()
                    if hasattr(bordered_widget, 'trigger_success_flash'):
                        bordered_widget.trigger_success_flash()
                else:
                    # Connection failed - trigger error flash
                    # Access the BorderedMainWidget which is the central widget
                    bordered_widget = self.main_window.centralWidget()
                    if hasattr(bordered_widget, 'trigger_error_flash'):
                        bordered_widget.trigger_error_flash()
            
            # Always clean up, whether connection succeeded or failed
            self.cancel_connection()
            
            # Ensure we reset to initial state completely even after errors
            self.connection_source = None
            self.temp_connection = None
            self.creating_connection = False
            self.main_window.creating_connection = False
    
    def handle_mouse_move_for_connection(self, event):
        """Handle mouse movement for the temporary connection line"""
        if self.temp_connection and self.connection_source:
            # Get source component center in scene coordinates
            source_pos = self.connection_source.sceneBoundingRect().center()
            # Convert mouse position to scene coordinates
            mouse_pos = self.view.mapToScene(event.pos())
            # Update the temporary line
            self.temp_connection.setLine(source_pos.x(), source_pos.y(),
                                     mouse_pos.x(), mouse_pos.y())
            return True  # Event has been handled
        return False
    
    def create_connection_cursor(self, phase):
        """Create a custom cursor for connection mode with pulsing effect"""
        size = self.cursor_size
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Calculate pulse effect (0.0 to 1.0)
        pulse = abs(math.sin(phase))
        
        # Draw outer glow with higher opacity
        glow_color = QColor(255, 215, 0, int(180 * pulse))  # Golden yellow with varying opacity
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(glow_color)
        painter.drawEllipse(4, 4, size-8, size-8)
        
        # Draw crosshair with thicker lines
        painter.setPen(QPen(QColor(255, 215, 0), 3))  # Thicker golden yellow lines
        # Horizontal line
        painter.drawLine(2, size//2, size-2, size//2)
        # Vertical line
        painter.drawLine(size//2, 2, size//2, size-2)
        
        # Must end painter before creating cursor
        painter.end()
        
        # Set hot spot to center of cursor
        return QCursor(pixmap, size//2, size//2)

    def update_cursor(self):
        """Update the cursor appearance for the pulsing effect"""
        if self.creating_connection:
            self.cursor_phase += 0.2
            cursor = self.create_connection_cursor(self.cursor_phase)
            self.view.setCursor(cursor)  # Set cursor on both view
            self.view.viewport().setCursor(cursor)  # and viewport 

    def autoconnect_all_components(self):
        """Automatically connect all components in the scene to form a valid network"""
        if not self.main_window.components:
            TerminalWidget.log("Autoconnect: No components available to connect.")
            return
        
        # Disable the autoconnect button to prevent double-clicks
        if hasattr(self.main_window, 'autoconnect_btn'):
            self.main_window.autoconnect_btn.setEnabled(False)
        
        try:
            # Save a copy of the components list
            saved_components = self.main_window.components.copy()
            
            # Remove all connections manually
            for connection in list(self.main_window.connections):
                # First clean up the connection
                connection.cleanup()
                # Remove from scene if it's still valid
                try:
                    self.scene.removeItem(connection)
                except RuntimeError:
                    pass  # Already removed, ignore
            
            # Clear connections list
            self.main_window.connections.clear()
                
            # Dictionary to track which components are already connected
            connected_pairs = set()
            
            # Strategy: Connect components in a logical pattern
            # Priority: Bus → Generators → Loads → Grid connections
            
            # Find components by type (exclude TreeComponent instances)
            buses = [c for c in self.main_window.components if isinstance(c, BusComponent)]
            generators = [c for c in self.main_window.components if isinstance(c, GeneratorComponent)]
            loads = [c for c in self.main_window.components if isinstance(c, LoadComponent)]
            grid_import = [c for c in self.main_window.components if isinstance(c, GridImportComponent)]
            grid_export = [c for c in self.main_window.components if isinstance(c, GridExportComponent)]
            cloud_workloads = [c for c in self.main_window.components if isinstance(c, CloudWorkloadComponent)]
            
            # Identify data center loads specifically
            data_center_loads = [load for load in loads if load.profile_type == "Data Center"]
            
            # 1. If there are buses, connect generators to buses
            if buses:
                # Connect generators to buses (distribute evenly if multiple buses)
                for i, generator in enumerate(generators):
                    bus = buses[i % len(buses)]  # Distribute evenly
                    self.create_connection_between(generator, bus, connected_pairs)
                
                # Connect loads to buses (distribute evenly if multiple buses)
                for i, load in enumerate(loads):
                    bus = buses[i % len(buses)]  # Distribute evenly
                    self.create_connection_between(load, bus, connected_pairs)
                
                # Connect grid connections to buses
                for i, grid in enumerate(grid_import + grid_export):
                    bus = buses[i % len(buses)]  # Distribute evenly
                    self.create_connection_between(grid, bus, connected_pairs)
                    
                # Connect cloud workloads to buses (they'll indirectly connect to data center loads)
                for i, cloud in enumerate(cloud_workloads):
                    bus = buses[i % len(buses)]  # Distribute evenly
                    self.create_connection_between(cloud, bus, connected_pairs)
            else:
                # No buses - connect generators directly to loads
                if generators and loads:
                    # Connect generators to loads (distribute evenly)
                    for i, generator in enumerate(generators):
                        load = loads[i % len(loads)]
                        self.create_connection_between(generator, load, connected_pairs)
                
                # Connect grid import to loads if there are any loads
                if loads and grid_import:
                    for i, load in enumerate(loads):
                        grid = grid_import[i % len(grid_import)]
                        self.create_connection_between(grid, load, connected_pairs)
                
                # Connect generators to grid export if there are any grid exports
                if generators and grid_export:
                    for i, generator in enumerate(generators):
                        grid = grid_export[i % len(grid_export)]
                        self.create_connection_between(generator, grid, connected_pairs)
                
                # Connect grid import to grid export if both exist
                if grid_import and grid_export:
                    for i, g_import in enumerate(grid_import):
                        g_export = grid_export[i % len(grid_export)]
                        self.create_connection_between(g_import, g_export, connected_pairs)
                        
                # Connect cloud workloads directly to data center loads if available
                if cloud_workloads and data_center_loads:
                    for i, cloud in enumerate(cloud_workloads):
                        # Try to connect to a data center load
                        dc_load = data_center_loads[i % len(data_center_loads)]
                        self.create_connection_between(cloud, dc_load, connected_pairs)
            
            # Special handling: Ensure all cloud workloads are connected to data center loads when possible
            # Do this separately to prioritize these connections regardless of other network structure
            if cloud_workloads and data_center_loads:
                for cloud in cloud_workloads:
                    # Check if cloud workload is already connected
                    cloud_id = id(cloud)
                    cloud_connected = False
                    
                    for pair in connected_pairs:
                        if cloud_id in pair:
                            cloud_connected = True
                            break
                    
                    # If not connected, try to connect to any data center load
                    if not cloud_connected:
                        for dc_load in data_center_loads:
                            if self.create_connection_between(cloud, dc_load, connected_pairs):
                                break  # Successfully connected
            
            # STEP 2: Ensure all components are connected in a single network
            # Build a graph of the current connections
            connection_graph = {id(component): set() for component in self.main_window.components}
            for pair in connected_pairs:
                source_id, target_id = pair
                connection_graph[source_id].add(target_id)
                connection_graph[target_id].add(source_id)
            
            # Find connected components in the graph (using BFS)
            connected_components = self.find_connected_components(connection_graph)
            
            # If more than one connected component, connect them together
            if len(connected_components) > 1:
                # Connect each component to the next one
                for i in range(len(connected_components) - 1):
                    # Take one node from each component
                    comp1_node_id = connected_components[i][0]
                    comp2_node_id = connected_components[i + 1][0]
                    
                    # Find the actual component objects
                    comp1_node = next(c for c in self.main_window.components if id(c) == comp1_node_id)
                    comp2_node = next(c for c in self.main_window.components if id(c) == comp2_node_id)
                    
                    # Connect them
                    self.create_connection_between(comp1_node, comp2_node, connected_pairs)
            
            # STEP 3: Final check - ensure any isolated components are connected
            # Create a list of all component IDs
            all_component_ids = [id(c) for c in self.main_window.components]
            
            # Find any components not in any connection
            connected_component_ids = set(sum(connected_components, []))
            isolated_component_ids = set(all_component_ids) - connected_component_ids
            
            # Connect any isolated components to the main network
            if isolated_component_ids and connected_component_ids:
                # Take the first node from the largest connected component as anchor
                largest_component = max(connected_components, key=len)
                anchor_id = largest_component[0]
                anchor_component = next(c for c in self.main_window.components if id(c) == anchor_id)
                
                # Connect each isolated component to the anchor
                for isolated_id in isolated_component_ids:
                    isolated_component = next(c for c in self.main_window.components if id(c) == isolated_id)
                    self.create_connection_between(anchor_component, isolated_component, connected_pairs)
            
            # Verify network connectivity
            if self.main_window.check_network_connectivity():
                # Trigger success flash before showing the success message
                bordered_widget = self.main_window.centralWidget()
                if hasattr(bordered_widget, 'trigger_success_flash'):
                    bordered_widget.trigger_success_flash()
                
                TerminalWidget.log(f"Autoconnect: Successfully created {len(self.main_window.connections)} connections.")
            else:
                # Final fallback: connect everything in a line
                if not self.main_window.check_network_connectivity():
                    self.connect_all_in_sequence(connected_pairs)
        finally:
            # Re-enable the autoconnect button
            if hasattr(self.main_window, 'autoconnect_btn'):
                self.main_window.autoconnect_btn.setEnabled(True)
    
    def find_connected_components(self, graph):
        """Find connected components in the graph (using BFS)"""
        components = []
        visited = set()
        
        for node in graph:
            if node not in visited:
                # Start a new connected component
                component = []
                queue = [node]
                visited.add(node)
                
                while queue:
                    current = queue.pop(0)
                    component.append(current)
                    
                    for neighbor in graph[current]:
                        if neighbor not in visited:
                            visited.add(neighbor)
                            queue.append(neighbor)
                
                components.append(component)
        
        return components
    
    def connect_all_in_sequence(self, connected_pairs):
        """Last resort fallback: connect all components in a simple line/sequence"""
        # Simply connect each component to the next one
        for i in range(len(self.main_window.components) - 1):
            component1 = self.main_window.components[i]
            component2 = self.main_window.components[i + 1]
            self.create_connection_between(component1, component2, connected_pairs)

    def create_connection_between(self, source, target, connected_pairs, show_errors=False):
        """Create a connection between two components if not already connected"""
        # Check if this pair is already connected (in either direction)
        if (id(source), id(target)) in connected_pairs or (id(target), id(source)) in connected_pairs:
            if show_errors:
                TerminalWidget.log("Error: These components are already connected to each other.")
            return False
        
        # Check if these components are already connected directly
        for conn in source.connections:
            if (conn.source == source and conn.target == target) or \
               (conn.source == target and conn.target == source):
                if show_errors:
                    TerminalWidget.log("Error: These components are already connected to each other.")
                return False
        
        # Validate cloud workload connection
        is_valid, error_message = self.validate_cloud_workload_connection(source, target)
        if not is_valid:
            if show_errors:
                TerminalWidget.log(f"Error: Invalid Connection - {error_message}")
            return False
            
        # Safety check for deleted components
        try:
            # Verify both components are still valid
            if not source.scene() or not target.scene():
                return False
                
            # Create the connection
            connection = Connection(source, target)
            self.scene.addItem(connection)
            connection.setup_component_tracking()
            self.main_window.connections.append(connection)
            
            # Log connection to terminal
            source_type = source.component_type if hasattr(source, 'component_type') else source.__class__.__name__
            target_type = target.component_type if hasattr(target, 'component_type') else target.__class__.__name__
            source_id = str(id(source))[-6:]  # Last 6 digits of source ID
            target_id = str(id(target))[-6:]  # Last 6 digits of target ID
            TerminalWidget.log(f"Connected {source_type} {source_id} to {target_type} {target_id}")
            
            # Mark this pair as connected
            connected_pairs.add((id(source), id(target)))
            return True
        except (RuntimeError, AttributeError):
            # Handle case where C++ objects have been deleted
            return False 