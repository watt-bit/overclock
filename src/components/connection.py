from PyQt5.QtWidgets import QGraphicsLineItem
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPen, QColor
import math

class Connection(QGraphicsLineItem):
    # Static variables for synchronized animation
    animation_time = 0
    oscillation_speed = 0.2
    animation_timer = None
    active_connections = []
    
    @classmethod
    def update_all_connections(cls):
        # Update shared animation time
        cls.animation_time += cls.oscillation_speed
        # Update all active connections, removing any that are no longer valid
        invalid_connections = []
        for connection in cls.active_connections:
            try:
                connection.update_animation()
            except RuntimeError:
                invalid_connections.append(connection)
        
        # Remove any invalid connections
        for conn in invalid_connections:
            if conn in cls.active_connections:
                cls.active_connections.remove(conn)
        
        # Stop timer if no valid connections remain
        if not cls.active_connections and cls.animation_timer:
            cls.animation_timer.stop()
            cls.animation_timer = None
            cls.animation_time = 0
    
    def __init__(self, source, target):
        super().__init__()
        self.source = source
        self.target = target
        
        # Create yellow dashed pen with wider line
        pen = QPen(QColor(255, 215, 0), 3)  # Golden yellow, 3px wide
        pen.setStyle(Qt.DashLine)
        pen.setDashPattern([8, 4])  # 8px dash, 4px gap
        self.setPen(pen)
        
        # Make sure the line is behind the components
        self.setZValue(-1)
        
        # Add this connection to both components' lists
        self.source.connections.append(self)
        self.target.connections.append(self)
        
        # Add to active connections list
        Connection.active_connections.append(self)
        
        # Initialize the shared timer if it doesn't exist
        if Connection.animation_timer is None:
            Connection.animation_timer = QTimer()
            Connection.animation_timer.timeout.connect(Connection.update_all_connections)
            Connection.animation_timer.start(50)  # Update every 50ms
        
        self.update_position()
    
    def update_animation(self):
        # Use sine wave to create smooth back-and-forth motion
        self.dash_offset = 6 * math.sin(Connection.animation_time)  # 6 is amplitude of motion
        
        # Create new pen with updated dash offset
        pen = self.pen()
        pen.setDashOffset(self.dash_offset)
        self.setPen(pen)
    
    def cleanup(self):
        """Remove this connection from both components and stop animation"""
        if self in Connection.active_connections:
            Connection.active_connections.remove(self)
        
        # If this is the last connection, stop and clear the timer
        if not Connection.active_connections and Connection.animation_timer:
            Connection.animation_timer.stop()
            Connection.animation_timer = None
            Connection.animation_time = 0
        
        if self.source and self in self.source.connections:
            self.source.connections.remove(self)
        if self.target and self in self.target.connections:
            self.target.connections.remove(self)
        self.source = None
        self.target = None
    
    def setup_component_tracking(self):
        """No longer needed as we're using itemChange now"""
        pass
    
    def update_position(self):
        if not (self.source and self.target):
            return
            
        try:
            source_rect = self.source.sceneBoundingRect()
            target_rect = self.target.sceneBoundingRect()
            
            source_center = source_rect.center()
            target_center = target_rect.center()
            
            self.setLine(source_center.x(), source_center.y(), 
                        target_center.x(), target_center.y())
        except RuntimeError:
            # Handle case where C++ objects have been deleted
            if self in Connection.active_connections:
                Connection.active_connections.remove(self)
            
            # Clean up any references we can
            if hasattr(self, 'source') and self.source and hasattr(self.source, 'connections') and self in self.source.connections:
                self.source.connections.remove(self)
            if hasattr(self, 'target') and self.target and hasattr(self.target, 'connections') and self in self.target.connections:
                self.target.connections.remove(self)
                
            self.source = None
            self.target = None 