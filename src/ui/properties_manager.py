from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QSlider, QFileDialog, QFormLayout, 
                            QLineEdit, QComboBox, QSizePolicy, QDialog)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDoubleValidator, QIntValidator, QPixmap
import csv
import re
import os

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
from src.components.traditional_data_center import TraditionalDataCenterComponent
from src.components.cloud_workload import CloudWorkloadComponent
from src.components.solar_panel import SolarPanelComponent
from src.components.wind_turbine import WindTurbineComponent
from src.components.distribution_pole import DistributionPoleComponent
from src.utils.resource import resource_path

# Define common styles
COMMON_BUTTON_STYLE = "QPushButton { border: 1px solid #777777; border-radius: 3px; padding: 1px; }"
DEFAULT_BUTTON_STYLE = "QPushButton { background-color: rgba(37, 47, 52, 0.75); color: white; border: 1px solid #777777; border-radius: 3px; padding: 1px; }"
SLIDER_STYLE = "QSlider::groove:horizontal { background: rgba(37, 47, 52, 0.75); height: 8px; border-radius: 4px; } " \
              "QSlider::handle:horizontal { background: #777777; width: 16px; margin: -4px 0; border-radius: 8px; }"
COMBOBOX_STYLE = "QComboBox { background-color: rgba(37, 47, 52, 0.75); color: white; border: 1px solid #777777; border-radius: 3px; padding: 1px; }"
INPUT_STYLE = "QLineEdit { background-color: rgba(37, 47, 52, 0.75); color: white; border: 1px solid #777777; border-radius: 3px; padding: 1px; }"
LINEEDIT_STYLE = "QLineEdit { background-color: rgba(37, 47, 52, 0.75); color: white; border: 1px solid #777777; border-radius: 3px; padding: 1px; }"

