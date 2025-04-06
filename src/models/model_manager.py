import json
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from PyQt5.QtCore import Qt, QPointF

from src.components.generator import GeneratorComponent
from src.components.load import LoadComponent
from src.components.bus import BusComponent
from src.components.connection import Connection
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

class ModelManager:
    """
    Manages saving and loading models for the power system simulator.
    Encapsulates file handling and component reconstruction logic.
    """
    
    def __init__(self, main_window):
        """
        Initialize the ModelManager.
        
        Args:
            main_window: Reference to the main application window to access scene and components
        """
        self.main_window = main_window
    
    def new_scenario(self):
        """Create a new blank scenario by clearing the scene and resetting all state"""
        # Clear the scene
        self.main_window.scene.clear()
        
        # Reset simulation
        self.main_window.simulation_engine.simulation_running = False
        self.main_window.play_btn.setText("Play (Space)")
        self.main_window.time_slider.setValue(0)
        
        # Reset cursor state and connection mode
        self.main_window.creating_connection = False
        self.main_window.cursor_timer.stop()
        self.main_window.view.setCursor(Qt.ArrowCursor)
        self.main_window.view.viewport().setCursor(Qt.ArrowCursor)
        self.main_window.connection_btn.setEnabled(True)
        self.main_window.sever_connection_btn.setEnabled(True)
        
        # Reset simulation components
        self.main_window.components = []
        self.main_window.connections = []
        self.main_window.simulation_engine.current_time_step = 0
        
        # Reset energy tracking
        self.main_window.simulation_engine.total_energy_imported = 0
        self.main_window.simulation_engine.total_energy_exported = 0
        self.main_window.simulation_engine.last_time_step = 0
        
        # Reset system stability
        self.main_window.simulation_engine.system_stable = True
        
        # Reset fractional step counter
        self.main_window.simulation_engine.fractional_step = 0
        
        self.main_window.update_simulation()
    
    def save_scenario(self):
        """Save the current scenario to a file"""
        filename, _ = QFileDialog.getSaveFileName(self.main_window, "Save Scenario", "", "JSON Files (*.json)")
        
        if not filename:
            return
            
        if not filename.endswith('.json'):
            filename += '.json'
            
        # Create data structure
        data = {
            "components": [],
            "connections": [],
            "decorations": []  # For non-functional decorative elements
        }
        
        # Create a component index map to ensure correct connection references
        component_index_map = {}
        index = 0
        
        # Save components and build index map
        for item in self.main_window.scene.items():
            if isinstance(item, GeneratorComponent):
                component_index_map[item] = index
                index += 1
                data["components"].append({
                    "type": "Generator",
                    "x": item.x(),
                    "y": item.y(),
                    "capacity": item.capacity,
                    "operating_mode": item.operating_mode,
                    "auto_charging": item.auto_charging
                })
            elif isinstance(item, LoadComponent):
                component_index_map[item] = index
                index += 1
                data["components"].append({
                    "type": "Load",
                    "x": item.x(),
                    "y": item.y(),
                    "demand": item.demand,
                    "profile_type": item.profile_type,
                    "graphics_enabled": item.graphics_enabled
                })
            elif isinstance(item, BusComponent):
                component_index_map[item] = index
                index += 1
                data["components"].append({
                    "type": "Bus",
                    "x": item.x(),
                    "y": item.y(),
                    "is_on": item.is_on
                })
            elif isinstance(item, GridImportComponent):
                component_index_map[item] = index
                index += 1
                data["components"].append({
                    "type": "GridImport",
                    "x": item.x(),
                    "y": item.y(),
                    "capacity": item.capacity
                })
            elif isinstance(item, GridExportComponent):
                component_index_map[item] = index
                index += 1
                data["components"].append({
                    "type": "GridExport",
                    "x": item.x(),
                    "y": item.y(),
                    "capacity": item.capacity
                })
            elif isinstance(item, BatteryComponent):
                component_index_map[item] = index
                index += 1
                data["components"].append({
                    "type": "Battery",
                    "x": item.x(),
                    "y": item.y(),
                    "power_capacity": item.power_capacity,
                    "energy_capacity": item.energy_capacity,
                    "current_charge": item.current_charge,
                    "operating_mode": item.operating_mode
                })
            elif isinstance(item, CloudWorkloadComponent):
                component_index_map[item] = index
                index += 1
                data["components"].append({
                    "type": "CloudWorkload",
                    "x": item.x(),
                    "y": item.y(),
                    "operating_mode": item.operating_mode,
                    "accumulated_revenue": item.accumulated_revenue
                })
            elif isinstance(item, SolarPanelComponent):
                component_index_map[item] = index
                index += 1
                data["components"].append({
                    "type": "SolarPanel",
                    "x": item.x(),
                    "y": item.y(),
                    "capacity": item.capacity,
                    "operating_mode": item.operating_mode
                })
            elif isinstance(item, WindTurbineComponent):
                component_index_map[item] = index
                index += 1
                data["components"].append({
                    "type": "WindTurbine",
                    "x": item.x(),
                    "y": item.y(),
                    "capacity": item.capacity,
                    "operating_mode": item.operating_mode
                })
            elif isinstance(item, (TreeComponent, BushComponent, PondComponent, House1Component, House2Component, FactoryComponent, TraditionalDataCenterComponent)):
                data["decorations"].append({
                    "type": item.__class__.__name__,
                    "x": item.x(),
                    "y": item.y()
                })
                
        # Save connections using the component index map
        for connection in self.main_window.connections:
            # Skip any connections where source or target is no longer in the scene
            if connection.source not in component_index_map or connection.target not in component_index_map:
                continue
                
            source_index = component_index_map[connection.source]
            target_index = component_index_map[connection.target]
            
            data["connections"].append({
                "source": source_index,
                "target": target_index
            })
            
        # Save to file
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
            
        QMessageBox.information(self.main_window, "Save Complete", "Scenario saved successfully.")

    def load_scenario(self):
        """Load a scenario from a file"""
        filename, _ = QFileDialog.getOpenFileName(self.main_window, "Load Scenario", "", "JSON Files (*.json)")
        
        if not filename:
            return
            
        # Clear existing scenario
        self.new_scenario()
        
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
                
            # Load components
            component_map = []  # Map saved indexes to new component objects
            
            # First pass: create all components in same order as saved
            for i, component_data in enumerate(data.get("components", [])):
                x = component_data["x"]
                y = component_data["y"]
                component_type = component_data["type"]
                
                if component_type == "Generator":
                    component = GeneratorComponent(x, y)
                    component.capacity = component_data.get("capacity", 100)
                    # Handle both new and old attribute names for backward compatibility
                    if "operating_mode" in component_data:
                        component.operating_mode = component_data["operating_mode"]
                    elif "mode" in component_data:
                        component.operating_mode = component_data["mode"]
                    else:
                        component.operating_mode = "BTF Droop (Auto)"  # Default value
                        
                    # Set auto_charging parameter if available, otherwise default to True
                    if "auto_charging" in component_data:
                        component.auto_charging = component_data["auto_charging"]
                    else:
                        component.auto_charging = True  # Default value
                        
                    self.main_window.scene.addItem(component)
                    self.main_window.components.append(component)
                    component_map.append(component)
                    
                elif component_type == "Load":
                    component = LoadComponent(x, y)
                    # Handle both new (demand) and old (capacity) attribute names
                    if "demand" in component_data:
                        component.demand = component_data["demand"]
                    elif "capacity" in component_data:
                        component.demand = component_data["capacity"]
                    else:
                        component.demand = 100  # Default value
                        
                    # Handle both new (profile_type) and old (profile) attribute names
                    if "profile_type" in component_data:
                        component.profile_type = component_data["profile_type"]
                    elif "profile" in component_data:
                        component.profile_type = component_data["profile"]
                    else:
                        component.profile_type = "Static"  # Default value
                        
                    if "graphics_enabled" in component_data:
                        component.graphics_enabled = component_data["graphics_enabled"]
                    self.main_window.scene.addItem(component)
                    self.main_window.components.append(component)
                    component_map.append(component)
                    
                elif component_type == "Bus":
                    component = BusComponent(x, y)
                    component.is_on = component_data.get("is_on", True)
                    self.main_window.scene.addItem(component)
                    self.main_window.components.append(component)
                    component_map.append(component)
                    
                elif component_type == "GridImport":
                    component = GridImportComponent(x, y)
                    component.capacity = component_data.get("capacity", 500)
                    # Load auto_charge_batteries with default True for backward compatibility
                    component.auto_charge_batteries = component_data.get("auto_charge_batteries", True)
                    self.main_window.scene.addItem(component)
                    self.main_window.components.append(component)
                    component_map.append(component)
                    
                elif component_type == "GridExport":
                    component = GridExportComponent(x, y)
                    component.capacity = component_data.get("capacity", 500)
                    self.main_window.scene.addItem(component)
                    self.main_window.components.append(component)
                    component_map.append(component)
                    
                elif component_type == "Battery":
                    component = BatteryComponent(x, y)
                    # Handle both new and old attribute names for backward compatibility
                    if "power_capacity" in component_data:
                        component.power_capacity = component_data["power_capacity"]
                    elif "capacity" in component_data:
                        component.power_capacity = component_data["capacity"]
                    else:
                        component.power_capacity = 500  # Default value
                    
                    if "energy_capacity" in component_data:
                        component.energy_capacity = component_data["energy_capacity"]
                    else:
                        component.energy_capacity = 2000  # Default value
                        
                    if "current_charge" in component_data:
                        component.current_charge = component_data["current_charge"]
                    elif "initial_charge" in component_data:
                        # Convert from percentage to absolute value if needed
                        initial_charge_pct = component_data["initial_charge"]
                        component.current_charge = (initial_charge_pct / 100) * component.energy_capacity
                    else:
                        component.current_charge = component.energy_capacity * 0.5  # Default 50% charge
                        
                    if "operating_mode" in component_data:
                        component.operating_mode = component_data["operating_mode"]
                    else:
                        component.operating_mode = "BTF Basic Unit (Auto)"  # Default mode
                        
                    self.main_window.scene.addItem(component)
                    self.main_window.components.append(component)
                    component_map.append(component)
                
                elif component_type == "CloudWorkload":
                    component = CloudWorkloadComponent(x, y)
                    component.operating_mode = component_data.get("operating_mode", "No Customer")
                    component.accumulated_revenue = component_data.get("accumulated_revenue", 0.0)
                    self.main_window.scene.addItem(component)
                    self.main_window.components.append(component)
                    component_map.append(component)
                    
                elif component_type == "SolarPanel":
                    component = SolarPanelComponent(x, y)
                    component.capacity = component_data.get("capacity", 500)
                    component.operating_mode = component_data.get("operating_mode", "Disabled")
                    # Load capacity factors if in active mode
                    if component.operating_mode == "Powerlandia 8760 - Midwest 1":
                        component.load_capacity_factors()
                    self.main_window.scene.addItem(component)
                    self.main_window.components.append(component)
                    component_map.append(component)
                
                elif component_type == "WindTurbine":
                    component = WindTurbineComponent(x, y)
                    component.capacity = component_data.get("capacity", 500)
                    component.operating_mode = component_data.get("operating_mode", "Disabled")
                    # Load capacity factors if in active mode
                    if component.operating_mode == "Powerlandia 8760 - Midwest 1":
                        component.load_capacity_factors()
                    self.main_window.scene.addItem(component)
                    self.main_window.components.append(component)
                    component_map.append(component)
                    
            # Load decorations (trees, bushes, etc.)
            for decoration_data in data.get("decorations", []):
                x = decoration_data["x"]
                y = decoration_data["y"]
                decoration_type = decoration_data["type"]
                
                if decoration_type == "TreeComponent":
                    component = TreeComponent(x, y)
                    self.main_window.scene.addItem(component)
                elif decoration_type == "BushComponent":
                    component = BushComponent(x, y)
                    self.main_window.scene.addItem(component)
                elif decoration_type == "PondComponent":
                    component = PondComponent(x, y)
                    self.main_window.scene.addItem(component)
                elif decoration_type == "House1Component":
                    component = House1Component(x, y)
                    self.main_window.scene.addItem(component)
                elif decoration_type == "House2Component":
                    component = House2Component(x, y)
                    self.main_window.scene.addItem(component)
                elif decoration_type == "FactoryComponent":
                    component = FactoryComponent(x, y)
                    self.main_window.scene.addItem(component)
                elif decoration_type == "TraditionalDataCenterComponent":
                    component = TraditionalDataCenterComponent(x, y)
                    self.main_window.scene.addItem(component)
                    
            # Second pass: restore connections using the exact same indices from the file
            for connection_data in data.get("connections", []):
                source_index = connection_data["source"]
                target_index = connection_data["target"]
                
                if 0 <= source_index < len(component_map) and 0 <= target_index < len(component_map):
                    source = component_map[source_index]
                    target = component_map[target_index]
                    
                    # Create the connection
                    connection = Connection(source, target)
                    self.main_window.connections.append(connection)
                    self.main_window.scene.addItem(connection)
                else:
                    print(f"Warning: Invalid connection indices {source_index} -> {target_index}")
                    
            QMessageBox.information(self.main_window, "Load Complete", "Scenario loaded successfully.")
            
            # Update scenario state
            self.main_window.validate_bus_states()  # Ensure buses without load connections are ON
            self.main_window.simulation_engine.time = 0
            self.main_window.time_slider.setValue(0)
            self.main_window.update_simulation()
            
        except Exception as e:
            QMessageBox.critical(self.main_window, "Error", f"Failed to load scenario: {str(e)}")
            # Start fresh if loading failed
            self.new_scenario() 