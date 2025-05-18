from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit, QHBoxLayout, QPushButton, QSizePolicy
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class TerminalWidget(QWidget):
    """A simple terminal-like widget that displays status messages"""
    
    # Class variable to store the global instance
    _instance = None
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # Set this instance as the global instance
        TerminalWidget._instance = self
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the terminal UI elements"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # Create a header layout
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create a terminal label that floats above the text area
        terminal_label = QLabel("Terminal")
        terminal_label.setStyleSheet("QLabel { color: white; font-weight: bold; font-size: 10px; padding-bottom: 2px; }")
        header_layout.addWidget(terminal_label)
        
        # Add spacer to push the button to the right
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        header_layout.addWidget(spacer)
        
        # Add a clear button
        clear_button = QPushButton("+")
        clear_button.setToolTip("New terminal")
        clear_button.setFixedSize(20, 20)
        clear_button.setStyleSheet("""
            QPushButton {
                color: #AAAAAA;
                font-weight: bold;
                font-size: 14px;
                background-color: transparent;
                border: none;
            }
            QPushButton:hover {
                color: #FFFFFF;
            }
            QPushButton:pressed {
                color: #888888;
            }
        """)
        clear_button.clicked.connect(self.clear)
        header_layout.addWidget(clear_button)
        
        # Add header layout to main layout
        layout.addLayout(header_layout)
        
        # Create the terminal text area
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        
        # Set a fixed-width font
        fixed_font = QFont("Courier", 10)
        self.text_area.setFont(fixed_font)
        
        # Style the text area to look like a terminal
        self.text_area.setStyleSheet("""
            QTextEdit {
                background-color: #121212;
                color: #AAAAAA;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 5px;
            }
        """)
        
        # Add widget to layout
        layout.addWidget(self.text_area)
        
    def add_message(self, message):
        """Add a message to the terminal"""
        # Simply append the message
        self.text_area.append(f'<div>{message}</div>')
            
        # Scroll to the bottom to show the most recent message
        self.text_area.verticalScrollBar().setValue(
            self.text_area.verticalScrollBar().maximum()
        )
        
    def clear(self):
        """Clear all messages from the terminal"""
        self.text_area.clear()
        
    @staticmethod
    def log(message):
        """Static method to add a message to the terminal from anywhere
        
        Args:
            message (str): The message to display in the terminal
        """
        if TerminalWidget._instance:
            TerminalWidget._instance.add_message(message) 