class ComponentPropertiesManager:
    def __init__(self, main_window):
        self.main_window = main_window
        self.properties_widget = QWidget()
        self.properties_widget.setStyleSheet('color: white; background-color: rgba(37, 47, 52, 0.75); border: none; font-family: Menlo, Consolas, Courier, monospace; font-size: 10px; border-radius: 3px;')
        # Set size policies to have fixed width but allow height to adjust to contents
        self.properties_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        # Set fixed width to match the dock widget width
        self.properties_widget.setFixedWidth(300)
        self.properties_layout = QFormLayout(self.properties_widget)
        # Set layout margins to be minimal
        self.properties_layout.setContentsMargins(10, 10, 10, 10)
        # Set left alignment for all labels in the form
        self.properties_layout.setLabelAlignment(Qt.AlignLeft)
        self.properties_layout.setFormAlignment(Qt.AlignLeft | Qt.AlignTop)
        # Initialize current_component attribute
        self.current_component = None
        # Initialize delete_btn attribute
        self.delete_btn = None
    
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
        
        # Update the component's properties_open state if there's a current component
        if self.current_component and hasattr(self.current_component, 'set_properties_panel_state'):
            self.current_component.set_properties_panel_state(False)
        
        # Clear the current component reference
        self.current_component = None
        
        # Clear the delete button reference
        if hasattr(self, 'delete_btn'):
            self.delete_btn = None
        
        # Force the properties dock to resize to its minimum size
        self.properties_widget.adjustSize()
        self.main_window.properties_dock.adjustSize()
    
    def show_component_properties(self, component):
        """Display the properties for the selected component"""
        # Only show properties if not in connection mode
        if self.main_window.creating_connection:
            return
            
        # Clear existing properties
        while self.properties_layout.count():
            item = self.properties_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.current_component = component
        
        # Make properties panel visible if it's currently hidden
        if not self.main_window.properties_dock.isVisible():
            self.main_window.properties_dock.setVisible(True)
        
        # Update the component's properties_open state
        if hasattr(component, 'set_properties_panel_state'):
            component.set_properties_panel_state(True)
        
        # Create a vertical layout for the component properties
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)  # Reduce margins
        
        # Create the main content area (previously left column)
        content_layout = QFormLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)  # Minimal margins
        content_layout.setLabelAlignment(Qt.AlignLeft)
        content_layout.setFormAlignment(Qt.AlignLeft | Qt.AlignTop)
        
        # Create bottom button area
        bottom_layout = QVBoxLayout()
        bottom_layout.setContentsMargins(0, 10, 0, 0)  # Add some top padding
        
        # Add delete button to bottom layout
        delete_btn = QPushButton("Delete (DEL)")
        delete_btn.setStyleSheet(COMMON_BUTTON_STYLE + """
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
        delete_btn.clicked.connect(self.delete_component)
        
        # Store reference to delete button for later enabling/disabling
        self.delete_btn = delete_btn
        
        # Disable delete button if simulation is running or autocompleting
        self.update_delete_button_state()
        
        bottom_layout.addWidget(delete_btn)
        
        # Add graphics toggle button for load components only
        if isinstance(component, LoadComponent):
            graphics_toggle = QPushButton("Graphics " + ("ON" if component.graphics_enabled else "OFF"))
            graphics_toggle.setStyleSheet(
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
        """ if component.graphics_enabled 
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
            
            def toggle_graphics():
                component.graphics_enabled = not component.graphics_enabled
                graphics_toggle.setText("Graphics " + ("ON" if component.graphics_enabled else "OFF"))
                graphics_toggle.setStyleSheet(
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
        """ if component.graphics_enabled 
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
                component.update()  # Redraw the component
            
            graphics_toggle.clicked.connect(toggle_graphics)
            graphics_toggle.setToolTip("Toggle visibility of the load component's image")
            bottom_layout.addWidget(graphics_toggle)
        
        # Add component-specific properties to the content layout
        if isinstance(component, BusComponent):
            self._add_bus_properties(component, content_layout)
        elif isinstance(component, GeneratorComponent):
            self._add_generator_properties(component, content_layout)
        elif isinstance(component, GridImportComponent):
            self._add_grid_import_properties(component, content_layout)
        elif isinstance(component, GridExportComponent):
            self._add_grid_export_properties(component, content_layout)
        elif isinstance(component, LoadComponent):
            self._add_load_properties(component, content_layout)
        elif isinstance(component, BatteryComponent):
            self._add_battery_properties(component, content_layout)
        elif isinstance(component, CloudWorkloadComponent):
            self._add_cloud_workload_properties(component, content_layout)
        elif isinstance(component, SolarPanelComponent):
            self._add_solar_panel_properties(component, content_layout)
        elif isinstance(component, WindTurbineComponent):
            self._add_wind_turbine_properties(component, content_layout)
        elif isinstance(component, TreeComponent):
            # Trees are decorative with no functional properties
            tree_info = QLabel("Tree Prop")
            content_layout.addRow(tree_info)
        elif isinstance(component, BushComponent):
            # Bushes are decorative with no functional properties
            bush_info = QLabel("Bush Prop")
            content_layout.addRow(bush_info)
        elif isinstance(component, PondComponent):
            # Ponds are decorative with no functional properties
            pond_info = QLabel("Pond Prop")
            content_layout.addRow(pond_info)
        elif isinstance(component, House1Component):
            # Houses are decorative with no functional properties
            house1_info = QLabel("House Prop")
            content_layout.addRow(house1_info)
        elif isinstance(component, House2Component):
            # Houses are decorative with no functional properties
            house2_info = QLabel("Greenhouse Prop")
            content_layout.addRow(house2_info)
        elif isinstance(component, FactoryComponent):
            # Factories are decorative with no functional properties
            factory_info = QLabel("Factory Prop")
            content_layout.addRow(factory_info)
        elif isinstance(component, TraditionalDataCenterComponent):
            # Traditional Data Centers are decorative with no functional properties
            trad_dc_info = QLabel("Traditional Data Center Prop")
            content_layout.addRow(trad_dc_info)
        elif isinstance(component, DistributionPoleComponent):
            # Distribution Poles are decorative with no functional properties
            pole_info = QLabel("Distribution Pole Prop")
            content_layout.addRow(pole_info)
        else:
            # Add default message
            default_info = QLabel("No specific properties available for this component type")
            content_layout.addRow(default_info)
        
        # Create content widget to hold the form layout
        content_widget = QWidget()
        content_widget.setLayout(content_layout)
        
        # Create button widget to hold the bottom layout
        bottom_widget = QWidget()
        bottom_widget.setLayout(bottom_layout)
        
        # Add the content and button widgets to the main layout
        main_layout.addWidget(content_widget)
        main_layout.addWidget(bottom_widget)
        
        # Create a widget to hold the main layout
        main_widget = QWidget()
        main_widget.setLayout(main_layout)
        
        # Add the main widget to the properties layout
        self.properties_layout.addRow(main_widget)
        
        # Force the properties dock to resize to its minimum size
        self.properties_widget.adjustSize()
        self.main_window.properties_dock.adjustSize()
    
    def update_delete_button_state(self):
        """
        Update the state of the delete button based on simulation status.
        Disables the button when simulation is running or in autocomplete mode.
        """
        if hasattr(self, 'delete_btn') and self.delete_btn is not None:
            # Check if the button is still a valid widget
            try:
                # Test if the widget is still valid by checking a property
                _ = self.delete_btn.isEnabled()
                
                # Only proceed if we didn't get an exception
                is_running = self.main_window.simulation_engine.simulation_running
                is_autocompleting = self.main_window.is_autocompleting
                
                self.delete_btn.setEnabled(not (is_running or is_autocompleting))
                
                # Update button appearance based on enabled state
                if not self.delete_btn.isEnabled():
                    self.delete_btn.setStyleSheet(COMMON_BUTTON_STYLE + "QPushButton { background-color: #888888; color: #DDDDDD; font-weight: bold; }")
                else:
                    self.delete_btn.setStyleSheet(COMMON_BUTTON_STYLE + """
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
            except (RuntimeError, Exception):
                # The widget has been deleted or is otherwise invalid
                # Remove our reference to it
                self.delete_btn = None
    
    def _add_bus_properties(self, component, layout):
        from src.ui.component_properties.bus_properties import add_bus_properties
        add_bus_properties(self, component, layout)
    
    def _add_generator_properties(self, component, layout):
        from src.ui.component_properties.generator_properties import add_generator_properties
        add_generator_properties(self, component, layout)
    
    def _add_grid_import_properties(self, component, layout):
        from src.ui.component_properties.grid_import_properties import add_grid_import_properties
        add_grid_import_properties(self, component, layout)
    
    def _add_grid_export_properties(self, component, layout):
        from src.ui.component_properties.grid_export_properties import add_grid_export_properties
        add_grid_export_properties(self, component, layout)

    
    def _is_connected_to_cloud_workload(self, load_component):
        """Check if a load component is connected to a cloud workload component
        
        Args:
            load_component: The load component to check
            
        Returns:
            bool: True if connected to a cloud workload, False otherwise
        """
        if not isinstance(load_component, LoadComponent):
            return False
            
        for connection in load_component.connections:
            if isinstance(connection.source, CloudWorkloadComponent):
                return True
            if isinstance(connection.target, CloudWorkloadComponent):
                return True
        return False
    
    def _add_load_properties(self, component, layout):
        from src.ui.component_properties.load_properties import add_load_properties
        add_load_properties(self, component, layout)
    
    def _add_battery_properties(self, component, layout):
        from src.ui.component_properties.battery_properties import add_battery_properties
        add_battery_properties(self, component, layout)
    
    def _add_cloud_workload_properties(self, component, layout):
        from src.ui.component_properties.cloud_workload_properties import add_cloud_workload_properties
        add_cloud_workload_properties(self, component, layout)
    
    def _add_solar_panel_properties(self, component, layout):
        from src.ui.component_properties.solar_panel_properties import add_solar_panel_properties
        add_solar_panel_properties(self, component, layout)
    
    def _add_wind_turbine_properties(self, component, layout):
        from src.ui.component_properties.wind_turbine_properties import add_wind_turbine_properties
        add_wind_turbine_properties(self, component, layout)
    
    def _show_csv_format_dialog(self):
        """Show a dialog explaining the expected CSV format for load profiles"""
        dialog = QDialog(self.main_window)
        dialog.setWindowTitle("Load Custom Profile")
        dialog.setModal(True)
        dialog.setFixedSize(350, 400)
        
        # Match the properties panel styling
        dialog.setStyleSheet('''
            QDialog {
                background-color: rgba(37, 47, 52, 0.95);
                color: white;
                font-family: Menlo, Consolas, Courier, monospace;
                font-size: 10px;
                border: 1px solid #777777;
                border-radius: 3px;
            }
            QLabel {
                color: white;
                background: transparent;
            }
            QPushButton {
                background-color: rgba(37, 47, 52, 0.75);
                color: white;
                border: 1px solid #777777;
                border-radius: 3px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #227D22;
            }
            QPushButton:pressed {
                background-color: #103D10;
            }
        ''')
        
        # Create main layout
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Add spreadsheet image
        image_label = QLabel()
        image_path = resource_path("src/ui/assets/spreadsheet.png")
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            # Scale to 200x200 while maintaining aspect ratio
            scaled_pixmap = pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            image_label.setPixmap(scaled_pixmap)
        else:
            image_label.setText("📊 Spreadsheet")
            image_label.setStyleSheet("font-size: 48px;")
        
        image_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(image_label)
        
        # Add format explanation
        format_text = QLabel(
            "Expected CSV Format for OVERCLOCK:\n\n"
            "• 1 header row\n"
            "• 8760 data rows (one for each hour of the year)\n"
            "• Each row contains a capacity or load factor\n"
            "• Values must be between 0.0 and 1.0\n\n"
            "\n"
            "\n"
            "\n"
        )
        format_text.setAlignment(Qt.AlignLeft)
        format_text.setWordWrap(True)
        format_text.setStyleSheet("font-size: 11px; line-height: 1.4;")
        layout.addWidget(format_text)
        
        # Add OK button
        ok_button = QPushButton("Continue to File Selector")
        ok_button.clicked.connect(dialog.accept)
        layout.addWidget(ok_button)
        
        # Show dialog and return result
        return dialog.exec_() == QDialog.Accepted

    def _load_custom_profile(self, component):
        # Show format explanation dialog first
        if not self._show_csv_format_dialog():
            return  # User cancelled the dialog
            
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
                
                # Refresh properties panel to show loaded profile name
                self.show_component_properties(component)
                
                # Log success message to terminal
                from src.ui.terminal_widget import TerminalWidget
                TerminalWidget.log(f"Profile Loaded: Loaded {len(data)} time steps from {component.profile_name}")
            
            except Exception as e:
                # Log error message to terminal
                from src.ui.terminal_widget import TerminalWidget
                TerminalWidget.log(f"Error Loading Profile: {str(e)}")
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
            # Use the component deleter to handle deletion
            self.main_window.component_deleter.delete_component(component)
            
            # Clear the current component reference to prevent repeated deletion attempts
            self.current_component = None 