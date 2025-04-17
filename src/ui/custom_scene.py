from PyQt5.QtWidgets import QGraphicsScene
from PyQt5.QtCore import QObject, pyqtSignal, QPointF
from PyQt5.QtGui import QPen, QPixmap, QColor, QBrush


class CustomScene(QGraphicsScene, QObject):
    component_clicked = pyqtSignal(object)
    
    def __init__(self):
        QGraphicsScene.__init__(self)
        QObject.__init__(self)
        
        # Load the background image
        self.background_image = QPixmap("src/ui/assets/background.png")
        # Set the background brush to tile the image
        if not self.background_image.isNull():
            self.setBackgroundBrush(QBrush(self.background_image))
        
        # Background mode: 0 = image1, 1 = image2, 2 = solid color
        self.background_mode = 0
        # Grey color for solid background matching other windows
        self.background_color = QColor("#1E1E1E")
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release events on the scene background"""
        items = self.items(event.scenePos())
        if not items:
            # If clicked on empty space (no items at the position)
            if hasattr(self, 'parent') and self.parent() and hasattr(self.parent(), 'properties_manager'):
                # Clear the properties panel
                self.parent().properties_manager.clear_properties_panel()
                # Also hide the properties panel
                if hasattr(self.parent(), 'properties_dock'):
                    self.parent().properties_dock.setVisible(False)
        super().mouseReleaseEvent(event)
    
    def set_background(self, mode):
        """Change the background based on the specified mode
        mode: 0 = image1, 1 = image2, 2 = solid color
        """
        self.background_mode = mode
        
        if mode == 0:
            # Background 1 (default texture)
            self.background_image = QPixmap("src/ui/assets/background.png")
            if not self.background_image.isNull():
                self.setBackgroundBrush(QBrush(self.background_image))
        elif mode == 1:
            # Background 2 (alternate texture)
            self.background_image = QPixmap("src/ui/assets/background2.png")
            if not self.background_image.isNull():
                self.setBackgroundBrush(QBrush(self.background_image))
        elif mode == 2:
            # Solid color background
            self.setBackgroundBrush(QBrush(self.background_color))
        
        self.update()
    
    def drawBackground(self, painter, rect):
        # Call the base implementation to clear the background
        super().drawBackground(painter, rect)
        
        # If using solid color, draw dotted gridlines
        if self.background_mode == 2:
            # Set up a dotted pen for the grid
            gridPen = QPen(QColor(80, 80, 80, 180))  # Less transparent grey (alpha increased from 100 to 180)
            # Use custom dash pattern for sparser dashes: [dash length, space length]
            gridPen.setDashPattern([8, 12])  # Longer dashes with more space between them
            gridPen.setWidth(2)
            painter.setPen(gridPen)
            
            # Grid size (200x200 pixels)
            grid_size = 200
            
            # Calculate the grid based on the view rect
            left = int(rect.left()) - (int(rect.left()) % grid_size)
            top = int(rect.top()) - (int(rect.top()) % grid_size)
            
            # Draw vertical grid lines
            for x in range(left, int(rect.right()) + grid_size, grid_size):
                painter.drawLine(QPointF(x, rect.top()), QPointF(x, rect.bottom()))
                
            # Draw horizontal grid lines  
            for y in range(top, int(rect.bottom()) + grid_size, grid_size):
                painter.drawLine(QPointF(rect.left(), y), QPointF(rect.right(), y))
                
            return
            
        # Only proceed with background drawing if we have a valid background image
        if self.background_image.isNull():
            return
            
        # Tile size (300x300 pixels at 1x resolution)
        tile_size = 200
        
        # Calculate the grid based on the view rect
        left = int(rect.left()) - (int(rect.left()) % tile_size)
        top = int(rect.top()) - (int(rect.top()) % tile_size)
        
        # Draw the tiled background
        for x in range(left, int(rect.right()) + tile_size, tile_size):
            for y in range(top, int(rect.bottom()) + tile_size, tile_size):
                painter.drawPixmap(x, y, tile_size, tile_size, self.background_image) 