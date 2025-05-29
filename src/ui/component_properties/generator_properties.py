from PyQt5.QtWidgets import (QLineEdit, QLabel, QPushButton, QComboBox, QHBoxLayout, QSlider, QWidget)
from PyQt5.QtCore import Qt

# Import styles from the parent module
from src.ui.properties_manager import COMMON_BUTTON_STYLE, INPUT_STYLE, COMBOBOX_STYLE, SLIDER_STYLE

def add_generator_properties(properties_manager, component, layout):
    # Display capacity in MW in the edit field
    capacity_edit = QLineEdit(str(component.capacity / 1000))
    capacity_edit.setStyleSheet(INPUT_STYLE)
    
    def update_capacity(value):
        # Convert back to kW for internal storage
        kw_value = value * 1000
        setattr(component, 'capacity', kw_value)
        # Update CAPEX display when capacity changes
        properties_manager.main_window.update_capex_display()
        
    properties_manager._set_up_numeric_field(capacity_edit, update_capacity, min_value=0.025, max_value=5000)
    
    # Add operating mode selector
    mode_selector = QComboBox()
    mode_selector.setStyleSheet(COMBOBOX_STYLE)
    mode_selector.addItems(["Static (Auto)", "BTF Unit Commit (Auto)", "BTF Droop (Auto)"])
    mode_selector.setCurrentText(component.operating_mode)
    
    # Add output level slider for static mode
    output_level_layout = QHBoxLayout()
    output_level_layout.setContentsMargins(0, 0, 0, 0)
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
    
    # Always show output level widget, but enable/disable based on mode
    def update_control_states(mode):
        is_static_mode = mode == "Static (Auto)"
        output_level_widget.setEnabled(is_static_mode)
        # Update label styling when disabled
        if is_static_mode:
            output_level_label.setStyleSheet("color: white;")
        else:
            output_level_label.setStyleSheet("color: #888888;")  # Grey out when disabled
    
    # Set initial state
    update_control_states(component.operating_mode)
    
    def on_mode_changed(text):
        component.operating_mode = text
        update_control_states(text)
    
    mode_selector.currentTextChanged.connect(on_mode_changed)
    
    # Add ramp rate limiter controls
    ramp_rate_layout = QHBoxLayout()
    ramp_rate_layout.setContentsMargins(0, 0, 0, 0)
    # Checkbox to enable/disable
    ramp_rate_checkbox = QPushButton("OFF")
    ramp_rate_checkbox.setCheckable(True)
    ramp_rate_checkbox.setChecked(component.ramp_rate_enabled)
    ramp_rate_checkbox.setStyleSheet(
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
    """ if component.ramp_rate_enabled 
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
    ramp_rate_checkbox.setText("ON" if component.ramp_rate_enabled else "OFF")
    
    # Ramp rate slider (1-100% per hour)
    ramp_rate_slider = QSlider(Qt.Horizontal)
    ramp_rate_slider.setMinimum(1)
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
    """ if component.ramp_rate_enabled 
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
        ramp_rate_slider.setEnabled(component.ramp_rate_enabled)
        ramp_rate_label.setEnabled(component.ramp_rate_enabled)
        # Update label styling when disabled
        if component.ramp_rate_enabled:
            ramp_rate_label.setStyleSheet("color: white;")
        else:
            ramp_rate_label.setStyleSheet("color: #888888;")  # Grey out when disabled
    
    ramp_rate_checkbox.clicked.connect(toggle_ramp_rate)
    ramp_rate_slider.valueChanged.connect(update_ramp_rate)
    
    # Set initial state
    ramp_rate_slider.setEnabled(component.ramp_rate_enabled)
    ramp_rate_label.setEnabled(component.ramp_rate_enabled)
    # Set initial label styling based on enabled state
    if component.ramp_rate_enabled:
        ramp_rate_label.setStyleSheet("color: white;")
    else:
        ramp_rate_label.setStyleSheet("color: #888888;")  # Grey out when disabled
    
    ramp_rate_layout.addWidget(ramp_rate_checkbox)
    ramp_rate_layout.addWidget(ramp_rate_slider)
    ramp_rate_layout.addWidget(ramp_rate_label)
    
    ramp_rate_widget = QWidget()
    ramp_rate_widget.setLayout(ramp_rate_layout)
    
    # Add auto-charging toggle button
    auto_charging_btn = QPushButton("ON" if component.auto_charging else "OFF")
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
    """ if component.auto_charging 
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
        component.auto_charging = not component.auto_charging
        auto_charging_btn.setText("ON" if component.auto_charging else "OFF")
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
    """ if component.auto_charging 
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
    
    auto_charging_btn.clicked.connect(toggle_auto_charging)
    
    # Add conversion constant info label
    conversion_info = QLabel(f"{component.conversion_constant}")
    conversion_info.setStyleSheet("color: white;")
    
    # Add efficiency field
    efficiency_layout = QHBoxLayout()
    efficiency_layout.setContentsMargins(0, 0, 0, 0)
    efficiency_slider = QSlider(Qt.Horizontal)
    efficiency_slider.setMinimum(10)  # 10% minimum
    efficiency_slider.setMaximum(95)  # 95% maximum (practical limit)
    efficiency_slider.setValue(int(component.efficiency * 100))
    efficiency_slider.setStyleSheet(SLIDER_STYLE)
    efficiency_label = QLabel(f"{int(component.efficiency * 100)}%")
    
    def update_efficiency(value):
        component.efficiency = value / 100
        efficiency_label.setText(f"{value}%")
    
    efficiency_slider.valueChanged.connect(update_efficiency)
    efficiency_layout.addWidget(efficiency_slider)
    efficiency_layout.addWidget(efficiency_label)
    
    efficiency_widget = QWidget()
    efficiency_widget.setLayout(efficiency_layout)
    
    # Add cost per GJ field
    cost_edit = QLineEdit(str(component.cost_per_gj))
    cost_edit.setStyleSheet(INPUT_STYLE)
    properties_manager._set_up_numeric_field(cost_edit, lambda value: setattr(component, 'cost_per_gj', value), min_value=0.00)
    
    # Add CAPEX per kW field
    capex_edit = QLineEdit(str(component.capex_per_kw))
    capex_edit.setStyleSheet(INPUT_STYLE)
    
    def update_capex(value):
        setattr(component, 'capex_per_kw', value)
        # Update CAPEX display when CAPEX per kW changes
        properties_manager.main_window.update_capex_display()
        
    properties_manager._set_up_numeric_field(capex_edit, update_capex, min_value=0.00, max_value=100000)
    
    # Add maintenance parameters  
    # Frequency per 10,000 hours field
    frequency_edit = QLineEdit(str(component.frequency_per_10000_hours))
    frequency_edit.setStyleSheet(INPUT_STYLE)
    properties_manager._set_up_numeric_field(frequency_edit, 
                              lambda value: setattr(component, 'frequency_per_10000_hours', value), 
                              min_value=0.0, max_value=1000.0)
    
    # Minimum downtime field
    min_downtime_edit = QLineEdit(str(component.minimum_downtime))
    min_downtime_edit.setStyleSheet(INPUT_STYLE)
    properties_manager._set_up_numeric_field(min_downtime_edit, 
                              lambda value: setattr(component, 'minimum_downtime', value), 
                              is_float=False, min_value=1, max_value=1000)
    
    # Maximum downtime field
    max_downtime_edit = QLineEdit(str(component.maximum_downtime))
    max_downtime_edit.setStyleSheet(INPUT_STYLE)
    properties_manager._set_up_numeric_field(max_downtime_edit, 
                              lambda value: setattr(component, 'maximum_downtime', value), 
                              is_float=False, min_value=1, max_value=1000)
    
    # Cooldown time field
    cooldown_edit = QLineEdit(str(component.cooldown_time))
    cooldown_edit.setStyleSheet(INPUT_STYLE)
    properties_manager._set_up_numeric_field(cooldown_edit, 
                              lambda value: setattr(component, 'cooldown_time', value), 
                              is_float=False, min_value=1, max_value=10000)
    
    # Add all controls to properties layout
    layout.addRow("Operating Mode:", mode_selector)
    layout.addRow("Capacity (MW):", capacity_edit)
    layout.addRow("Static Output:", output_level_widget)
    layout.addRow("Ramp Rate Limit:", ramp_rate_widget)
    layout.addRow("Auto-Charging:", auto_charging_btn)
    layout.addRow("kWh per GJ:", conversion_info)
    layout.addRow("Efficiency:", efficiency_widget)
    layout.addRow("Gas Cost ($/GJ):", cost_edit)
    layout.addRow("CAPEX per kW ($):", capex_edit)
    layout.addRow("Outage (/10k hrs):", frequency_edit)
    layout.addRow("Min Outage (hrs):", min_downtime_edit)
    layout.addRow("Max Outage (hrs):", max_downtime_edit)
    layout.addRow("Cooldown (hrs):", cooldown_edit) 