from PyQt5.QtWidgets import (QLineEdit, QLabel, QComboBox)
from PyQt5.QtCore import Qt

# Import styles from the parent module
from src.ui.properties_manager import COMMON_BUTTON_STYLE, INPUT_STYLE, COMBOBOX_STYLE

def add_battery_properties(properties_manager, component, layout):
    # Power capacity field in MW
    power_capacity_edit = QLineEdit(str(component.power_capacity / 1000))
    power_capacity_edit.setStyleSheet(INPUT_STYLE)
    
    def update_power_capacity(value):
        # Convert back to kW for internal storage
        kw_value = value * 1000
        setattr(component, 'power_capacity', kw_value)
        # Update CAPEX display when power capacity changes
        properties_manager.main_window.update_capex_display()
        
    properties_manager._set_up_numeric_field(power_capacity_edit, update_power_capacity, min_value=0.025, max_value=5000)
    
    # Energy capacity field
    energy_capacity_edit = QLineEdit(str(component.energy_capacity))
    energy_capacity_edit.setStyleSheet(INPUT_STYLE)
    
    def update_energy_capacity(value):
        # Skip if already updating to prevent recursive updates
        if properties_manager.main_window.simulation_engine.updating_simulation:
            return
            
        # Set the new energy capacity
        component.energy_capacity = value
        
        # Cap current charge at the new energy capacity if needed
        if component.current_charge > component.energy_capacity:
            component.current_charge = component.energy_capacity
            
        component.update()
        properties_manager.main_window.update_simulation()
    
    properties_manager._set_up_numeric_field(energy_capacity_edit, update_energy_capacity, min_value=25, max_value=5000000)
    
    # Operating mode selector
    mode_selector = QComboBox()
    mode_selector.setStyleSheet(COMBOBOX_STYLE)
    mode_selector.addItems(["Off", "BTF Basic Unit (Auto)"])
    mode_selector.setCurrentText(component.operating_mode)
    
    # Connect operating mode change
    def change_mode(text):
        component.operating_mode = text
        component.update()
        properties_manager.main_window.update_simulation()
    
    mode_selector.currentTextChanged.connect(change_mode)
    
    # Display charge percentage as read-only label
    if component.energy_capacity > 0:
        charge_percent = int((component.current_charge / component.energy_capacity) * 100)
    else:
        charge_percent = 0
        
    charge_label = QLabel(f"{charge_percent}%")
    charge_label.setStyleSheet("color: white; font-weight: bold;")
    
    # Add CAPEX per kW field
    capex_edit = QLineEdit(str(component.capex_per_kw))
    capex_edit.setStyleSheet(INPUT_STYLE)
    
    def update_capex(value):
        setattr(component, 'capex_per_kw', value)
        # Update CAPEX display when CAPEX per kW changes
        properties_manager.main_window.update_capex_display()
        
    properties_manager._set_up_numeric_field(capex_edit, update_capex, min_value=0.00, max_value=100000)
    
    # Add controls to layout
    layout.addRow("Power Capacity (MW):", power_capacity_edit)
    layout.addRow("Energy Capacity (kWh):", energy_capacity_edit)
    layout.addRow("Charge Level:", charge_label)
    layout.addRow("Operating Mode:", mode_selector)
    layout.addRow("CAPEX per kW ($):", capex_edit) 