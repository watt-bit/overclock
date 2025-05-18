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
    
    # Create market prices selector with dropdown
    market_prices_layout = QHBoxLayout()
    market_prices_layout.setContentsMargins(0, 0, 0, 0)
    market_prices_selector = QComboBox()
    market_prices_selector.setStyleSheet(COMBOBOX_STYLE)
    market_prices_selector.addItems(["None", "Powerlandia 8760 Wholesale - Year 1", "Custom"])
    market_prices_selector.setCurrentText(component.market_prices_mode)
    market_prices_selector.setMinimumWidth(250)
    market_prices_layout.addWidget(market_prices_selector)
    
    # Add load profile button (only visible for Custom type)
    load_profile_btn = QPushButton("Load Profile")
    load_profile_btn.setStyleSheet(DEFAULT_BUTTON_STYLE)
    load_profile_btn.setVisible(component.market_prices_mode == "Custom")
    load_profile_btn.clicked.connect(lambda: properties_manager._load_custom_profile(component))
    market_prices_layout.addWidget(load_profile_btn)
    
    # Create a widget to hold the market prices layout
    market_prices_widget = QWidget()
    market_prices_widget.setLayout(market_prices_layout)
    market_prices_widget.setFixedWidth(275)
    
    # Add profile info label
    profile_info = QLabel()
    if component.market_prices_mode == "Custom" and component.profile_name:
        profile_info.setText(f"Loaded: {component.profile_name}")
    else:
        profile_info.setText("")
    
    def on_market_prices_mode_changed(text):
        component.market_prices_mode = text
        # If switching to Powerlandia mode, load market prices
        if text == "Powerlandia 8760 Wholesale - Year 1":
            component.load_market_prices()
        # Show/hide load profile button based on mode
        load_profile_btn.setVisible(text == "Custom")
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
        COMMON_BUTTON_STYLE + "QPushButton { background-color: #4CAF50; color: white; }" if component.auto_charge_batteries 
        else COMMON_BUTTON_STYLE + "QPushButton { background-color: #f44336; color: white; }"
    )
    
    def toggle_auto_charging():
        component.auto_charge_batteries = not component.auto_charge_batteries
        auto_charging_btn.setText("ON" if component.auto_charge_batteries else "OFF")
        auto_charging_btn.setStyleSheet(
            COMMON_BUTTON_STYLE + "QPushButton { background-color: #4CAF50; color: white; }" if component.auto_charge_batteries 
            else COMMON_BUTTON_STYLE + "QPushButton { background-color: #f44336; color: white; }"
        )
        component.update()
        properties_manager.main_window.update_simulation()
    
    auto_charging_btn.clicked.connect(toggle_auto_charging)
    
    layout.addRow("Max Capacity (MW):", capacity_edit)
    layout.addRow("Bulk Import PPA ($/kWh):", cost_edit)
    layout.addRow("Market Import Prices ($/kWh):", market_prices_widget)
    layout.addRow("", profile_info)
    layout.addRow("Operating Mode:", QLabel("Last Resort Unit (Auto)"))
    layout.addRow("Auto-Charge Batteries:", auto_charging_btn) 