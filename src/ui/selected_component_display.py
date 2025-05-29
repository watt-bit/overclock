from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor

class SelectedComponentDisplay(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Set fixed size as specified
        self.setFixedSize(300, 25)
        
        # Set default text with light gray color to match component type color
        self.default_text = 'no component selected'
        self.setText(self.default_text)
        
        # Apply styling to match properties panel color scheme with hover/pressed states like open button
        self.setStyleSheet("""
            QPushButton {
                background-color: rgba(37, 47, 52, 0.75);
                border: 1px solid rgba(52, 152, 219, 0.75);
                border-radius: 4px;
                padding: 5px;
                font-weight: bold;
                font-size: 12px;
                font-family: Menlo, Consolas, Courier, monospace;
                text-align: center;
                color: rgba(255, 255, 255, 0.8);
            }
            QPushButton:hover {
                background-color: #3498db;
                border: 1px solid #3498db;
            }
            QPushButton:pressed {
                background-color: #2C80B4;
                border: 1px solid #2C80B4;
            }
            QPushButton:disabled {
                background-color: rgba(37, 47, 52, 0.75);
                border: 1px solid rgba(52, 152, 219, 0.75);
                color: rgba(205, 205, 205, 0.6);
            }
        """)
        
        # Store reference to currently selected component
        self.selected_component = None
        
        # Connect click to open properties
        self.clicked.connect(self.open_properties_panel)
        
        # Initially disabled since no component is selected
        self.setEnabled(False)
    
    def set_component_name(self, name):
        """Set the component name to display"""
        self.setText(name)
    
    def update_selected_component(self, component):
        """Update the display based on the selected component"""
        self.selected_component = component
        
        if component:
            # Get component ID string (last 6 digits)
            component_id_str = str(component.component_id)[-6:]
            # Use plain text format since QPushButton doesn't support rich text
            display_text = f'{component.component_type} {component_id_str}'
            self.setText(display_text)
            self.setEnabled(True)
            self.setToolTip("Click to open properties panel")
        else:
            # No component selected, show default text
            self.setText(self.default_text)
            self.setEnabled(False)
            self.setToolTip("")
    
    def clear_display(self):
        """Clear the display and show default text"""
        self.selected_component = None
        self.setText(self.default_text)
        self.setEnabled(False)
        self.setToolTip("")
    
    def open_properties_panel(self):
        """Open the properties panel for the selected component"""
        if self.selected_component and hasattr(self.selected_component, 'open_properties'):
            self.selected_component.open_properties() 