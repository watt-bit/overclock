from PyQt5.QtWidgets import (QLabel, QComboBox, QLineEdit, QWidget, QFormLayout, QHBoxLayout, QSlider)
from PyQt5.QtCore import Qt

# Import styles from the parent module
from src.ui.properties_manager import COMBOBOX_STYLE, INPUT_STYLE, SLIDER_STYLE

def add_cloud_workload_properties(properties_manager, component, layout):
    """Add properties for CloudWorkloadComponent"""
    # Add note label
    note_label = QLabel("NOTE: Cloud Workload component only connects\nto Load component in Data Center demand mode.")
    note_label.setStyleSheet("background-color: transparent; color: rgba(200, 255, 255, 0.9); padding: 4px; border-radius: 4px;")
    note_label.setAlignment(Qt.AlignCenter)
    note_label.setWordWrap(False)
    
    # Add operating mode selector
    mode_selector = QComboBox()
    mode_selector.setStyleSheet(COMBOBOX_STYLE + "QComboBox { width: 150px; }")
    mode_selector.addItems(["No Customer", "Multi-Cloud Spot", "Dedicated Capacity"])
    mode_selector.setCurrentText(component.operating_mode)
    
    # Create a container for resource parameters that will only be visible in Multi-Cloud Spot mode
    multi_cloud_params_widget = QWidget()
    multi_cloud_params_layout = QFormLayout(multi_cloud_params_widget)
    multi_cloud_params_layout.setContentsMargins(10, 10, 10, 10)
    
    # Add traditional cloud parameters
    trad_params_label = QLabel(f"Power: {component.traditional_cloud_power} kW\nPrice: ${component.traditional_cloud_price:.2f}")
    multi_cloud_params_layout.addRow("Traditional Cloud:", trad_params_label)
    
    # Add GPU Dense parameters
    gpu_params_label = QLabel(f"Power: {component.gpu_intensive_power} kW\nPrice: ${component.gpu_intensive_price:.2f}")
    multi_cloud_params_layout.addRow("GPU Dense:", gpu_params_label)
    
    # Add crypto ASIC parameters
    crypto_params_label = QLabel(f"Power: {component.crypto_asic_power} kW\nPrice: ${component.crypto_asic_price:.2f}")
    multi_cloud_params_layout.addRow("Crypto ASIC:", crypto_params_label)
    
    # Create a container for dedicated capacity parameters
    dedicated_params_widget = QWidget()
    dedicated_params_layout = QFormLayout(dedicated_params_widget)
    dedicated_params_layout.setContentsMargins(10, 10, 10, 10)
    
    # Add power per resource field
    power_per_resource_edit = QLineEdit(str(component.dedicated_power_per_resource))
    power_per_resource_edit.setStyleSheet(INPUT_STYLE)
    properties_manager._set_up_numeric_field(
        power_per_resource_edit, 
        lambda value: setattr(component, 'dedicated_power_per_resource', value),
        min_value=0.05,
        max_value=100.0
    )
    dedicated_params_layout.addRow("Power per Resource (kW):", power_per_resource_edit)
    
    # Add power use efficiency slider
    efficiency_layout = QHBoxLayout()
    efficiency_layout.setContentsMargins(0, 0, 0, 0)
    
    efficiency_slider = QSlider(Qt.Horizontal)
    efficiency_slider.setMinimum(100)  # 1.0
    efficiency_slider.setMaximum(200)  # 2.0
    efficiency_slider.setValue(int(component.dedicated_power_use_efficiency * 100))
    efficiency_slider.setStyleSheet(SLIDER_STYLE)
    
    efficiency_label = QLabel(f"{component.dedicated_power_use_efficiency:.2f}")
    
    def update_efficiency(value):
        component.dedicated_power_use_efficiency = value / 100.0
        efficiency_label.setText(f"{component.dedicated_power_use_efficiency:.2f}")
        component.update()
    
    efficiency_slider.valueChanged.connect(update_efficiency)
    efficiency_layout.addWidget(efficiency_slider)
    efficiency_layout.addWidget(efficiency_label)
    
    efficiency_widget = QWidget()
    efficiency_widget.setLayout(efficiency_layout)
    dedicated_params_layout.addRow("Power Use Efficiency:", efficiency_widget)
    
    # Add price per resource hour field
    price_per_resource_edit = QLineEdit(str(component.dedicated_price_per_resource))
    price_per_resource_edit.setStyleSheet(INPUT_STYLE)
    properties_manager._set_up_numeric_field(
        price_per_resource_edit, 
        lambda value: setattr(component, 'dedicated_price_per_resource', value),
        min_value=0.00,
        max_value=10.0
    )
    dedicated_params_layout.addRow("Price per Resource Hour ($):", price_per_resource_edit)
    
    # Add revenue display to both parameter widgets
    revenue_label = QLabel(f"${component.accumulated_revenue:.2f}")
    revenue_label.setStyleSheet("font-weight: bold;")
    
    # Create a separate label for multi-cloud params
    multi_cloud_revenue_label = QLabel(f"${component.accumulated_revenue:.2f}")
    multi_cloud_revenue_label.setStyleSheet("font-weight: bold;")
    
    multi_cloud_params_layout.addRow("Accumulated Revenue:", multi_cloud_revenue_label)
    dedicated_params_layout.addRow("Accumulated Revenue:", revenue_label)
    
    # Set left alignment for all labels in the forms
    multi_cloud_params_layout.setLabelAlignment(Qt.AlignLeft)
    multi_cloud_params_layout.setFormAlignment(Qt.AlignLeft | Qt.AlignTop)
    dedicated_params_layout.setLabelAlignment(Qt.AlignLeft)
    dedicated_params_layout.setFormAlignment(Qt.AlignLeft | Qt.AlignTop)
    
    # Set visibility based on current mode
    multi_cloud_params_widget.setVisible(component.operating_mode == "Multi-Cloud Spot")
    dedicated_params_widget.setVisible(component.operating_mode == "Dedicated Capacity")
    
    # Connect mode selector to update component and UI
    def on_mode_changed(text):
        component.operating_mode = text
        component.update()
        # Show/hide appropriate parameters based on mode
        multi_cloud_params_widget.setVisible(text == "Multi-Cloud Spot")
        dedicated_params_widget.setVisible(text == "Dedicated Capacity")
        # Reset accumulated revenue when switching modes
        if text != component.operating_mode:
            component.accumulated_revenue = 0.0
            revenue_label.setText(f"${component.accumulated_revenue:.2f}")
            multi_cloud_revenue_label.setText(f"${component.accumulated_revenue:.2f}")
    
    mode_selector.currentTextChanged.connect(on_mode_changed)
    layout.addRow("Operating Mode:", mode_selector)
    layout.addRow("", multi_cloud_params_widget)
    layout.addRow("", dedicated_params_widget)
    layout.addRow(note_label) 