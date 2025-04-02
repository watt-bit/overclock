from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QSlider, QFileDialog, QFormLayout, 
                            QLineEdit, QComboBox, QMessageBox, QSizePolicy)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDoubleValidator, QIntValidator
import csv
import re

from src.components.base import ComponentBase
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
from src.components.cloud_workload import CloudWorkloadComponent
from src.components.solar_panel import SolarPanelComponent

# Define common styles
COMMON_BUTTON_STYLE = "QPushButton { border: 1px solid #555555; border-radius: 3px; padding: 5px; }"
DEFAULT_BUTTON_STYLE = "QPushButton { background-color: #3D3D3D; color: white; border: 1px solid #555555; border-radius: 3px; padding: 5px; }"
SLIDER_STYLE = "QSlider::groove:horizontal { background: #3D3D3D; height: 8px; border-radius: 4px; } " \
              "QSlider::handle:horizontal { background: #5D5D5D; width: 16px; margin: -4px 0; border-radius: 8px; }"
COMBOBOX_STYLE = "QComboBox { background-color: #3D3D3D; color: white; border: 1px solid #555555; border-radius: 3px; padding: 5px; }"
INPUT_STYLE = "QLineEdit { background-color: #3D3D3D; color: white; border: 1px solid #555555; border-radius: 3px; padding: 5px; }"
LINEEDIT_STYLE = "QLineEdit { background-color: #3D3D3D; color: white; border: 1px solid #555555; border-radius: 3px; padding: 5px; }"

