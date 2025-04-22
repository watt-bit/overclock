from PyQt5.QtWidgets import QGraphicsRectItem
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QBrush, QColor, QPen, QRadialGradient

class ComponentBase(QGraphicsRectItem):
    def __init__(self, x, y, width=100, height=60):
        super().__init__(x, y, width, height)
        self.setFlag(QGraphicsRectItem.ItemIsMovable)
        self.setFlag(QGraphicsRectItem.ItemIsSelectable)
        self.setFlag(QGraphicsRectItem.ItemSendsGeometryChanges)
        self.setBrush(QBrush(QColor(200, 200, 200)))
        self.setPen(QPen(Qt.NoPen))
        self.setAcceptHoverEvents(True)
        # Store the original brush for restoration after hover
        self.original_brush = self.brush()
        # List to keep track of connected lines
        self.connections = []
        
        # Shadow properties
        self.shadow_opacity = 0.2  # Shadow transparency (0-1)
        self.shadow_blur = 30      # Shadow blur radius
        self.shadow_y_offset = -90   # Shadow offset from component bottom (reduced from 10)
        
        # Selection highlight pen
        self.selection_pen = QPen(QColor(255, 255, 255), 3, Qt.SolidLine)
        self.selection_pen.setCosmetic(True)  # Keep width constant regardless of zoom
    
    def paint(self, painter, option, widget):
        # Save painter state
        painter.save()
        
        # Draw the shadow first (before the component)
        rect = self.boundingRect()
        
        # Create a shadow ellipse at the bottom of the component
        shadow_width = rect.width() * 0.9    # Shadow slightly narrower than component
        shadow_height = rect.height() * 0.4  # Shadow is flatter (increased from 0.3)
        
        # Position the shadow beneath the component with offset
        shadow_x = rect.x() + (rect.width() - shadow_width) / 2 + 25
        shadow_y = rect.y() + rect.height() - shadow_height / 2 + self.shadow_y_offset
        
        # Create a radial gradient for the shadow
        gradient = QRadialGradient(
            shadow_x + shadow_width / 2,
            shadow_y + shadow_height / 2,
            shadow_width / 2
        )
        gradient.setColorAt(0, QColor(0, 0, 0, int(255 * self.shadow_opacity)))
        gradient.setColorAt(1, QColor(0, 0, 0, 0))
        
        # Draw the shadow
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(int(shadow_x), int(shadow_y), int(shadow_width), int(shadow_height))
        
        # Restore painter to draw the component
        painter.restore()
        
        # Draw the regular component
        super().paint(painter, option, widget)
        
        # If selected, draw white highlight box around the component
        if self.isSelected():
            # Get the bounding rectangle with a small padding
            padding = 4
            highlight_rect = QRectF(
                rect.x() - padding/2,
                rect.y() - padding/2,
                rect.width() + padding,
                rect.height() + padding
            )
            # Save the current painter state
            painter.save()
            # Set up the painter for the highlight
            painter.setPen(self.selection_pen)
            painter.setBrush(Qt.NoBrush)
            # Draw the highlight rectangle
            painter.drawRect(highlight_rect)
            # Restore the painter state
            painter.restore()
    
    def hoverEnterEvent(self, event):
        # Only change cursor if not in connection mode
        if not self.scene() or not hasattr(self.scene(), 'parent') or not self.scene().parent().creating_connection:
            self.setCursor(Qt.PointingHandCursor)
        # Save the original brush and pen for restoring later
        self.original_brush = self.brush()
        self.original_pen = self.pen()
        # Set a semi-transparent ice blue background (alpha 0.1)
        hover_color = QColor(210, 235, 255, 25)  # RGBA where 25 is approx 10% of 255
        self.setBrush(QBrush(hover_color))
        # Add a bright ice blue border with transparency
        border_color = QColor(100, 200, 255, 180)  # Brighter blue with 70% opacity
        hover_pen = QPen(border_color, 2)  # 2px width
        self.setPen(hover_pen)
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        # Only unset cursor if not in connection mode
        if not self.scene() or not hasattr(self.scene(), 'parent') or not self.scene().parent().creating_connection:
            self.unsetCursor()
        # Restore original brush and pen
        if hasattr(self, 'original_brush'):
            self.setBrush(self.original_brush)
        if hasattr(self, 'original_pen'):
            self.setPen(self.original_pen)
        super().hoverLeaveEvent(event)
    
    def mousePressEvent(self, event):
        # Scale up slightly when clicked
        self.setScale(1.05)
        super().mousePressEvent(event)
        if self.scene() and hasattr(self.scene(), 'component_clicked'):
            self.scene().component_clicked.emit(self)
    
    def mouseReleaseEvent(self, event):
        # Restore original scale
        self.setScale(1.0)
        super().mouseReleaseEvent(event)
    
    def itemChange(self, change, value):
        if change == QGraphicsRectItem.ItemPositionChange:
            # Update all connected lines
            for connection in self.connections:
                connection.update_position()
        elif change == QGraphicsRectItem.ItemSelectedChange:
            # Force a repaint when selection state changes
            self.update()
        return super().itemChange(change, value) 