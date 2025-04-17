from PyQt5.QtCore import Qt, QObject
from PyQt5.QtWidgets import QLineEdit, QApplication

from src.components.tree import TreeComponent
from src.components.bush import BushComponent
from src.components.pond import PondComponent
from src.components.house1 import House1Component
from src.components.house2 import House2Component
from src.components.factory import FactoryComponent
from src.components.traditional_data_center import TraditionalDataCenterComponent
from src.components.distribution_pole import DistributionPoleComponent


class KeyHandler(QObject):
    """
    Handles key press events for the Power System Simulator.
    This class extracts the keyPressEvent logic from the main window
    for better code organization.
    """
    
    def __init__(self, main_window):
        """
        Initialize with a reference to the main window.
        
        Args:
            main_window: Reference to the PowerSystemSimulator instance
        """
        super().__init__()  # Initialize QObject parent
        self.main_window = main_window
        
        # Install an application-wide event filter to capture key presses 
        # regardless of which widget has focus
        QApplication.instance().installEventFilter(self)
    
    def eventFilter(self, obj, event):
        """
        Global event filter that catches key events application-wide.
        This will process key events even when focus is in the properties panel.
        
        Args:
            obj: The object receiving the event
            event: The event being processed
        
        Returns:
            bool: True if the event was handled, False otherwise
        """
        # Only process KeyPress events
        if event.type() == event.KeyPress:
            # Don't process keystrokes if we're typing in a text field
            if isinstance(QApplication.focusWidget(), QLineEdit):
                return False
                
            # Check for the Delete key
            if event.key() == Qt.Key_Delete:
                # Process deletion for selected items in the scene
                selected_items = [item for item in self.main_window.scene.selectedItems() if hasattr(item, 'connections')]
                
                if selected_items:
                    # Delete all selected components
                    for component in selected_items:
                        # Find and remove all connections associated with this component
                        connections_to_remove = [conn for conn in self.main_window.connections 
                                        if conn.source == component or conn.target == component]
                        
                        for connection in connections_to_remove:
                            connection.cleanup()
                            self.main_window.scene.removeItem(connection)
                            if connection in self.main_window.connections:
                                self.main_window.connections.remove(connection)
                        
                        # Remove component's historian keys
                        self.main_window.simulation_engine.remove_component_historian_keys(component)
                        
                        # Remove the component from the scene
                        self.main_window.scene.removeItem(component)
                        
                        # Only remove from components list if it's a functional component and in the list
                        if (not isinstance(component, (TreeComponent, BushComponent, PondComponent, 
                                                      House1Component, House2Component, FactoryComponent,
                                                      TraditionalDataCenterComponent, DistributionPoleComponent)) and 
                            component in self.main_window.components):
                            self.main_window.components.remove(component)
                    
                    # Clear the properties panel
                    self.main_window.properties_dock.setVisible(False)
                    
                    # Update simulation state
                    self.main_window.update_simulation()
                    
                    # Update the CAPEX display after deleting components
                    self.main_window.update_capex_display()
                    
                    return True
                # Handle property panel component
                elif hasattr(self.main_window.properties_manager, 'current_component') and self.main_window.properties_manager.current_component:
                    # Only delete the component if it's still selected in the scene
                    if self.main_window.properties_manager.current_component.isSelected():
                        self.main_window.properties_manager.delete_component()
                        self.main_window.properties_dock.setVisible(False)
                        return True
        
        # Let the event continue to be processed
        return False
        
    def handle_key_press(self, event):
        """
        Handle key press events for hotkeys.
        
        Args:
            event: QKeyEvent to process
        
        Returns:
            bool: True if the event was handled, False otherwise
        """
        # Skip if we're typing in a text field
        if isinstance(self.main_window.focusWidget(), QLineEdit):
            return False
            
        key = event.key()
        
        # Space for play/pause - active unless in autocomplete mode
        if key == Qt.Key_Space and not self.main_window.is_autocompleting:
            self.main_window.toggle_simulation()
            return True
            
        # Tab is now handled by QShortcut for better reliability
        
        # Enter key for autocomplete - active unless simulation is running
        if key == Qt.Key_Return and not self.main_window.simulation_engine.simulation_running:
            self.main_window.run_autocomplete()
            return True
            
        # Delete key for deleting selected component is now handled by the event filter
        # but kept here for backward compatibility
        if key == Qt.Key_Delete:
            # Check if any components are selected in the scene
            selected_items = [item for item in self.main_window.scene.selectedItems() if hasattr(item, 'connections')]
            
            if selected_items:
                # Delete all selected components
                for component in selected_items:
                    # Find and remove all connections associated with this component
                    connections_to_remove = [conn for conn in self.main_window.connections 
                                    if conn.source == component or conn.target == component]
                    
                    for connection in connections_to_remove:
                        connection.cleanup()
                        self.main_window.scene.removeItem(connection)
                        if connection in self.main_window.connections:
                            self.main_window.connections.remove(connection)
                    
                    # Remove component's historian keys
                    self.main_window.simulation_engine.remove_component_historian_keys(component)
                    
                    # Remove the component from the scene
                    self.main_window.scene.removeItem(component)
                    
                    # Only remove from components list if it's a functional component and in the list
                    if (not isinstance(component, (TreeComponent, BushComponent, PondComponent, 
                                                  House1Component, House2Component, FactoryComponent,
                                                  TraditionalDataCenterComponent, DistributionPoleComponent)) and 
                        component in self.main_window.components):
                        self.main_window.components.remove(component)
                
                # Clear the properties panel
                self.main_window.properties_dock.setVisible(False)
                
                # Update simulation state
                self.main_window.update_simulation()
                
                # Update the CAPEX display after deleting components
                self.main_window.update_capex_display()
                
                return True
            # If no scene items are selected, check if properties manager has a current component
            elif hasattr(self.main_window.properties_manager, 'current_component') and self.main_window.properties_manager.current_component:
                # Only delete the component if it's still selected in the scene
                if self.main_window.properties_manager.current_component.isSelected():
                    self.main_window.properties_manager.delete_component()
                    self.main_window.properties_dock.setVisible(False)
                    return True
                
        # R key for reset simulation - always active regardless of mode
        if key == Qt.Key_R:
            self.main_window.reset_simulation()
            return True
        
        # P key for toggling analytics panel - active only in model view
        if key == Qt.Key_P:
            # Only process if in model view (not in historian view)
            if self.main_window.is_model_view:
                self.main_window.toggle_analytics_panel()
                return True
        
        # Only process if not in connection mode, sever mode, and simulation is not running
        if (not self.main_window.creating_connection and 
            self.main_window.connection_btn.isEnabled() and 
            self.main_window.sever_connection_btn.isEnabled() and
            not self.main_window.simulation_engine.simulation_running):
            # G for generator
            if key == Qt.Key_G:
                self.main_window.add_component("generator")
                return True
            # B for bus
            elif key == Qt.Key_B:
                self.main_window.add_component("bus")
                return True
            # L for load
            elif key == Qt.Key_L:
                self.main_window.add_component("load")
                return True
            # I for grid import
            elif key == Qt.Key_I:
                self.main_window.add_component("grid_import")
                return True
            # E for grid export
            elif key == Qt.Key_E:
                self.main_window.add_component("grid_export")
                return True
            # S for battery storage
            elif key == Qt.Key_S:
                self.main_window.add_component("battery")
                return True
            # W for cloud workload
            elif key == Qt.Key_W:
                self.main_window.add_component("cloud_workload")
                return True
            # C for create connection
            elif key == Qt.Key_C:
                self.main_window.start_connection()
                return True
            # A for autoconnect
            elif key == Qt.Key_A:
                self.main_window.autoconnect_all_components()
                return True
        
        # Event not handled by this handler
        return False 