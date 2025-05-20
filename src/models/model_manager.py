import json
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from PyQt5.QtCore import Qt

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
from src.components.distribution_pole import DistributionPoleComponent

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
        # First, ensure we're in model view
        if hasattr(self.main_window, 'is_model_view') and not self.main_window.is_model_view:
            # We're in historian view, switch back to model view
            # Using toggle_mode_button instead of switch_to_model_view to ensure complete UI update
            self.main_window.mode_toggle_manager.toggle_mode_button()
        
        # Safely handle welcome text before clearing the scene
        if hasattr(self.main_window, 'welcome_text') and self.main_window.welcome_text:
            if self.main_window.welcome_text.scene():
                self.main_window.scene.removeItem(self.main_window.welcome_text)
            self.main_window.welcome_text = None
        
        # Clear the scene
        self.main_window.scene.clear()
        
        # Reset simulation
        self.main_window.simulation_engine.simulation_running = False
        self.main_window.time_slider.setValue(0)
        
        # Reset cursor state and connection mode
        self.main_window.creating_connection = False
        self.main_window.cursor_timer.stop()
        self.main_window.view.setCursor(Qt.ArrowCursor)
        self.main_window.view.viewport().setCursor(Qt.ArrowCursor)
        self.main_window.connection_btn.setEnabled(True)
        
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
        
        # Reset the view center position
        self.main_window.view.centerOn(0, 0)
        
        # Remove all individual component keys from the historian dictionary
        default_keys = [
            'total_generation', 'total_load', 'grid_import', 'grid_export',
            'cumulative_revenue', 'cumulative_cost', 'battery_charge', 'system_instability',
            'satisfied_load'
        ]
        
        # Identify keys to remove (non-default keys)
        keys_to_remove = []
        for key in self.main_window.simulation_engine.historian.keys():
            if key not in default_keys:
                keys_to_remove.append(key)
        
        # Remove non-default keys from the historian
        for key in keys_to_remove:
            del self.main_window.simulation_engine.historian[key]
        
        # Reset the historian data for default keys
        self.main_window.simulation_engine.reset_historian()
        
        # Reset the historian chart to remove component buttons
        if hasattr(self.main_window, 'historian_manager'):
            self.main_window.historian_manager.clear_chart()
        
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
                    "auto_charging": item.auto_charging,
                    "efficiency": item.efficiency,
                    "cost_per_gj": item.cost_per_gj,
                    "accumulated_cost": item.accumulated_cost,
                    "capex_per_kw": item.capex_per_kw,
                    "frequency_per_10000_hours": item.frequency_per_10000_hours,
                    "minimum_downtime": item.minimum_downtime,
                    "maximum_downtime": item.maximum_downtime,
                    "cooldown_time": item.cooldown_time
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
                    "graphics_enabled": item.graphics_enabled,
                    "capex_per_kw": item.capex_per_kw
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
                    "capacity": item.capacity,
                    "cost_per_kwh": item.cost_per_kwh,
                    "accumulated_cost": item.accumulated_cost,
                    "market_prices_mode": item.market_prices_mode,
                    "custom_profile": item.custom_profile,
                    "profile_name": item.profile_name
                })
            elif isinstance(item, GridExportComponent):
                component_index_map[item] = index
                index += 1
                data["components"].append({
                    "type": "GridExport",
                    "x": item.x(),
                    "y": item.y(),
                    "capacity": item.capacity,
                    "bulk_ppa_price": item.bulk_ppa_price,
                    "accumulated_revenue": item.accumulated_revenue,
                    "market_prices_mode": item.market_prices_mode,
                    "custom_profile": item.custom_profile,
                    "profile_name": item.profile_name
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
                    "operating_mode": item.operating_mode,
                    "capex_per_kw": item.capex_per_kw
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
                    "operating_mode": item.operating_mode,
                    "capex_per_kw": item.capex_per_kw
                })
            elif isinstance(item, WindTurbineComponent):
                component_index_map[item] = index
                index += 1
                data["components"].append({
                    "type": "WindTurbine",
                    "x": item.x(),
                    "y": item.y(),
                    "capacity": item.capacity,
                    "operating_mode": item.operating_mode,
                    "capex_per_kw": item.capex_per_kw
                })
            elif isinstance(item, (TreeComponent, BushComponent, PondComponent, House1Component, House2Component, FactoryComponent, TraditionalDataCenterComponent, DistributionPoleComponent)):
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
            
        self.load_scenario_from_file(filename)

    def load_scenario_from_file(self, filename):
        """Load a scenario from a specific file path without showing a dialog"""
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
                    
                    # Set efficiency parameter if available, otherwise default to 0.40 (40%)
                    if "efficiency" in component_data:
                        component.efficiency = component_data["efficiency"]
                    else:
                        component.efficiency = 0.40  # Default value
                        
                    # Set cost_per_gj parameter if available, otherwise default to 2.00
                    if "cost_per_gj" in component_data:
                        component.cost_per_gj = component_data["cost_per_gj"]
                    else:
                        component.cost_per_gj = 2.00  # Default value
                        
                    # Set accumulated_cost if available, otherwise default to 0.00
                    if "accumulated_cost" in component_data:
                        component.accumulated_cost = component_data["accumulated_cost"]
                    else:
                        component.accumulated_cost = 0.00
                    
                    # Set capex_per_kw if available, otherwise keep default value
                    if "capex_per_kw" in component_data:
                        component.capex_per_kw = component_data["capex_per_kw"]
                    
                    # Set maintenance parameters if available
                    if "frequency_per_10000_hours" in component_data:
                        component.frequency_per_10000_hours = component_data["frequency_per_10000_hours"]
                    if "minimum_downtime" in component_data:
                        component.minimum_downtime = component_data["minimum_downtime"]
                    if "maximum_downtime" in component_data:
                        component.maximum_downtime = component_data["maximum_downtime"]
                    if "cooldown_time" in component_data:
                        component.cooldown_time = component_data["cooldown_time"]
                    
                    self.main_window.scene.addItem(component)
                    self.main_window.components.append(component)
                    component_map.append(component)
                    
                elif component_type == "Load":
                    component = LoadComponent(x, y)
                    component.demand = component_data.get("demand", 500)
                    # Handle both new (profile_type) and old (profile) attribute names
                    if "profile_type" in component_data:
                        component.profile_type = component_data["profile_type"]
                    elif "profile" in component_data:
                        component.profile_type = component_data["profile"]
                    else:
                        component.profile_type = "Static"  # Default value
                        
                    if "graphics_enabled" in component_data:
                        component.graphics_enabled = component_data["graphics_enabled"]
                    
                    # Set capex_per_kw if available, otherwise keep default value
                    if "capex_per_kw" in component_data:
                        component.capex_per_kw = component_data["capex_per_kw"]
                    
                    # Handle Powerlandia profile if needed
                    if component.profile_type == "Powerlandia 60CF":
                        component.load_powerlandia_profile()
                        
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
                    component.cost_per_kwh = component_data.get("cost_per_kwh", 0.0)
                    component.accumulated_cost = component_data.get("accumulated_cost", 0.0)
                    component.market_prices_mode = component_data.get("market_prices_mode", "None")
                    component.custom_profile = component_data.get("custom_profile", None)
                    component.profile_name = component_data.get("profile_name", "")
                    self.main_window.scene.addItem(component)
                    self.main_window.components.append(component)
                    component_map.append(component)
                    
                elif component_type == "GridExport":
                    component = GridExportComponent(x, y)
                    component.capacity = component_data.get("capacity", 500)
                    component.bulk_ppa_price = component_data.get("bulk_ppa_price", 0.0)
                    component.accumulated_revenue = component_data.get("accumulated_revenue", 0.0)
                    component.market_prices_mode = component_data.get("market_prices_mode", "None")
                    component.custom_profile = component_data.get("custom_profile", None)
                    component.profile_name = component_data.get("profile_name", "")
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
                     
                    # Set capex_per_kw if available, otherwise keep default value
                    if "capex_per_kw" in component_data:
                        component.capex_per_kw = component_data["capex_per_kw"]
                        
                    self.main_window.scene.addItem(component)
                    self.main_window.components.append(component)
                    component_map.append(component)
                
                elif component_type == "CloudWorkload":
                    component = CloudWorkloadComponent(x, y)
                    component.operating_mode = component_data.get("operating_mode", "No Customer")
                    component.accumulated_revenue = component_data.get("accumulated_revenue", 0.0)
                    # Load dedicated capacity parameters if they exist
                    if "dedicated_power_per_resource" in component_data:
                        component.dedicated_power_per_resource = component_data.get("dedicated_power_per_resource", 1.20)
                    if "dedicated_power_use_efficiency" in component_data:
                        component.dedicated_power_use_efficiency = component_data.get("dedicated_power_use_efficiency", 1.15)
                    if "dedicated_price_per_resource" in component_data:
                        component.dedicated_price_per_resource = component_data.get("dedicated_price_per_resource", 3.25)
                    self.main_window.scene.addItem(component)
                    self.main_window.components.append(component)
                    component_map.append(component)
                    
                elif component_type == "SolarPanel":
                    component = SolarPanelComponent(x, y)
                    component.capacity = component_data.get("capacity", 500)
                    component.operating_mode = component_data.get("operating_mode", "Disabled")
                    
                    # Set capex_per_kw if available, otherwise keep default value
                    if "capex_per_kw" in component_data:
                        component.capex_per_kw = component_data["capex_per_kw"]
                    
                    # Load custom profile data if available
                    if "custom_profile" in component_data and "profile_name" in component_data:
                        component.custom_profile = component_data["custom_profile"]
                        component.profile_name = component_data["profile_name"]
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
                    
                    # Set capex_per_kw if available, otherwise keep default value
                    if "capex_per_kw" in component_data:
                        component.capex_per_kw = component_data["capex_per_kw"]
                    
                    # Load custom profile data if available
                    if "custom_profile" in component_data and "profile_name" in component_data:
                        component.custom_profile = component_data["custom_profile"]
                        component.profile_name = component_data["profile_name"]
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
                elif decoration_type == "DistributionPoleComponent":
                    component = DistributionPoleComponent(x, y)
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
            
            # Update scenario state
            self.main_window.validate_bus_states()  # Ensure buses without load connections are ON
            self.main_window.simulation_engine.time = 0
            self.main_window.time_slider.setValue(0)
            self.main_window.update_simulation()
            
            # Reset the simulation state to ensure consistent initial conditions
            if hasattr(self.main_window, 'simulation_controller'):
                self.main_window.simulation_controller.reset_simulation(skip_flash=False)
            
        except Exception as e:
            QMessageBox.critical(self.main_window, "Error", f"Failed to load scenario: {str(e)}")
            # Start fresh if loading failed
            self.new_scenario() 