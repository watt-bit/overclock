from PyQt5.QtWidgets import (QComboBox, QHBoxLayout, QPushButton, QWidget, QLabel, QLineEdit)

# Import styles from the parent module
from src.ui.properties_manager import COMBOBOX_STYLE, DEFAULT_BUTTON_STYLE, INPUT_STYLE

def add_solar_panel_properties(properties_manager, component, layout):
    """Add properties for SolarPanelComponent"""
    # Add operating mode selector
    mode_selector = QComboBox()
    mode_selector.setStyleSheet(COMBOBOX_STYLE)
    mode_selector.addItems(["Disabled", "Powerlandia 8760 - Midwest 1", "Custom"])
    mode_selector.setCurrentText(component.operating_mode)
    mode_selector.setMinimumWidth(250)
    
    # Create a horizontal layout for profile selection and load button
    profile_layout = QHBoxLayout()
    profile_layout.setContentsMargins(0, 0, 0, 0)
    profile_layout.addWidget(mode_selector)
    
    # Add load profile button (only visible for Custom type)
    load_profile_btn = QPushButton("Load Profile")
    load_profile_btn.setStyleSheet(DEFAULT_BUTTON_STYLE)
    load_profile_btn.setVisible(component.operating_mode == "Custom")
    load_profile_btn.clicked.connect(lambda: properties_manager._load_custom_profile(component))
    profile_layout.addWidget(load_profile_btn)
    
    # Create a widget to hold the profile layout
    profile_widget = QWidget()
    profile_widget.setLayout(profile_layout)
    
    # Add profile info label
    profile_info = QLabel()
    if component.operating_mode == "Custom" and component.profile_name:
        profile_info.setText(f"Loaded: {component.profile_name}")
    else:
        profile_info.setText("")
    
    def on_mode_changed(text):
        component.operating_mode = text
        # If switching to Powerlandia mode, load capacity factors
        if text == "Powerlandia 8760 - Midwest 1":
            component.load_capacity_factors()
        # Show/hide load profile button based on mode
        load_profile_btn.setVisible(text == "Custom")
        # Update profile info text
        if text == "Custom" and component.profile_name:
            profile_info.setText(f"Loaded: {component.profile_name}")
        else:
            profile_info.setText("")
        component.update()  # Refresh the component display
        properties_manager.main_window.update_simulation()  # Update simulation to reflect the change
    
    mode_selector.currentTextChanged.connect(on_mode_changed)
    layout.addRow("Operating Mode:", profile_widget)
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