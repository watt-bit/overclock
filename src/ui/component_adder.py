from src.components.generator import GeneratorComponent
from src.components.load import LoadComponent
from src.components.bus import BusComponent
from src.components.grid_import import GridImportComponent
from src.components.grid_export import GridExportComponent
from src.components.battery import BatteryComponent
from src.components.tree import TreeComponent
from src.components.bush import BushComponent
from src.components.pond import PondComponent
from src.components.house1 import House1Component
from src.components.house2 import House2Component
from src.components.factory import FactoryComponent
from src.components.traditional_data_center import TraditionalDataCenterComponent
from src.components.cloud_workload import CloudWorkloadComponent
from src.components.solar_panel import SolarPanelComponent
from src.components.wind_turbine import WindTurbineComponent
from src.components.distribution_pole import DistributionPoleComponent
import sip

class ComponentAdder:
    def __init__(self, main_window):
        """Initialize with reference to the main window to access scene, components list, etc."""
        self.main_window = main_window
    
    def add_component(self, component_type):
        """Create and add a component of the specified type to the scene"""
        position = None  # Store position for particle effect
        
        if component_type == "generator":
            component = GeneratorComponent(0, 0)
            self.main_window.scene.addItem(component)
            self.main_window.components.append(component)
            position = component.pos()
        elif component_type == "grid_import":
            component = GridImportComponent(0, 0)
            self.main_window.scene.addItem(component)
            self.main_window.components.append(component)
            position = component.pos()
        elif component_type == "grid_export":
            component = GridExportComponent(0, 0)
            self.main_window.scene.addItem(component)
            self.main_window.components.append(component)
            position = component.pos()
        elif component_type == "bus":
            component = BusComponent(0, 0)
            self.main_window.scene.addItem(component)
            self.main_window.components.append(component)
            position = component.pos()
        elif component_type == "load":
            component = LoadComponent(0, 0)
            self.main_window.scene.addItem(component)
            self.main_window.components.append(component)
            position = component.pos()
        elif component_type == "battery":
            component = BatteryComponent(0, 0)
            self.main_window.scene.addItem(component)
            self.main_window.components.append(component)
            position = component.pos()
        elif component_type == "cloud_workload":
            component = CloudWorkloadComponent(0, 0)
            self.main_window.scene.addItem(component)
            self.main_window.components.append(component)
            position = component.pos()
        elif component_type == "solar_panel":
            component = SolarPanelComponent(0, 0)
            self.main_window.scene.addItem(component)
            self.main_window.components.append(component)
            position = component.pos()
        elif component_type == "wind_turbine":
            component = WindTurbineComponent(0, 0)
            self.main_window.scene.addItem(component)
            self.main_window.components.append(component)
            position = component.pos()
        elif component_type == "tree":
            component = TreeComponent(0, 0)
            self.main_window.scene.addItem(component)
            position = component.pos()
            # Do not add trees to the components list as they are decorative
            # and should not affect network connectivity checks
        elif component_type == "bush":
            component = BushComponent(0, 0)
            self.main_window.scene.addItem(component)
            position = component.pos()
            # Do not add bushes to the components list as they are decorative
            # and should not affect network connectivity checks
        elif component_type == "pond":
            component = PondComponent(0, 0)
            self.main_window.scene.addItem(component)
            position = component.pos()
            # Do not add ponds to the components list as they are decorative
            # and should not affect network connectivity checks
        elif component_type == "house1":
            component = House1Component(0, 0)
            self.main_window.scene.addItem(component)
            position = component.pos()
            # Do not add houses to the components list as they are decorative
            # and should not affect network connectivity checks
        elif component_type == "house2":
            component = House2Component(0, 0)
            self.main_window.scene.addItem(component)
            position = component.pos()
            # Do not add houses to the components list as they are decorative
            # and should not affect network connectivity checks
        elif component_type == "factory":
            component = FactoryComponent(0, 0)
            self.main_window.scene.addItem(component)
            position = component.pos()
            # Do not add factories to the components list as they are decorative
        elif component_type == "traditional_data_center":
            component = TraditionalDataCenterComponent(0, 0)
            self.main_window.scene.addItem(component)
            position = component.pos()
            # Do not add traditional data centers to the components list as they are decorative
        elif component_type == "distribution_pole":
            component = DistributionPoleComponent(0, 0)
            self.main_window.scene.addItem(component)
            position = component.pos()
            # Do not add distribution poles to the components list as they are decorative
        
        # Hide welcome text after adding the first component (if it's not decorative)
        if component_type in ["generator", "grid_import", "grid_export", "bus", "load", "battery", "cloud_workload", "solar_panel", "wind_turbine"]:
            if hasattr(self.main_window, 'welcome_text') and self.main_window.welcome_text and not sip.isdeleted(self.main_window.welcome_text) and self.main_window.welcome_text.isVisible():
                self.main_window.welcome_text.setVisible(False)
        
        # Create particle effect at the component's position
        if position is not None and not self.main_window.simulation_engine.simulation_running:
            # Get the center of the component
            component_width = 300  # Approximate width for most components
            component_height = 200  # Approximate height for most components
            center_x = position.x() + component_width / 2
            center_y = position.y() + component_height / 2
            
            # Create particle effect
            self.main_window.particle_system.create_puff(center_x, center_y, num_particles=200) 