from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor

class SelectedComponentDisplay(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Set fixed size as specified
        self.setFixedSize(300, 25)
        
        # Set default text with light gray color to match component type color
        self.default_text = '<span style="color: rgb(205, 205, 205);">no component selected</span>'
        self.setText(self.default_text)
        
        # Set text alignment to center
        self.setAlignment(Qt.AlignCenter)
        
        # Apply styling to match properties panel color scheme
        self.setStyleSheet("""
            QLabel {
                background-color: rgba(37, 47, 52, 0.75);
                border: 1px solid rgba(52, 152, 219, 0.75);
                border-radius: 4px;
                padding: 5px;
                font-weight: bold;
                font-size: 12px;
                font-family: Menlo, Consolas, Courier, monospace;
            }
        """)
        
        # Make it click-through for mouse events
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
    
    def set_component_name(self, name):
        """Set the component name to display"""
        self.setText(name)
    
    def update_selected_component(self, component):
        """Update the display based on the selected component"""
        if component:
            # Get component ID string (last 6 digits)
            component_id_str = str(component.component_id)[-6:]
            # Format with HTML colors matching the hover display
            # Component type: light gray (205, 205, 205)
            # ID: darker blue (80, 150, 225)
            display_text = f'<span style="color: rgb(205, 205, 205);">{component.component_type}</span> <span style="color: rgb(80, 150, 225);">{component_id_str}</span>'
            self.setText(display_text)
        else:
            # No component selected, show default text
            self.setText(self.default_text)
    
    def clear_display(self):
        """Clear the display and show default text"""
        self.setText(self.default_text) 