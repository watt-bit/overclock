from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGraphicsScene
from PyQt5.QtGui import QColor, QBrush

class HistorianManager:
    """
    Manager for the Historian view content.
    Handles creation and management of the historian scene.
    """
    
    def __init__(self, parent):
        """
        Initialize the historian manager
        
        Args:
            parent: Reference to the main window
        """
        self.parent = parent
        self.historian_scene = None
        self.initialize_historian_scene()
    
    def initialize_historian_scene(self):
        """
        Create the historian scene with a dark grey background
        """
        self.historian_scene = QGraphicsScene()
        
        # Set dark grey background
        background_color = QColor("#2D2D2D")
        self.historian_scene.setBackgroundBrush(QBrush(background_color)) 