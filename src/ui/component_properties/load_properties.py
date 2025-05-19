from PyQt5.QtWidgets import (QLineEdit, QLabel, QPushButton, QComboBox, 
                            QHBoxLayout, QWidget, QSlider, QMessageBox)
from PyQt5.QtCore import Qt
from src.ui.terminal_widget import TerminalWidget

# Import styles from the parent module
from src.ui.properties_manager import COMMON_BUTTON_STYLE, INPUT_STYLE, DEFAULT_BUTTON_STYLE, COMBOBOX_STYLE, SLIDER_STYLE

def add_load_properties(properties_manager, component, layout):
    # Display demand in MW in the edit field
    demand_edit = QLineEdit(str(component.demand / 1000))
    demand_edit.setStyleSheet(INPUT_STYLE)
    
    def update_demand(value):
        # Convert back to kW for internal storage
        kw_value = value * 1000
        setattr(component, 'demand', kw_value)
        # Update CAPEX display when demand changes
        properties_manager.main_window.update_capex_display()
        
    properties_manager._set_up_numeric_field(demand_edit, update_demand, min_value=0.025, max_value=5000)
    
    # Add price per kWh field
    price_edit = QLineEdit(str(component.price_per_kwh))
    price_edit.setStyleSheet(INPUT_STYLE)
    properties_manager._set_up_numeric_field(price_edit, lambda value: setattr(component, 'price_per_kwh', value), min_value=0.00)
    
    # Add CAPEX per kW field
    capex_edit = QLineEdit(str(component.capex_per_kw))
    capex_edit.setStyleSheet(INPUT_STYLE)
    
    def update_capex(value):
        setattr(component, 'capex_per_kw', value)
        # Update CAPEX display when CAPEX per kW changes
        properties_manager.main_window.update_capex_display()
        
    properties_manager._set_up_numeric_field(capex_edit, update_capex, min_value=0.00, max_value=100000)
    
    # Add operating mode display (not editable)
    operating_mode_label = QLabel(component.operating_mode)
    operating_mode_label.setStyleSheet("color: white;")
    
    # Check if connected to cloud workload
    connected_to_cloud = properties_manager._is_connected_to_cloud_workload(component)
    
    profile_type = QComboBox()
    profile_type.setStyleSheet(COMBOBOX_STYLE + "QComboBox { width: 125px; }")
    profile_type.addItems(["Data Center", "Sine Wave", "Custom", "Random 8760", "Constant", "Powerlandia 60CF"])
    profile_type.setCurrentText(component.profile_type)
    
    # Disable profile switching if connected to cloud workload
    if connected_to_cloud:
        profile_type.setEnabled(False)
        # Apply a specific style for the disabled state with greyed out text
        disabled_combobox_style = COMBOBOX_STYLE + """
            QComboBox:disabled {
                color: #808080;  /* Grey color */
                background-color: #2A2A2A;  /* Darker background */
                border: 1px solid #444444;  /* Darker border */
            }
        """
        profile_type.setStyleSheet(disabled_combobox_style)
    
    # Create a horizontal layout for profile selection and load button
    profile_layout = QHBoxLayout()
    profile_layout.setContentsMargins(0, 0, 0, 0)
    profile_layout.addWidget(profile_type)
    
    # Add load profile button (only visible for Custom type)
    load_profile_btn = QPushButton("Load Profile")
    load_profile_btn.setStyleSheet(DEFAULT_BUTTON_STYLE)
    load_profile_btn.setVisible(component.profile_type == "Custom")
    load_profile_btn.clicked.connect(lambda: properties_manager._load_custom_profile(component))
    profile_layout.addWidget(load_profile_btn)
    
    # Create a widget to hold the profile layout
    profile_widget = QWidget()
    profile_widget.setLayout(profile_layout)
    
    # Add profile info label
    profile_info = QLabel()
    if component.profile_type == "Custom" and component.profile_name:
        profile_info.setText(f"Loaded: {component.profile_name}")
    elif component.profile_type == "Powerlandia 60CF" and component.profile_name:
        profile_info.setText(f"Loaded: {component.profile_name}")
    elif connected_to_cloud:
        profile_info.setText("<i>Cloud Workload connected</i>")
        profile_info.setStyleSheet("color: #808080;")
    else:
        profile_info.setText("")
    
    # Create data center type selector
    data_center_layout = QHBoxLayout()
    data_center_layout.setContentsMargins(0, 0, 0, 0)
    data_center_type = QComboBox()
    data_center_type.setStyleSheet(COMBOBOX_STYLE)
    data_center_type.addItems(["GPU Dense", "Traditional Cloud", "Crypto ASIC"])
    data_center_type.setCurrentText(component.data_center_type)
    data_center_type.currentTextChanged.connect(lambda text: setattr(component, 'data_center_type', text))
    data_center_layout.addWidget(data_center_type)
    
    # Create a widget to hold the data center type selector
    data_center_widget = QWidget()
    data_center_widget.setLayout(data_center_layout)
    data_center_widget.setVisible(component.profile_type == "Data Center")
    
    # Create data center profile generator button
    dc_generate_layout = QHBoxLayout()
    dc_generate_layout.setContentsMargins(0, 0, 0, 0)
    dc_generate_btn = QPushButton("Generate Data Center Profile")
    dc_generate_btn.setStyleSheet(DEFAULT_BUTTON_STYLE)
    
    def generate_data_center_profile():
        # Clear any existing random profile
        component.random_profile = None
        # Generate new profile based on selected data center type
        component.generate_data_center_profile()
        properties_manager.main_window.update_simulation()
        # Log to terminal instead of popup
        TerminalWidget.log(f"Generated 8760 hours of {component.data_center_type} data center profile.")
    
    dc_generate_btn.clicked.connect(generate_data_center_profile)
    dc_generate_layout.addWidget(dc_generate_btn)
    
    # Create a widget to hold the data center generator controls
    dc_generate_widget = QWidget()
    dc_generate_widget.setLayout(dc_generate_layout)
    dc_generate_widget.setVisible(component.profile_type == "Data Center")
    
    # Create random profile generator controls
    random_profile_layout = QHBoxLayout()
    random_profile_layout.setContentsMargins(0, 0, 0, 0)
    generate_btn = QPushButton("Generate Random Data")
    generate_btn.setStyleSheet(DEFAULT_BUTTON_STYLE)
    
    def generate_random_data():
        # Clear any existing random profile
        component.random_profile = None
        # Generate new profile
        component.generate_random_profile()
        properties_manager.main_window.update_simulation()
        # Log to terminal instead of popup
        TerminalWidget.log(f"Generated 8760 hours of random load data with {int(component.max_ramp_rate * 100)}% max ramp rate.")
    
    generate_btn.clicked.connect(generate_random_data)
    random_profile_layout.addWidget(generate_btn)
    
    # Create a widget to hold the random profile controls
    random_profile_widget = QWidget()
    random_profile_widget.setLayout(random_profile_layout)
    random_profile_widget.setVisible(component.profile_type == "Random 8760")
    
    # Create max ramp rate control for Random 8760 mode
    ramp_rate_layout = QHBoxLayout()
    ramp_rate_layout.setContentsMargins(0, 0, 0, 0)

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
        ramp_rate_value_label.setText(f"{value}%/hr")
        # Don't regenerate while dragging - wait until slider is released

    def regenerate_on_slider_release():
        # Only regenerate when slider is released
        if component.random_profile:
            generate_random_data()

    ramp_rate_slider.valueChanged.connect(update_ramp_rate_from_slider)
    ramp_rate_slider.sliderReleased.connect(regenerate_on_slider_release)

    ramp_rate_layout.addWidget(ramp_rate_slider)
    ramp_rate_layout.addWidget(ramp_rate_value_label)

    # Create a widget to hold the ramp rate controls
    ramp_rate_widget = QWidget()
    ramp_rate_widget.setLayout(ramp_rate_layout)
    ramp_rate_widget.setVisible(component.profile_type == "Random 8760")
    
    # Create time offset control (spinner and slider)
    time_offset_layout = QHBoxLayout()
    time_offset_layout.setContentsMargins(0, 0, 0, 0)
    time_offset_edit = QLineEdit(str(component.time_offset))
    time_offset_edit.setMaximumWidth(50)
    time_offset_edit.setStyleSheet(INPUT_STYLE)
    properties_manager._set_up_numeric_field(time_offset_edit, 
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
        properties_manager.main_window.update_simulation()
    
    time_offset_slider.valueChanged.connect(update_offset_from_slider)
    
    time_offset_layout.addWidget(time_offset_edit)
    time_offset_layout.addWidget(time_offset_slider)
    
    # Create a widget to hold the time offset controls
    time_offset_widget = QWidget()
    time_offset_widget.setLayout(time_offset_layout)
    
    # Create frequency control for Sine Wave mode
    frequency_layout = QHBoxLayout()
    frequency_layout.setContentsMargins(0, 0, 0, 0)
    frequency_edit = QLineEdit(str(component.frequency))
    frequency_edit.setMaximumWidth(50)
    frequency_edit.setStyleSheet(INPUT_STYLE)
    properties_manager._set_up_numeric_field(frequency_edit, 
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
        properties_manager.main_window.update_simulation()
    
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
    time_offset_widget.setVisible(component.profile_type in ["Sine Wave", "Custom", "Powerlandia 60CF"])
    
    def on_profile_changed(text):
        # If connected to a cloud workload, do not allow changing from Data Center
        if connected_to_cloud and component.profile_type == "Data Center" and text != "Data Center":
            # Silently revert back to Data Center
            profile_type.blockSignals(True)
            profile_type.setCurrentText("Data Center")
            profile_type.blockSignals(False)
            return
            
        setattr(component, 'profile_type', text)
        load_profile_btn.setVisible(text == "Custom")
        time_offset_widget.setVisible(text in ["Sine Wave", "Custom", "Powerlandia 60CF"])
        frequency_widget.setVisible(text == "Sine Wave")
        random_profile_widget.setVisible(text == "Random 8760")
        ramp_rate_widget.setVisible(text == "Random 8760")
        data_center_widget.setVisible(text == "Data Center")
        dc_generate_widget.setVisible(text == "Data Center")
        
        # Handle special cases for different profile types
        if text == "Random 8760" and not component.random_profile:
            # Auto-generate random profile when mode is selected
            generate_random_data()
        elif text == "Data Center" and not component.random_profile:
            # Auto-generate data center profile when mode is selected
            generate_data_center_profile()
        elif text == "Powerlandia 60CF":
            # Load the Powerlandia profile
            if not component.powerlandia_profile:
                component.load_powerlandia_profile()
                if component.profile_name:
                    profile_info.setText(f"Loaded: {component.profile_name}")
                properties_manager.main_window.update_simulation()
        elif text != "Custom":
            component.custom_profile = None
            component.profile_name = None
            profile_info.setText("")
    
    profile_type.currentTextChanged.connect(on_profile_changed)
    
    layout.addRow("Demand (MW):", demand_edit)
    layout.addRow("Price per kWh ($):", price_edit)
    layout.addRow("CAPEX per kW ($):", capex_edit)
    layout.addRow("Operating Mode:", operating_mode_label)
    layout.addRow("Demand Mode:", profile_widget)
    layout.addRow("", profile_info)
    layout.addRow("Data Center Type:", data_center_widget)
    layout.addRow("", dc_generate_widget)
    layout.addRow("", random_profile_widget)
    layout.addRow("Max Ramp Rate:", ramp_rate_widget)
    layout.addRow("Time Offset (hr):", time_offset_widget)
    layout.addRow("Frequency:", frequency_widget) 