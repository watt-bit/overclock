from src.components.tree import TreeComponent
from src.components.bush import BushComponent
from src.components.pond import PondComponent
from src.components.house1 import House1Component
from src.components.house2 import House2Component
from src.components.factory import FactoryComponent
from src.components.traditional_data_center import TraditionalDataCenterComponent
from src.components.distribution_pole import DistributionPoleComponent
from src.ui.terminal_widget import TerminalWidget


class ComponentDeleter:
    """
    Handles component deletion in the Power System Simulator.
    This class extracts the component deletion logic to be used by both
    KeyHandler and PropertiesManager.
    """
    
    def __init__(self, main_window):
        """
        Initialize with a reference to the main window.
        
        Args:
            main_window: Reference to the PowerSystemSimulator instance
        """
        self.main_window = main_window
    
    def delete_component(self, component):
        """
        Delete a component from the scene.
        
        Args:
            component: The component to delete
            
        Returns:
            bool: True if component was deleted, False otherwise
        """
        if not component:
            return False
            
        # Check if component is still in the scene
        if not component.scene():
            return False
        
        # Get component position for particle effect before removing it
        component_position = component.pos()
        component_width = 300  # Approximate width for most components
        component_height = 200  # Approximate height for most components
        center_x = component_position.x() + component_width / 2
        center_y = component_position.y() + component_height / 2
            
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
        
        # Create particle effect at the component's position after removal
        if not self.main_window.simulation_engine.simulation_running:
            self.main_window.particle_system.create_puff(center_x, center_y, num_particles=200)
        
        # Only remove from components list if it's a functional component (not a decorative one)
        # and if it's actually in the components list (to prevent the "x not in list" error)
        if (not isinstance(component, (TreeComponent, BushComponent, PondComponent, 
                       House1Component, House2Component, FactoryComponent, 
                       TraditionalDataCenterComponent, DistributionPoleComponent)) and 
            component in self.main_window.components):
            self.main_window.components.remove(component)
        
        # Clear the properties panel
        self.main_window.properties_dock.setVisible(False)
        
        # Clear the current component reference in the properties manager
        if hasattr(self.main_window.properties_manager, 'current_component'):
            self.main_window.properties_manager.current_component = None
        
        # Clear selection in the scene to prevent lingering references
        self.main_window.scene.clearSelection()
        
        # Clear the selected component display since no components are selected
        if hasattr(self.main_window, 'selected_component_display'):
            self.main_window.selected_component_display.update_selected_component(None)
        
        # Update simulation state
        self.main_window.update_simulation()
        
        # Update the CAPEX display
        self.main_window.update_capex_display()
        
        # Trigger red flash on the border when a component is deleted
        if hasattr(self.main_window, 'centralWidget') and self.main_window.centralWidget():
            central_widget = self.main_window.centralWidget()
            if hasattr(central_widget, 'trigger_gray_flash'):
                central_widget.trigger_gray_flash()
        
        # Log component deletion to terminal
        if hasattr(component, 'component_type') and hasattr(component, 'component_id'):
            component_type_name = component.component_type
            component_id_str = str(component.component_id)[-6:]
            TerminalWidget.log(f"Deleted {component_type_name} {component_id_str}")
        
        return True
    
    def delete_selected_components(self):
        """
        Delete all selected components in the scene.
        
        Returns:
            bool: True if any components were deleted, False otherwise
        """
        # Get selected items from the scene that have a connections attribute
        selected_items = [item for item in self.main_window.scene.selectedItems() if hasattr(item, 'connections')]
        
        deleted_any = False
        if selected_items:
            # Delete all selected components
            for component in selected_items.copy():  # Use a copy to avoid modifying during iteration
                if self.delete_component(component):
                    deleted_any = True
            return deleted_any
        
        # If no scene items are selected, check if properties manager has a current component
        elif hasattr(self.main_window.properties_manager, 'current_component') and self.main_window.properties_manager.current_component:
            # Only delete the component if it's still valid and in the scene
            component = self.main_window.properties_manager.current_component
            if component and component.scene() and component.isSelected():
                deleted_any = self.delete_component(component)
                return deleted_any
        
        return False 