class ComponentPropertiesManager:
    def __init__(self, main_window):
        self.main_window = main_window
        self.properties_widget = QWidget()
        # Set size policies to allow the widget to shrink to its minimum size
        self.properties_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.properties_layout = QFormLayout(self.properties_widget)
        # Set layout margins to be minimal
        self.properties_layout.setContentsMargins(10, 10, 10, 10)
        # Set left alignment for all labels in the form
        self.properties_layout.setLabelAlignment(Qt.AlignLeft)
        self.properties_layout.setFormAlignment(Qt.AlignLeft | Qt.AlignTop)
    
    def clear_properties_panel(self):
        """Clear all widgets from the properties panel"""
        while self.properties_layout.count():
            item = self.properties_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                # Clear sub-layouts
                while item.layout().count():
                    sub_item = item.layout().takeAt(0)
                    if sub_item.widget():
                        sub_item.widget().deleteLater()
                item.layout().deleteLater()
        
        # Force the properties dock to resize to its minimum size
        self.properties_widget.adjustSize()
        self.main_window.properties_dock.adjustSize()
    
    def show_component_properties(self, component):
        """Display the properties for the selected component"""
        # Only show properties if not in connection mode
        if self.main_window.creating_connection:
            return
            
        # Make properties panel visible if it's currently hidden
        if not self.main_window.properties_dock.isVisible():
            self.main_window.properties_dock.setVisible(True)
            self.main_window.position_properties_panel_if_needed()
            
        # Clear existing properties
        while self.properties_layout.count():
            item = self.properties_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.current_component = component
        
        # Create a layout for the component properties
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(5, 5, 5, 5)  # Reduce margins
        left_column = QFormLayout()
        left_column.setContentsMargins(0, 0, 0, 0)  # Minimal margins
        left_column.setLabelAlignment(Qt.AlignLeft)
        left_column.setFormAlignment(Qt.AlignLeft | Qt.AlignTop)
        right_column = QVBoxLayout()
        right_column.setContentsMargins(0, 0, 0, 0)  # Minimal margins
        
        # Add common buttons to the right column
        delete_btn = QPushButton("Delete (DEL)")
        delete_btn.setStyleSheet(COMMON_BUTTON_STYLE + "QPushButton { background-color: #f44336; color: white; }")
        delete_btn.clicked.connect(self.delete_component)
        
        right_column.addWidget(delete_btn)
        
        # Add graphics toggle button for load components only
        if isinstance(component, LoadComponent):
            graphics_toggle = QPushButton("Graphics " + ("ON" if component.graphics_enabled else "OFF"))
            graphics_toggle.setStyleSheet(
                COMMON_BUTTON_STYLE + "QPushButton { background-color: #4CAF50; color: white; }" if component.graphics_enabled 
                else COMMON_BUTTON_STYLE + "QPushButton { background-color: #f44336; color: white; }"
            )
            
            def toggle_graphics():
                component.graphics_enabled = not component.graphics_enabled
                graphics_toggle.setText("Graphics " + ("ON" if component.graphics_enabled else "OFF"))
                graphics_toggle.setStyleSheet(
                    COMMON_BUTTON_STYLE + "QPushButton { background-color: #4CAF50; color: white; }" if component.graphics_enabled 
                    else COMMON_BUTTON_STYLE + "QPushButton { background-color: #f44336; color: white; }"
                )
                component.update()  # Redraw the component
            
            graphics_toggle.clicked.connect(toggle_graphics)
            graphics_toggle.setToolTip("Toggle visibility of the load component's image")
            right_column.addWidget(graphics_toggle)
        
        right_column.addStretch()  # Push everything to the top
        
        # Add component-specific properties to the left column
        if isinstance(component, BusComponent):
            self._add_bus_properties(component, left_column)
        elif isinstance(component, GeneratorComponent):
            self._add_generator_properties(component, left_column)
        elif isinstance(component, GridImportComponent):
            self._add_grid_import_properties(component, left_column)
        elif isinstance(component, GridExportComponent):
            self._add_grid_export_properties(component, left_column)
        elif isinstance(component, LoadComponent):
            self._add_load_properties(component, left_column)
        elif isinstance(component, BatteryComponent):
            self._add_battery_properties(component, left_column)
        elif isinstance(component, CloudWorkloadComponent):
            self._add_cloud_workload_properties(component, left_column)
        elif isinstance(component, SolarPanelComponent):
            self._add_solar_panel_properties(component, left_column)
        elif isinstance(component, TreeComponent):
            # Trees are decorative with no functional properties
            tree_info = QLabel("Decorative element - no properties to edit")
            left_column.addRow(tree_info)
        elif isinstance(component, BushComponent):
            # Bushes are decorative with no functional properties
            bush_info = QLabel("Decorative element - no properties to edit")
            left_column.addRow(bush_info)
        elif isinstance(component, PondComponent):
            # Ponds are decorative with no functional properties
            pond_info = QLabel("Decorative element - no properties to edit")
            left_column.addRow(pond_info)
        elif isinstance(component, House1Component):
            # Houses are decorative with no functional properties
            house1_info = QLabel("Decorative element - no properties to edit")
            left_column.addRow(house1_info)
        elif isinstance(component, House2Component):
            # Houses are decorative with no functional properties
            house2_info = QLabel("Decorative element - no properties to edit")
            left_column.addRow(house2_info)
        elif isinstance(component, FactoryComponent):
            # Factories are decorative with no functional properties
            factory_info = QLabel("Decorative element - no properties to edit")
            left_column.addRow(factory_info)
        else:
            # Add default message
            default_info = QLabel("No specific properties available for this component type")
            left_column.addRow(default_info)
        
        # Set up the main layout with both columns
        main_layout.addLayout(left_column, 3)  # 3:1 ratio for left:right
        main_layout.addLayout(right_column, 1)
        
        # Create a widget to hold the main layout
        main_widget = QWidget()
        main_widget.setLayout(main_layout)
        
        # Add the main widget to the properties layout
        self.properties_layout.addRow(main_widget)
        
        # Force the properties dock to resize to its minimum size
        self.properties_widget.adjustSize()
        self.main_window.properties_dock.adjustSize()
    
    def _add_bus_properties(self, component, layout):
        # Add name field
        name_edit = QLineEdit(component.name)
        name_edit.setStyleSheet(INPUT_STYLE)
        name_edit.textChanged.connect(lambda text: setattr(component, 'name', text))
        layout.addRow("Name:", name_edit)
        
        # Check if bus has any load connections
        has_loads = component.has_load_connections()
        
        # Add network state indicator - always AUTO when no loads
        network_state_label = QLabel("AUTO")
        if not has_loads:
            # Style for yellow background, black text
            network_state_label.setStyleSheet("""
                QLabel {
                    background-color: rgb(255, 215, 0);
                    color: black;
                    padding: 5px;
                    font-weight: bold;
                    border-radius: 3px;
                    border: 1px solid #555555;
                }
            """)
        else:
            network_state_label.setText("LOADED")
            network_state_label.setStyleSheet("""
                QLabel {
                    background-color: rgb(100, 100, 200);
                    color: white;
                    padding: 5px;
                    font-weight: bold;
                    border-radius: 3px;
                    border: 1px solid #555555;
                }
            """)
        
        layout.addRow("Bus State:", network_state_label)
        
        # Add on/off toggle - renamed to Load State
        state_toggle = QPushButton("ON" if component.is_on else "OFF")
        state_toggle.setStyleSheet(
            COMMON_BUTTON_STYLE + "QPushButton { background-color: #4CAF50; color: white; }" if component.is_on 
            else COMMON_BUTTON_STYLE + "QPushButton { background-color: #f44336; color: white; }"
        )
        
        # Enable or disable based on load connections
        state_toggle.setEnabled(has_loads)
        
        # Add tooltip explaining why it might be disabled
        if not has_loads:
            state_toggle.setToolTip("On/Off switch is disabled because this bus has no connected loads.")
            # Force bus to be on if it has no loads
            if not component.is_on:
                component.is_on = True
                state_toggle.setText("ON")
                state_toggle.setStyleSheet(COMMON_BUTTON_STYLE + "QPushButton { background-color: #4CAF50; color: white; }")
                component.update()  # Redraw the component
        else:
            state_toggle.setToolTip("Toggle power to connected loads.")
        
        def toggle_state():
            # Only allow toggling if there are connected loads
            if component.has_load_connections():
                component.is_on = not component.is_on
                state_toggle.setText("ON" if component.is_on else "OFF")
                state_toggle.setStyleSheet(
                    COMMON_BUTTON_STYLE + "QPushButton { background-color: #4CAF50; color: white; }" if component.is_on 
                    else COMMON_BUTTON_STYLE + "QPushButton { background-color: #f44336; color: white; }"
                )
                component.update()  # Redraw the component
                self.main_window.update_simulation()  # Update the simulation state
        
        state_toggle.clicked.connect(toggle_state)
        layout.addRow("Load State:", state_toggle)
    
    def _add_generator_properties(self, component, layout):
        capacity_edit = QLineEdit(str(component.capacity))
        capacity_edit.setStyleSheet(INPUT_STYLE)
        self._set_up_numeric_field(capacity_edit, lambda value: setattr(component, 'capacity', value))
        
        # Add operating mode selector
        mode_selector = QComboBox()
        mode_selector.setStyleSheet(COMBOBOX_STYLE)
        mode_selector.addItems(["Static (Auto)", "BTF Unit Commitment (Auto)", "BTF Droop (Auto)"])
        mode_selector.setCurrentText(component.operating_mode)
        
        # Add output level slider for static mode
        output_level_layout = QHBoxLayout()
        output_level_slider = QSlider(Qt.Horizontal)
        output_level_slider.setMinimum(0)
        output_level_slider.setMaximum(100)
        output_level_slider.setValue(int(component.output_level * 100))
        output_level_slider.setStyleSheet(SLIDER_STYLE)
        output_level_label = QLabel(f"{int(component.output_level * 100)}%")
        
        def update_output_level(value):
            component.output_level = value / 100
            output_level_label.setText(f"{value}%")
        
        output_level_slider.valueChanged.connect(update_output_level)
        output_level_layout.addWidget(output_level_slider)
        output_level_layout.addWidget(output_level_label)
        
        # Show/hide output level based on mode
        output_level_widget = QWidget()
        output_level_widget.setLayout(output_level_layout)
        output_level_widget.setVisible(component.operating_mode == "Static (Auto)")
        
        def on_mode_changed(text):
            component.operating_mode = text
            output_level_widget.setVisible(text == "Static (Auto)")
        
        mode_selector.currentTextChanged.connect(on_mode_changed)
        
        # Add ramp rate limiter controls
        ramp_rate_layout = QHBoxLayout()
        
        # Checkbox to enable/disable
        ramp_rate_checkbox = QPushButton("OFF")
        ramp_rate_checkbox.setCheckable(True)
        ramp_rate_checkbox.setChecked(component.ramp_rate_enabled)
        ramp_rate_checkbox.setStyleSheet(
            COMMON_BUTTON_STYLE + "QPushButton { background-color: #4CAF50; color: white; }" if component.ramp_rate_enabled 
            else COMMON_BUTTON_STYLE + "QPushButton { background-color: #f44336; color: white; }"
        )
        ramp_rate_checkbox.setText("ON" if component.ramp_rate_enabled else "OFF")
        
        # Ramp rate slider (10-20% per hour)
        ramp_rate_slider = QSlider(Qt.Horizontal)
        ramp_rate_slider.setMinimum(20)
        ramp_rate_slider.setMaximum(100)
        ramp_rate_slider.setValue(int(component.ramp_rate_limit * 100))
        ramp_rate_slider.setStyleSheet(SLIDER_STYLE)
        ramp_rate_label = QLabel(f"{int(component.ramp_rate_limit * 100)}%/hr")
        
        def update_ramp_rate(value):
            component.ramp_rate_limit = value / 100
            ramp_rate_label.setText(f"{value}%/hr")
        
        def toggle_ramp_rate():
            component.ramp_rate_enabled = not component.ramp_rate_enabled
            ramp_rate_checkbox.setText("ON" if component.ramp_rate_enabled else "OFF")
            ramp_rate_checkbox.setStyleSheet(
                COMMON_BUTTON_STYLE + "QPushButton { background-color: #4CAF50; color: white; }" if component.ramp_rate_enabled 
                else COMMON_BUTTON_STYLE + "QPushButton { background-color: #f44336; color: white; }"
            )
            ramp_rate_slider.setEnabled(component.ramp_rate_enabled)
            ramp_rate_label.setEnabled(component.ramp_rate_enabled)
        
        ramp_rate_checkbox.clicked.connect(toggle_ramp_rate)
        ramp_rate_slider.valueChanged.connect(update_ramp_rate)
        
        # Set initial state
        ramp_rate_slider.setEnabled(component.ramp_rate_enabled)
        ramp_rate_label.setEnabled(component.ramp_rate_enabled)
        
        ramp_rate_layout.addWidget(ramp_rate_checkbox)
        ramp_rate_layout.addWidget(ramp_rate_slider)
        ramp_rate_layout.addWidget(ramp_rate_label)
        
        ramp_rate_widget = QWidget()
        ramp_rate_widget.setLayout(ramp_rate_layout)
        
        # Add auto-charging toggle button
        auto_charging_btn = QPushButton("ON" if component.auto_charging else "OFF")
        auto_charging_btn.setStyleSheet(
            COMMON_BUTTON_STYLE + "QPushButton { background-color: #4CAF50; color: white; }" if component.auto_charging 
            else COMMON_BUTTON_STYLE + "QPushButton { background-color: #f44336; color: white; }"
        )
        
        def toggle_auto_charging():
            component.auto_charging = not component.auto_charging
            auto_charging_btn.setText("ON" if component.auto_charging else "OFF")
            auto_charging_btn.setStyleSheet(
                COMMON_BUTTON_STYLE + "QPushButton { background-color: #4CAF50; color: white; }" if component.auto_charging 
                else COMMON_BUTTON_STYLE + "QPushButton { background-color: #f44336; color: white; }"
            )
        
        auto_charging_btn.clicked.connect(toggle_auto_charging)
        
        # Add all controls to properties layout
        layout.addRow("Capacity (kW):", capacity_edit)
        layout.addRow("Operating Mode:", mode_selector)
        layout.addRow("Output Level:", output_level_widget)
        layout.addRow("Ramp Rate Limiter:", ramp_rate_widget)
        layout.addRow("Auto-Charge Batteries:", auto_charging_btn)
    
    def _add_grid_import_properties(self, component, layout):
        capacity_edit = QLineEdit(str(component.capacity))
        capacity_edit.setStyleSheet(INPUT_STYLE)
        self._set_up_numeric_field(capacity_edit, lambda value: setattr(component, 'capacity', value))
        
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
            self.main_window.update_simulation()
        
        auto_charging_btn.clicked.connect(toggle_auto_charging)
        
        layout.addRow("Max Capacity (kW):", capacity_edit)
        layout.addRow("Operating Mode:", QLabel("Auto"))
        layout.addRow("Auto-Charge Batteries:", auto_charging_btn)
    
    def _add_grid_export_properties(self, component, layout):
        capacity_edit = QLineEdit(str(component.capacity))
        capacity_edit.setStyleSheet(INPUT_STYLE)
        self._set_up_numeric_field(capacity_edit, lambda value: setattr(component, 'capacity', value))
        
        # Add price per kWh field
        price_edit = QLineEdit(str(component.bulk_ppa_price))
        price_edit.setStyleSheet(INPUT_STYLE)
        self._set_up_numeric_field(price_edit, lambda value: setattr(component, 'bulk_ppa_price', value), min_value=0.00)
        
        layout.addRow("Max Capacity (kW):", capacity_edit)
        layout.addRow("Bulk Export PPA ($/kWh):", price_edit)
        layout.addRow("Operating Mode:", QLabel("Auto"))
    
    def _add_load_properties(self, component, layout):
        demand_edit = QLineEdit(str(component.demand))
        demand_edit.setStyleSheet(INPUT_STYLE)
        self._set_up_numeric_field(demand_edit, lambda value: setattr(component, 'demand', value))
        
        # Add price per kWh field
        price_edit = QLineEdit(str(component.price_per_kwh))
        price_edit.setStyleSheet(INPUT_STYLE)
        self._set_up_numeric_field(price_edit, lambda value: setattr(component, 'price_per_kwh', value), min_value=0.00)
        
        profile_type = QComboBox()
        profile_type.setStyleSheet(COMBOBOX_STYLE)
        profile_type.addItems(["Data Center", "Sine Wave", "Custom", "Random 8760", "Constant"])
        profile_type.setCurrentText(component.profile_type)
        
        # Create a horizontal layout for profile selection and load button
        profile_layout = QHBoxLayout()
        profile_layout.addWidget(profile_type)
        
        # Add load profile button (only visible for Custom type)
        load_profile_btn = QPushButton("Load Profile")
        load_profile_btn.setStyleSheet(DEFAULT_BUTTON_STYLE)
        load_profile_btn.setVisible(component.profile_type == "Custom")
        load_profile_btn.clicked.connect(lambda: self._load_custom_profile(component))
        profile_layout.addWidget(load_profile_btn)
        
        # Create a widget to hold the profile layout
        profile_widget = QWidget()
        profile_widget.setLayout(profile_layout)
        
        # Add profile info label
        profile_info = QLabel()
        if component.profile_type == "Custom" and component.profile_name:
            profile_info.setText(f"Loaded: {component.profile_name}")
        else:
            profile_info.setText("")
        
        # Create data center type selector
        data_center_layout = QHBoxLayout()
        data_center_type = QComboBox()
        data_center_type.setStyleSheet(COMBOBOX_STYLE)
        data_center_type.addItems(["GPU Intensive", "Traditional Cloud", "Crypto ASIC"])
        data_center_type.setCurrentText(component.data_center_type)
        data_center_type.currentTextChanged.connect(lambda text: setattr(component, 'data_center_type', text))
        data_center_layout.addWidget(data_center_type)
        
        # Create a widget to hold the data center type selector
        data_center_widget = QWidget()
        data_center_widget.setLayout(data_center_layout)
        data_center_widget.setVisible(component.profile_type == "Data Center")
        
        # Create data center profile generator button
        dc_generate_layout = QHBoxLayout()
        dc_generate_btn = QPushButton("Generate Data Center Profile")
        dc_generate_btn.setStyleSheet(DEFAULT_BUTTON_STYLE)
        
        def generate_data_center_profile():
            # Clear any existing random profile
            component.random_profile = None
            # Generate new profile based on selected data center type
            component.generate_data_center_profile()
            self.main_window.update_simulation()
            # Show popup notification
            QMessageBox.information(self.main_window, "Data Center Profile Generated", 
                                  f"Generated 8760 hours of {component.data_center_type} data center profile.")
        
        dc_generate_btn.clicked.connect(generate_data_center_profile)
        dc_generate_layout.addWidget(dc_generate_btn)
        
        # Create a widget to hold the data center generator controls
        dc_generate_widget = QWidget()
        dc_generate_widget.setLayout(dc_generate_layout)
        dc_generate_widget.setVisible(component.profile_type == "Data Center")
        
        # Create random profile generator controls
        random_profile_layout = QHBoxLayout()
        generate_btn = QPushButton("Generate Random Data")
        generate_btn.setStyleSheet(DEFAULT_BUTTON_STYLE)
        
        def generate_random_data():
            # Clear any existing random profile
            component.random_profile = None
            # Generate new profile
            component.generate_random_profile()
            self.main_window.update_simulation()
            # Show popup notification
            QMessageBox.information(self.main_window, "Random Profile Generated", 
                                  f"Generated 8760 hours of random load data with {int(component.max_ramp_rate * 100)}% max ramp rate.")
        
        generate_btn.clicked.connect(generate_random_data)
        random_profile_layout.addWidget(generate_btn)
        
        # Create a widget to hold the random profile controls
        random_profile_widget = QWidget()
        random_profile_widget.setLayout(random_profile_layout)
        random_profile_widget.setVisible(component.profile_type == "Random 8760")
        
        # Create max ramp rate control for Random 8760 mode
        ramp_rate_layout = QHBoxLayout()
        ramp_rate_edit = QLineEdit(str(int(component.max_ramp_rate * 100)))
        ramp_rate_edit.setMaximumWidth(50)
        ramp_rate_edit.setStyleSheet(INPUT_STYLE)
        
        # Helper method to update component from the edit field
        def update_ramp_rate_from_edit_value(value):
            int_value = int(value)
            component.max_ramp_rate = int_value / 100.0
            ramp_rate_slider.setValue(int_value)
            ramp_rate_value_label.setText(f"{int_value}%/hr")
            # Only regenerate if we have an existing profile
            if component.random_profile and not ramp_rate_slider.isSliderDown():
                generate_random_data()
        
        # Set up numeric validation for the edit field
        self._set_up_numeric_field(ramp_rate_edit, 
                                 update_ramp_rate_from_edit_value,
                                 is_float=False, min_value=1, max_value=100)
        
        ramp_rate_slider = QSlider(Qt.Horizontal)
        ramp_rate_slider.setMinimum(1)  # 1% minimum
        ramp_rate_slider.setMaximum(100)  # 100% maximum
        ramp_rate_slider.setValue(int(component.max_ramp_rate * 100))
        ramp_rate_slider.setStyleSheet(SLIDER_STYLE)
        
        # Add a ramp rate value label
        ramp_rate_value_label = QLabel(f"{int(component.max_ramp_rate * 100)}%/hr")
        
        # Connect the controls to update the component
        def update_ramp_rate_from_slider(value):
            component.max_ramp_rate = value / 100.0
            # Use blockSignals to prevent recursive updates
            ramp_rate_edit.blockSignals(True)
            ramp_rate_edit.setText(str(value))
            ramp_rate_edit.blockSignals(False)
            ramp_rate_value_label.setText(f"{value}%/hr")
            # Don't regenerate while dragging - wait until slider is released
        
        def regenerate_on_slider_release():
            # Only regenerate when slider is released
            if component.random_profile:
                generate_random_data()
        
        ramp_rate_slider.valueChanged.connect(update_ramp_rate_from_slider)
        ramp_rate_slider.sliderReleased.connect(regenerate_on_slider_release)
        
        ramp_rate_layout.addWidget(ramp_rate_edit)
        ramp_rate_layout.addWidget(ramp_rate_slider)
        ramp_rate_layout.addWidget(ramp_rate_value_label)
        
        # Create a widget to hold the ramp rate controls
        ramp_rate_widget = QWidget()
        ramp_rate_widget.setLayout(ramp_rate_layout)
        ramp_rate_widget.setVisible(component.profile_type == "Random 8760")
        
        # Create time offset control (spinner and slider)
        time_offset_layout = QHBoxLayout()
        time_offset_edit = QLineEdit(str(component.time_offset))
        time_offset_edit.setMaximumWidth(50)
        time_offset_edit.setStyleSheet(INPUT_STYLE)
        self._set_up_numeric_field(time_offset_edit, 
                                 lambda value: setattr(component, 'time_offset', value),
                                 is_float=False, min_value=0, max_value=8760)
        
        time_offset_slider = QSlider(Qt.Horizontal)
        time_offset_slider.setMinimum(0)
        time_offset_slider.setMaximum(8760)  # Maximum hours in a year
        time_offset_slider.setValue(component.time_offset)
        time_offset_slider.setStyleSheet(SLIDER_STYLE)
        
        # Connect the controls to update the component
        def update_offset_from_slider(value):
            component.time_offset = value
            # Use blockSignals to prevent recursive updates
            time_offset_edit.blockSignals(True)
            time_offset_edit.setText(str(value))
            time_offset_edit.blockSignals(False)
            self.main_window.update_simulation()
        
        time_offset_slider.valueChanged.connect(update_offset_from_slider)
        
        time_offset_layout.addWidget(time_offset_edit)
        time_offset_layout.addWidget(time_offset_slider)
        
        # Create a widget to hold the time offset controls
        time_offset_widget = QWidget()
        time_offset_widget.setLayout(time_offset_layout)
        
        # Create frequency control for Sine Wave mode
        frequency_layout = QHBoxLayout()
        frequency_edit = QLineEdit(str(component.frequency))
        frequency_edit.setMaximumWidth(50)
        frequency_edit.setStyleSheet(INPUT_STYLE)
        self._set_up_numeric_field(frequency_edit, 
                                 lambda value: setattr(component, 'frequency', value),
                                 min_value=0.1, max_value=5.0)
        
        frequency_slider = QSlider(Qt.Horizontal)
        frequency_slider.setMinimum(10)  # 0.1 cycles per day
        frequency_slider.setMaximum(500)  # 5 cycles per day
        frequency_slider.setValue(int(component.frequency * 100))
        frequency_slider.setStyleSheet(SLIDER_STYLE)
        
        # Add a frequency value label
        frequency_value_label = QLabel(f"{component.frequency} cycles/day")
        
        # Connect the controls to update the component
        def update_frequency_from_slider(value):
            # Convert from slider value (10-500) to frequency (0.1-5.0)
            freq = value / 100.0
            component.frequency = freq
            # Use blockSignals to prevent recursive updates
            frequency_edit.blockSignals(True)
            frequency_edit.setText(str(freq))
            frequency_edit.blockSignals(False)
            frequency_value_label.setText(f"{freq} cycles/day")
            self.main_window.update_simulation()
        
        frequency_slider.valueChanged.connect(update_frequency_from_slider)
        
        frequency_layout.addWidget(frequency_edit)
        frequency_layout.addWidget(frequency_slider)
        frequency_layout.addWidget(frequency_value_label)
        
        # Create a widget to hold the frequency controls
        frequency_widget = QWidget()
        frequency_widget.setLayout(frequency_layout)
        
        # Only show frequency control for Sine Wave profile
        frequency_widget.setVisible(component.profile_type == "Sine Wave")
        
        # Only show time offset for Sine Wave and Custom profiles
        time_offset_widget.setVisible(component.profile_type in ["Sine Wave", "Custom"])
        
        def on_profile_changed(text):
            setattr(component, 'profile_type', text)
            load_profile_btn.setVisible(text == "Custom")
            time_offset_widget.setVisible(text in ["Sine Wave", "Custom"])
            frequency_widget.setVisible(text == "Sine Wave")
            random_profile_widget.setVisible(text == "Random 8760")
            ramp_rate_widget.setVisible(text == "Random 8760")
            data_center_widget.setVisible(text == "Data Center")
            dc_generate_widget.setVisible(text == "Data Center")
            if text == "Random 8760" and not component.random_profile:
                # Auto-generate random profile when mode is selected
                generate_random_data()
            elif text == "Data Center" and not component.random_profile:
                # Auto-generate data center profile when mode is selected
                generate_data_center_profile()
            elif text != "Custom":
                component.custom_profile = None
                component.profile_name = None
                profile_info.setText("")
        
        profile_type.currentTextChanged.connect(on_profile_changed)
        
        layout.addRow("Demand (kW):", demand_edit)
        layout.addRow("Price per kWh ($):", price_edit)
        layout.addRow("Profile Type:", profile_widget)
        layout.addRow("", profile_info)
        layout.addRow("Data Center Type:", data_center_widget)
        layout.addRow("", dc_generate_widget)
        layout.addRow("", random_profile_widget)
        layout.addRow("Max Ramp Rate:", ramp_rate_widget)
        layout.addRow("Time Offset (hr):", time_offset_widget)
        layout.addRow("Frequency:", frequency_widget)
    
    def _add_battery_properties(self, component, layout):
        # Power capacity field
        power_capacity_edit = QLineEdit(str(component.power_capacity))
        power_capacity_edit.setStyleSheet(INPUT_STYLE)
        self._set_up_numeric_field(power_capacity_edit, 
                                 lambda value: setattr(component, 'power_capacity', value),
                                 min_value=1)
        
        # Energy capacity field
        energy_capacity_edit = QLineEdit(str(component.energy_capacity))
        energy_capacity_edit.setStyleSheet(INPUT_STYLE)
        self._set_up_numeric_field(energy_capacity_edit, 
                                 lambda value: setattr(component, 'energy_capacity', value),
                                 min_value=1)
        
        # Current charge field (limited by energy capacity)
        current_charge_edit = QLineEdit(str(component.current_charge))
        current_charge_edit.setStyleSheet(INPUT_STYLE)
        
        def update_current_charge(value):
            # Skip if already updating to prevent recursive updates
            if self.main_window.simulation_engine.updating_simulation:
                return
                
            # Limit current charge to energy capacity
            setattr(component, 'current_charge', min(value, component.energy_capacity))
            
            # Block signals temporarily to avoid recursive calls
            current_charge_edit.blockSignals(True)
            current_charge_edit.setText(str(component.current_charge))
            current_charge_edit.blockSignals(False)
            
            # Update charge slider to match
            if component.energy_capacity > 0:
                charge_percent = int((component.current_charge / component.energy_capacity) * 100)
            else:
                charge_percent = 0
            
            # Block signals temporarily to avoid recursive calls
            charge_bar.blockSignals(True)
            charge_bar.setValue(charge_percent)
            charge_bar.blockSignals(False)
            
            charge_label.setText(f"{charge_percent}%")
            
            component.update()
            self.main_window.update_simulation()
        
        self._set_up_numeric_field(current_charge_edit, update_current_charge, min_value=0)
        
        # Operating mode selector
        mode_selector = QComboBox()
        mode_selector.setStyleSheet(COMBOBOX_STYLE)
        mode_selector.addItems(["Off", "BTF Basic Unit (Auto)"])
        mode_selector.setCurrentText(component.operating_mode)
        
        # Connect operating mode change
        def change_mode(text):
            component.operating_mode = text
            component.update()
            self.main_window.update_simulation()
        
        mode_selector.currentTextChanged.connect(change_mode)
        
        # Add charge percentage progress bar
        if component.energy_capacity > 0:
            charge_percent = int((component.current_charge / component.energy_capacity) * 100)
        else:
            charge_percent = 0
            
        charge_bar = QSlider(Qt.Horizontal)
        charge_bar.setMinimum(0)
        charge_bar.setMaximum(100)
        charge_bar.setValue(charge_percent)
        charge_bar.setEnabled(True)  # Enable the slider
        charge_bar.setStyleSheet(SLIDER_STYLE)
        
        charge_label = QLabel(f"{charge_percent}%")
        
        # Connect the slider to update the charge
        def update_charge_from_slider(value):
            # Skip if already updating to prevent recursive updates
            if self.main_window.simulation_engine.updating_simulation:
                return
                
            new_charge = (value / 100.0) * component.energy_capacity
            component.current_charge = new_charge
            
            # Block signals temporarily to avoid recursive calls
            current_charge_edit.blockSignals(True)
            current_charge_edit.setText(str(int(new_charge)))
            current_charge_edit.blockSignals(False)
            
            charge_label.setText(f"{value}%")
            component.update()
            self.main_window.update_simulation()
        
        charge_bar.valueChanged.connect(update_charge_from_slider)
        
        charge_layout = QHBoxLayout()
        charge_layout.addWidget(charge_bar, 7)
        charge_layout.addWidget(charge_label, 1)
        
        charge_widget = QWidget()
        charge_widget.setLayout(charge_layout)
        
        # Add controls to layout
        layout.addRow("Power Capacity (kW):", power_capacity_edit)
        layout.addRow("Energy Capacity (kWh):", energy_capacity_edit)
        layout.addRow("Current Charge (kWh):", current_charge_edit)
        layout.addRow("Charge Level:", charge_widget)
        layout.addRow("Operating Mode:", mode_selector)
    
    def _add_cloud_workload_properties(self, component, layout):
        """Add properties for CloudWorkloadComponent"""
        # Add operating mode selector
        mode_selector = QComboBox()
        mode_selector.setStyleSheet(COMBOBOX_STYLE)
        mode_selector.addItems(["No Customer", "Multi-Cloud Spot"])
        mode_selector.setCurrentText(component.operating_mode)
        
        # Create a container for resource parameters that will only be visible in Multi-Cloud Spot mode
        resource_params_widget = QWidget()
        resource_params_layout = QFormLayout(resource_params_widget)
        resource_params_layout.setContentsMargins(10, 10, 10, 10)
        
        # Add traditional cloud parameters
        trad_params_label = QLabel(f"Power: {component.traditional_cloud_power} kW\nPrice: ${component.traditional_cloud_price:.2f}")
        resource_params_layout.addRow("Traditional Cloud:", trad_params_label)
        
        # Add GPU intensive parameters
        gpu_params_label = QLabel(f"Power: {component.gpu_intensive_power} kW\nPrice: ${component.gpu_intensive_price:.2f}")
        resource_params_layout.addRow("GPU Intensive:", gpu_params_label)
        
        # Add crypto ASIC parameters
        crypto_params_label = QLabel(f"Power: {component.crypto_asic_power} kW\nPrice: ${component.crypto_asic_price:.2f}")
        resource_params_layout.addRow("Crypto ASIC:", crypto_params_label)
        
        # Add revenue display
        revenue_label = QLabel(f"${component.accumulated_revenue:.2f}")
        revenue_label.setStyleSheet("font-weight: bold;")
        resource_params_layout.addRow("Accumulated Revenue:", revenue_label)
        
        # Set left alignment for all labels in the form
        resource_params_layout.setLabelAlignment(Qt.AlignLeft)
        resource_params_layout.setFormAlignment(Qt.AlignLeft | Qt.AlignTop)
        
        # Set visibility based on current mode
        resource_params_widget.setVisible(component.operating_mode == "Multi-Cloud Spot")
        
        # Connect mode selector to update component and UI
        def on_mode_changed(text):
            component.operating_mode = text
            component.update()
            # Show/hide resource parameters based on mode
            resource_params_widget.setVisible(text == "Multi-Cloud Spot")
            # Reset accumulated revenue when switching modes
            if text != component.operating_mode:
                component.accumulated_revenue = 0.0
                revenue_label.setText(f"${component.accumulated_revenue:.2f}")
        
        mode_selector.currentTextChanged.connect(on_mode_changed)
        layout.addRow("Operating Mode:", mode_selector)
        layout.addRow("", resource_params_widget)
    
    def _add_solar_panel_properties(self, component, layout):
        """Add properties for SolarPanelComponent"""
        # Add operating mode selector
        mode_selector = QComboBox()
        mode_selector.setStyleSheet(COMBOBOX_STYLE)
        mode_selector.addItems(["Disabled", "Powerlandia 8760 - Midwest 1"])
        mode_selector.setCurrentText(component.operating_mode)
        
        def on_mode_changed(text):
            component.operating_mode = text
            # If switching to Powerlandia mode, load capacity factors
            if text == "Powerlandia 8760 - Midwest 1":
                component.load_capacity_factors()
            component.update()  # Refresh the component display
            self.main_window.update_simulation()  # Update simulation to reflect the change
        
        mode_selector.currentTextChanged.connect(on_mode_changed)
        layout.addRow("Operating Mode:", mode_selector)
        
        # Add capacity field
        capacity_field = QLineEdit(str(component.capacity))
        capacity_field.setStyleSheet(INPUT_STYLE)
        
        def update_capacity(value):
            try:
                component.capacity = float(value)
                component.update()  # Refresh the component display
                self.main_window.update_simulation()
            except (ValueError, TypeError):
                # Restore previous value if input is invalid
                capacity_field.setText(str(component.capacity))
        
        # Set up numeric validation for the capacity field
        self._set_up_numeric_field(capacity_field, update_capacity, is_float=True, min_value=0)
        layout.addRow("Capacity (kW):", capacity_field)
    
    def _load_custom_profile(self, component):
        filename, _ = QFileDialog.getOpenFileName(self.main_window, "Load Custom Profile", "", "CSV Files (*.csv)")
        if filename:
            try:
                # Read the CSV file
                data = []
                with open(filename, 'r') as f:
                    reader = csv.reader(f)
                    next(reader)  # Skip header row
                    for row in reader:
                        data.append(float(row[0]))  # Assume first column is load factor
                
                # Store the profile data
                component.custom_profile = data
                component.profile_name = filename.split('/')[-1]
                
                # Update maximum time steps if needed
                if len(data) > self.main_window.time_slider.maximum():
                    self.main_window.time_slider.setMaximum(len(data) - 1)
                
                # Refresh properties panel to show loaded profile name
                self.show_component_properties(component)
                
                QMessageBox.information(self.main_window, "Profile Loaded", 
                                      f"Loaded {len(data)} time steps from {component.profile_name}")
            
            except Exception as e:
                QMessageBox.critical(self.main_window, "Error Loading Profile", str(e))
                component.profile_type = "Constant"
                self.show_component_properties(component)
    
    def _set_up_numeric_field(self, line_edit, setter_function, is_float=True, min_value=0, max_value=float('inf')):
        """Set up a QLineEdit to only accept valid numeric input
        
        Args:
            line_edit: The QLineEdit to set up
            setter_function: Function to call with the numeric value when input is valid
            is_float: Whether to treat input as float (True) or int (False)
            min_value: Minimum allowed value
            max_value: Maximum allowed value
        """
        # Set up appropriate validator
        if is_float:
            validator = QDoubleValidator(min_value, max_value, 2)
        else:
            validator = QIntValidator(min_value, max_value)
            
        line_edit.setValidator(validator)
        
        # Set minimum width to accommodate larger numbers
        line_edit.setMinimumWidth(100)
        
        # Handle text changed events with proper validation
        def on_text_changed(text):
            if not text or text == '-':
                setter_function(0)
                return
                
            # Extra validation before conversion to prevent ValueErrors
            try:
                if is_float:
                    # Check if the text is a valid float format
                    if not re.match(r'^-?\d*\.?\d*$', text):
                        return
                    value = float(text)
                else:
                    # Check if the text is a valid integer format
                    if not re.match(r'^-?\d+$', text):
                        return
                    value = int(text)
                    
                # Clamp to range
                value = max(min_value, min(value, max_value))
                setter_function(value)
            except (ValueError, TypeError) as e:
                # Just return without calling the setter function
                # This prevents passing invalid values to the setter
                pass
        
        line_edit.textChanged.connect(on_text_changed) 

    def delete_component(self):
        """Delete the selected component from the scene"""
        component = self.current_component
        if component:
            # Find and remove all connections associated with this component
            connections_to_remove = [conn for conn in self.main_window.connections 
                                if conn.source == component or conn.target == component]
            
            for connection in connections_to_remove:
                connection.cleanup()
                self.main_window.scene.removeItem(connection)
                self.main_window.connections.remove(connection)
            
            # Remove the component from the scene and list
            self.main_window.scene.removeItem(component)
            
            # Only remove from components list if it's a functional component (not a decorative one)
            if not isinstance(component, (TreeComponent, BushComponent, PondComponent, House1Component, House2Component, FactoryComponent)):
                self.main_window.components.remove(component)
            
            # Clear the properties panel
            while self.properties_layout.count():
                item = self.properties_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
                elif item.layout():
                    # Clear sub-layouts
                    while item.layout().count():
                        sub_item = item.layout().takeAt(0)
                        if sub_item.widget():
                            sub_item.widget().deleteLater()
                    item.layout().deleteLater()
            
            # Update simulation state
            self.main_window.update_simulation() 