from PyQt5.QtWidgets import (QLineEdit, QLabel, QPushButton, QComboBox, QHBoxLayout, QWidget)
from PyQt5.QtCore import Qt

# Import styles from the parent module
from src.ui.properties_manager import COMMON_BUTTON_STYLE, INPUT_STYLE, DEFAULT_BUTTON_STYLE, COMBOBOX_STYLE

def add_grid_import_properties(properties_manager, component, layout):
    capacity_edit = QLineEdit(str(component.capacity / 1000))
    capacity_edit.setStyleSheet(INPUT_STYLE)
    properties_manager._set_up_numeric_field(capacity_edit, lambda value: setattr(component, 'capacity', value * 1000), min_value=0.025, max_value=5000)
    
    # Add cost per kWh field
    cost_edit = QLineEdit(str(component.cost_per_kwh))
    cost_edit.setStyleSheet(INPUT_STYLE)
    properties_manager._set_up_numeric_field(cost_edit, lambda value: setattr(component, 'cost_per_kwh', value), min_value=0.00)
    
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
    
    # Add auto-charging toggle button
    auto_charging_btn = QPushButton("ON" if component.auto_charge_batteries else "OFF")
    auto_charging_btn.setStyleSheet(
        COMMON_BUTTON_STYLE + """
        QPushButton { 
            background-color: #185D18; 
            color: white; 
            font-weight: bold; 
            font-size: 14px; 
        }
        QPushButton:hover { 
            background-color: #227D22; 
        }
        QPushButton:pressed { 
            background-color: #103D10; 
        }
    """ if component.auto_charge_batteries 
        else COMMON_BUTTON_STYLE + """
        QPushButton { 
            background-color: #5D1818; 
            color: white; 
            font-weight: bold; 
            font-size: 14px; 
        }
        QPushButton:hover { 
            background-color: #7D2222; 
        }
        QPushButton:pressed { 
            background-color: #3D1010; 
        }
    """)
    
    def toggle_auto_charging():
        component.auto_charge_batteries = not component.auto_charge_batteries
        auto_charging_btn.setText("ON" if component.auto_charge_batteries else "OFF")
        auto_charging_btn.setStyleSheet(
        COMMON_BUTTON_STYLE + """
        QPushButton { 
            background-color: #185D18; 
            color: white; 
            font-weight: bold; 
            font-size: 14px; 
        }
        QPushButton:hover { 
            background-color: #227D22; 
        }
        QPushButton:pressed { 
            background-color: #103D10; 
        }
    """ if component.auto_charge_batteries 
        else COMMON_BUTTON_STYLE + """
        QPushButton { 
            background-color: #5D1818; 
            color: white; 
            font-weight: bold; 
            font-size: 14px; 
        }
        QPushButton:hover { 
            background-color: #7D2222; 
        }
        QPushButton:pressed { 
            background-color: #3D1010; 
        }
    """)
        component.update()
        properties_manager.main_window.update_simulation()
    
    auto_charging_btn.clicked.connect(toggle_auto_charging)
    
    layout.addRow("Operating Mode:", QLabel("Last Resort Unit (Auto)"))
    layout.addRow("Capacity (MW):", capacity_edit)
    layout.addRow("Bulk PPA ($/kWh):", cost_edit)
    layout.addRow("Wholesale Prices:", market_prices_selector)
    layout.addRow("CSV File:", load_profile_btn)
    layout.addRow("", profile_info)
    layout.addRow("Auto-Charging:", auto_charging_btn) 