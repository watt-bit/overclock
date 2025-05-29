from PyQt5.QtWidgets import (QLineEdit, QLabel, QPushButton, QComboBox, QHBoxLayout, QWidget)
from PyQt5.QtCore import Qt
import csv

# Import styles from the parent module
from src.ui.properties_manager import COMMON_BUTTON_STYLE, DEFAULT_BUTTON_STYLE, COMBOBOX_STYLE, INPUT_STYLE

def add_wind_turbine_properties(properties_manager, component, layout):
    """Add properties for WindTurbineComponent"""
    # Add operating mode selector (no button on same line)
    mode_selector = QComboBox()
    mode_selector.setStyleSheet(COMBOBOX_STYLE)
    mode_selector.addItems(["Disabled", "Powerlandia 8760-1", "Custom"])
    mode_selector.setCurrentText(component.operating_mode)
    mode_selector.setMinimumWidth(150)
    
    # Create load profile button (always visible, on separate line)
    load_profile_btn = QPushButton("Load")
    load_profile_btn.setStyleSheet(DEFAULT_BUTTON_STYLE + ("" if component.operating_mode == "Custom" else " QPushButton:disabled { color: #888888; }"))
    load_profile_btn.setEnabled(component.operating_mode == "Custom")
    load_profile_btn.clicked.connect(lambda: properties_manager._load_custom_profile(component))
    
    # Add profile info label
    profile_info = QLabel()
    if component.operating_mode == "Custom" and component.profile_name:
        profile_info.setText(f"Loaded: {component.profile_name}")
    else:
        profile_info.setText("")
    
    def on_mode_changed(text):
        component.operating_mode = text
        # If switching to Powerlandia mode, load capacity factors
        if text == "Powerlandia 8760-1":
            component.load_capacity_factors()
        # Enable/disable load profile button based on mode and update styling
        is_enabled = text == "Custom"
        load_profile_btn.setEnabled(is_enabled)
        if is_enabled:
            load_profile_btn.setStyleSheet(DEFAULT_BUTTON_STYLE)
        else:
            load_profile_btn.setStyleSheet(DEFAULT_BUTTON_STYLE + " QPushButton:disabled { color: #888888; }")
        # Update profile info text
        if text == "Custom" and component.profile_name:
            profile_info.setText(f"Loaded: {component.profile_name}")
        else:
            profile_info.setText("")
        component.update()  # Refresh the component display
        properties_manager.main_window.update_simulation()  # Update simulation to reflect the change
    
    mode_selector.currentTextChanged.connect(on_mode_changed)
    layout.addRow("Operating Mode:", mode_selector)
    layout.addRow("CSV File:", load_profile_btn)
    layout.addRow("", profile_info)
    
    # Add capacity field
    capacity_field = QLineEdit(str(component.capacity / 1000))
    capacity_field.setStyleSheet(INPUT_STYLE)
    
    def update_capacity(value):
        try:
            component.capacity = float(value) * 1000  # Convert MW to kW
            component.update()  # Refresh the component display
            properties_manager.main_window.update_simulation()
            # Update CAPEX display when capacity changes
            properties_manager.main_window.update_capex_display()
        except (ValueError, TypeError):
            # Restore previous value if input is invalid
            capacity_field.setText(str(component.capacity / 1000))
    
    # Set up numeric validation for the capacity field
    properties_manager._set_up_numeric_field(capacity_field, update_capacity, is_float=True, min_value=0.025, max_value=5000)
    
    # Add CAPEX per kW field
    capex_edit = QLineEdit(str(component.capex_per_kw))
    capex_edit.setStyleSheet(INPUT_STYLE)
    
    def update_capex(value):
        setattr(component, 'capex_per_kw', value)
        # Update CAPEX display when CAPEX per kW changes
        properties_manager.main_window.update_capex_display()
        
    properties_manager._set_up_numeric_field(capex_edit, update_capex, min_value=0.00, max_value=100000)
    
    layout.addRow("Capacity (MW):", capacity_field)
    layout.addRow("CAPEX per kW ($):", capex_edit) 