from PyQt6.QtWidgets import (QLineEdit, QLabel, QPushButton, QHBoxLayout, QWidget, QComboBox)
from PyQt6.QtCore import Qt

# Import styles from the parent module
from src.ui.properties_manager import COMMON_BUTTON_STYLE, INPUT_STYLE, DEFAULT_BUTTON_STYLE, COMBOBOX_STYLE

def add_grid_export_properties(properties_manager, component, layout):
    capacity_edit = QLineEdit(str(component.capacity / 1000))
    capacity_edit.setStyleSheet(INPUT_STYLE)
    properties_manager._set_up_numeric_field(capacity_edit, lambda value: setattr(component, 'capacity', value * 1000), min_value=0.025, max_value=5000)
    
    # Add price per kWh field
    price_edit = QLineEdit(str(component.bulk_ppa_price))
    price_edit.setStyleSheet(INPUT_STYLE)
    properties_manager._set_up_numeric_field(price_edit, lambda value: setattr(component, 'bulk_ppa_price', value), min_value=0.00)
    
    # Create market prices selector dropdown (no button on same line)
    market_prices_selector = QComboBox()
    market_prices_selector.setStyleSheet(COMBOBOX_STYLE)
    market_prices_selector.addItems(["None", "Powerlandia 8760-1", "Custom"])
    market_prices_selector.setCurrentText(component.market_prices_mode)
    market_prices_selector.setMinimumWidth(150)
    
    # Create load profile button (always visible, on separate line)
    load_profile_btn = QPushButton("Load")
    load_profile_btn.setStyleSheet(DEFAULT_BUTTON_STYLE + ("" if component.market_prices_mode == "Custom" else " QPushButton:disabled { color: #888888; }"))
    load_profile_btn.setEnabled(component.market_prices_mode == "Custom")
    load_profile_btn.clicked.connect(lambda: properties_manager._load_custom_profile(component))
    
    # Add profile info label
    profile_info = QLabel()
    if component.market_prices_mode == "Custom" and component.profile_name:
        profile_info.setText(f"Loaded: {component.profile_name}")
    else:
        profile_info.setText("")
    
    def on_market_prices_mode_changed(text):
        component.market_prices_mode = text
        # If switching to Powerlandia mode, load market prices
        if text == "Powerlandia 8760-1":
            component.load_market_prices()
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
    
    market_prices_selector.currentTextChanged.connect(on_market_prices_mode_changed)
    
    layout.addRow("Operating Mode:", QLabel("Last Resort Unit (Auto)")) 
    layout.addRow("Max Capacity (MW):", capacity_edit)
    layout.addRow("Bulk PPA ($/kWh):", price_edit)
    layout.addRow("Wholesale Prices:", market_prices_selector)
    layout.addRow("CSV File:", load_profile_btn)
    layout.addRow("", profile_info)