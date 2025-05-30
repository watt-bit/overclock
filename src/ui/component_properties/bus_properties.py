from PyQt6.QtWidgets import (QLineEdit, QLabel, QPushButton)
from PyQt6.QtCore import Qt

# Import styles from the parent module
from src.ui.properties_manager import COMMON_BUTTON_STYLE, INPUT_STYLE

def add_bus_properties(properties_manager, component, layout):
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
    
    if has_loads:
        # Normal styling when enabled
        state_toggle.setStyleSheet(
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
        """ if component.is_on 
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
    else:
        # Disabled styling when no loads connected
        state_toggle.setStyleSheet(
            COMMON_BUTTON_STYLE + """
            QPushButton { 
                background-color: #185D18; 
                color: #888888; 
                font-weight: bold; 
                font-size: 14px; 
            }
            QPushButton:disabled { 
                background-color: #185D18; 
                color: #888888; 
            }
        """)
    
    # Enable or disable based on load connections
    state_toggle.setEnabled(has_loads)
    
    # Add tooltip explaining why it might be disabled
    if not has_loads:
        state_toggle.setToolTip("On/Off switch is disabled because this bus has no connected loads.")
        # Force bus to be on if it has no loads
        if not component.is_on:
            component.is_on = True
            state_toggle.setText("ON")
            # Apply disabled styling since it's forced to be disabled
            state_toggle.setStyleSheet(
                COMMON_BUTTON_STYLE + """
                QPushButton { 
                    background-color: #185D18; 
                    color: #888888; 
                    font-weight: bold; 
                    font-size: 14px; 
                }
                QPushButton:disabled { 
                    background-color: #185D18; 
                    color: #888888; 
                }
            """)
            component.update()  # Redraw the component
    else:
        state_toggle.setToolTip("Toggle power to connected loads.")
    
    def toggle_state():
        # Only allow toggling if there are connected loads
        if component.has_load_connections():
            component.is_on = not component.is_on
            state_toggle.setText("ON" if component.is_on else "OFF")
            state_toggle.setStyleSheet(
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
    """ if component.is_on 
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
            properties_manager.main_window.update_simulation()  # Update the simulation state
    
    state_toggle.clicked.connect(toggle_state)
    layout.addRow("Load State:", state_toggle) 