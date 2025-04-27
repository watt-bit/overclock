from src.components.tree import TreeComponent
from src.components.bush import BushComponent
from src.components.pond import PondComponent
from src.components.house1 import House1Component
from src.components.house2 import House2Component
from src.components.factory import FactoryComponent
from src.components.traditional_data_center import TraditionalDataCenterComponent
from src.components.distribution_pole import DistributionPoleComponent


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
        
        # Only remove from components list if it's a functional component (not a decorative one)
        # and if it's actually in the components list (to prevent the "x not in list" error)
        if (not isinstance(component, (TreeComponent, BushComponent, PondComponent, 
                       House1Component, House2Component, FactoryComponent, 
                       TraditionalDataCenterComponent, DistributionPoleComponent)) and 
            component in self.main_window.components):
            self.main_window.components.remove(component)
        
        # Clear the properties panel
        self.main_window.properties_dock.setVisible(False)
        
        # Update simulation state
        self.main_window.update_simulation()
        
        # Update the CAPEX display
        self.main_window.update_capex_display()
        
        return True
    
    def delete_selected_components(self):
        """
        Delete all selected components in the scene.
        
        Returns:
            bool: True if any components were deleted, False otherwise
        """
        # Get selected items from the scene that have a connections attribute
        selected_items = [item for item in self.main_window.scene.selectedItems() if hasattr(item, 'connections')]
        
        if selected_items:
            # Delete all selected components
            for component in selected_items:
                self.delete_component(component)
            return True
        
        # If no scene items are selected, check if properties manager has a current component
        elif hasattr(self.main_window.properties_manager, 'current_component') and self.main_window.properties_manager.current_component:
            # Only delete the component if it's still selected in the scene
            if self.main_window.properties_manager.current_component.isSelected():
                self.delete_component(self.main_window.properties_manager.current_component)
                return True
        
        return False 