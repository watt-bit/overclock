from PyQt6.QtWidgets import QGraphicsLineItem
from PyQt6.QtCore import Qt, QTimer, QRectF, QPointF
from PyQt6.QtGui import QPen, QColor, QBrush, QLinearGradient, QRadialGradient, QPainter, QPainterPath
import random
import math

class Connection(QGraphicsLineItem):
    # Static variables for synchronized animation
    animation_time = 0
    oscillation_speed = 0.2
    animation_timer = None
    active_connections = []
    
    # Visual style configuration
    core_width = 2.5
    glow_outer_width = 10
    glow_mid_width = 7
    glow_inner_width = 4
    flow_width = 3
    pulse_thick_width = 6
    
    # Wavy path parameters (kept small to stay within bounding rect of pen)
    sine_amplitude = 4.0   # px, must be <= glow_outer_width/2 to avoid bounding issues
    sine_frequency = 2.0   # waves along the length
    
    # Colors (subtle electric blue → cyan)
    color_start = QColor(80, 150, 225, 200)
    color_end = QColor(0, 200, 255, 200)
    glow_color = QColor(80, 150, 225, 140)
    highlight_color = QColor(255, 255, 255, 220)
    
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
        
        # Per-connection style seed for slight variation across connectors
        self._style_seed = random.random()
        self._hue_base_offset = (self._style_seed * 2.0 - 1.0) * 10.0  # ±10 degrees
        self._sine_amplitude = self.sine_amplitude * (0.8 + 0.4 * self._style_seed)  # 0.8x-1.2x
        self._sine_frequency = self.sine_frequency * (0.9 + 0.3 * (1.0 - self._style_seed))  # 0.9x-1.2x
        self._glow_intensity = 1.0 + 0.25 * (self._style_seed - 0.5)  # ~±12.5%

        # Use a wide transparent pen so the bounding rect accounts for glow and thick pulse
        base_width = max(self.glow_outer_width, self.flow_width, int(self.pulse_thick_width * 2.0))
        base_pen = QPen(QColor(0, 0, 0, 0), base_width)
        base_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        base_pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        self.setPen(base_pen)
        
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
        
        # Internal phase for highlight flow
        self._local_phase = 0.0

    # --- Helper methods for animated wavy path ---
    def _interpolate_point(self, p1: QPointF, p2: QPointF, t: float, phase: float) -> QPointF:
        dx = p2.x() - p1.x()
        dy = p2.y() - p1.y()
        length = math.hypot(dx, dy)
        if length <= 1e-6:
            return QPointF(p1)
        # Base point along the straight line
        bx = p1.x() + dx * t
        by = p1.y() + dy * t
        # Perpendicular unit normal
        nx = -dy / length
        ny = dx / length
        # Smooth amplitude taper near ends to avoid harsh joins
        taper = math.sin(math.pi * t)
        offset = self._sine_amplitude * taper * math.sin(2.0 * math.pi * self._sine_frequency * t + phase)
        return QPointF(bx + nx * offset, by + ny * offset)

    def _build_wavy_path(self, p1: QPointF, p2: QPointF, phase: float, samples: int = 40) -> QPainterPath:
        if samples < 2:
            samples = 2
        path = QPainterPath()
        # Start point
        start_point = self._interpolate_point(p1, p2, 0.0, phase)
        path.moveTo(start_point)
        # Interior points
        for i in range(1, samples):
            t = i / (samples - 1)
            pt = self._interpolate_point(p1, p2, t, phase)
            path.lineTo(pt)
        return path
    
    def update_animation(self):
        """Advance animation phase and request repaint."""
        # Keep a local phase that can be used for secondary motions
        self._local_phase = Connection.animation_time
        # Trigger a repaint to reflect the new animation state
        self.update()
    
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
            # Ensure the item repaints to reflect any changes
            self.update()
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

    def paint(self, painter: QPainter, option, widget=None):
        """Custom rendering for a softer, more sophisticated animated connector."""
        line = self.line()
        if line.length() < 1e-3:
            return
        
        # Enable smooth edges
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        
        p1 = line.p1()
        p2 = line.p2()

        # Time parameters
        phase = self._local_phase
        # Build animated wavy path following the line
        path = self._build_wavy_path(p1, p2, phase)
        
        # Build a gradient along the connector
        # Hue shift over time for extra interest (with per-connection base offset)
        base_hue = 205 + int(self._hue_base_offset)  # blue-ish
        hue_shift = int(15 * math.sin(phase * 0.6))
        start_hue = (base_hue + hue_shift) % 360
        end_hue = (start_hue + 35) % 360
        start_col = QColor.fromHsv(start_hue, 180, 255, 220)
        end_col = QColor.fromHsv(end_hue, 200, 255, 220)
        grad = QLinearGradient(p1, p2)
        grad.setColorAt(0.0, start_col)
        grad.setColorAt(1.0, end_col)
        
        # Soft outer glow (three passes, largest to smallest)
        breathing = (0.85 + 0.15 * (0.5 + 0.5 * math.sin(phase * 0.8))) * self._glow_intensity
        for width, alpha in [
            (self.glow_outer_width, int(60 * breathing)),
            (self.glow_mid_width, int(90 * breathing)),
            (self.glow_inner_width, int(120 * breathing)),
        ]:
            glow_pen = QPen(self.glow_color)
            glow_color = QColor(self.glow_color)
            glow_color.setAlpha(alpha)
            glow_pen.setColor(glow_color)
            glow_pen.setWidthF(width)
            glow_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            glow_pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.setPen(glow_pen)
            painter.drawPath(path)
        
        # Core line with subtle gradient
        core_width = self.core_width * (1.0 + 0.10 * math.sin(phase * 0.9))
        core_pen = QPen(QBrush(grad), core_width)
        core_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        core_pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(core_pen)
        painter.drawPath(path)

        # Inner bright filament for crispness
        filament_pen = QPen(QColor(255, 255, 255, 110), max(1.0, core_width * 0.5))
        filament_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        filament_pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(filament_pen)
        painter.drawPath(path)
        
        # Animated gentle flow (low-opacity dashes moving along the line)
        flow_pen = QPen(QBrush(grad), self.flow_width)
        flow_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        flow_pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        flow_pen.setDashPattern([10, 16])
        # Negative offset moves the dashes from source to target
        flow_pen.setDashOffset(-Connection.animation_time * 2.2)
        flow_color_start = QColor(255, 255, 255, 70)
        flow_color_end = QColor(255, 255, 255, 20)
        flow_grad = QLinearGradient(p1, p2)
        flow_grad.setColorAt(0.0, flow_color_start)
        flow_grad.setColorAt(1.0, flow_color_end)
        flow_pen.setBrush(QBrush(flow_grad))
        painter.setPen(flow_pen)
        painter.drawPath(path)
        
        # Subtle moving highlight pulse traveling back-and-forth
        # Map sine phase to [0, 1]
        t = 0.5 * (1.0 + math.sin(self._local_phase * 0.8))
        pulse_pt = self._interpolate_point(p1, p2, t, phase)
        pulse_x = pulse_pt.x()
        pulse_y = pulse_pt.y()
        
        # Pulse radius and opacity vary slightly with phase
        base_radius = 6.0
        radius = base_radius + 1.5 * (0.5 + 0.5 * math.sin(self._local_phase))
        
        radial = QRadialGradient(pulse_x, pulse_y, radius)
        inner = QColor(self.highlight_color)
        outer = QColor(self.highlight_color)
        inner.setAlpha(220)
        outer.setAlpha(0)
        radial.setColorAt(0.0, inner)
        radial.setColorAt(0.6, QColor(255, 255, 255, 90))
        radial.setColorAt(1.0, outer)
        painter.setBrush(QBrush(radial))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(pulse_x - radius, pulse_y - radius, radius * 2.0, radius * 2.0))

        # Thicker pulse segment overlay around the pulse for dynamic width feel
        segment_span = 0.10  # fraction of length
        t0 = max(0.0, t - segment_span * 0.5)
        t1 = min(1.0, t + segment_span * 0.5)
        seg_samples = 14
        pulse_path = QPainterPath()
        start_seg = self._interpolate_point(p1, p2, t0, phase)
        pulse_path.moveTo(start_seg)
        for i in range(1, seg_samples):
            tt = t0 + (t1 - t0) * (i / (seg_samples - 1))
            pulse_path.lineTo(self._interpolate_point(p1, p2, tt, phase))
        # Width oscillates slightly
        width_boost = 1.2 + 0.6 * (0.5 + 0.5 * math.sin(self._local_phase * 1.4))
        pulse_pen = QPen(QColor(255, 255, 255, 90), self.pulse_thick_width * width_boost)
        pulse_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pulse_pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pulse_pen)
        painter.drawPath(pulse_path)

        # Endpoint glow orbs (subtle)
        end_breathe = 0.6 + 0.4 * (0.5 + 0.5 * math.sin(phase * 0.7))
        end_radius = 7.0 * end_breathe
        for ep in (p1, p2):
            orb = QRadialGradient(ep.x(), ep.y(), end_radius)
            c0 = QColor(start_col)
            c0.setAlpha(160)
            c1 = QColor(start_col)
            c1.setAlpha(0)
            orb.setColorAt(0.0, c0)
            orb.setColorAt(1.0, c1)
            painter.setBrush(QBrush(orb))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QRectF(ep.x() - end_radius, ep.y() - end_radius, end_radius * 2.0, end_radius * 2.0))

        # Tiny sparkles traveling along the path
        sparkle_ts = [
            (phase * 0.15) % 1.0,
            (phase * 0.27 + 0.33) % 1.0,
            (phase * 0.39 + 0.66) % 1.0,
        ]
        for i, tt in enumerate(sparkle_ts):
            s_pt = self._interpolate_point(p1, p2, tt, phase)
            s_r = 2.0 + (i % 2)  # 2 or 3 px
            s_alpha = 110 if i == 0 else 80
            s_grad = QRadialGradient(s_pt.x(), s_pt.y(), s_r)
            s_grad.setColorAt(0.0, QColor(255, 255, 255, s_alpha))
            s_grad.setColorAt(1.0, QColor(255, 255, 255, 0))
            painter.setBrush(QBrush(s_grad))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QRectF(s_pt.x() - s_r, s_pt.y() - s_r, s_r * 2.0, s_r * 2.0))