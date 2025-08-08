from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QTimer, QRectF
from PyQt6.QtGui import QPainter, QColor, QPainterPath, QLinearGradient, QBrush, QPen
import math


class AnimatedGradientContainer(QWidget):
    """
    Lightweight container that paints a rounded, animated gradient background
    synchronized with the application's BorderedMainWidget colors and animation.

    If the main bordered widget is in autocomplete mode, uses its autocomplete color.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.corner_radius = 6
        self.background_opacity = 0.82
        self.border_color = QColor(85, 85, 85, 200)
        self.border_width = 1

        # Allow drawing semi-transparent rounded background
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAutoFillBackground(False)

        # Repaint periodically to follow the main widget's animation_offset
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.update)
        self._timer.start(50)

    def _get_bordered_widget(self):
        # Walk up to the top-level window and access its central widget
        top = self.window()
        if top and hasattr(top, 'centralWidget') and callable(top.centralWidget):
            return top.centralWidget()
        return None

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        path = QPainterPath()
        path.addRoundedRect(rect, self.corner_radius, self.corner_radius)
        painter.setClipPath(path)

        bordered_widget = self._get_bordered_widget()

        if bordered_widget and getattr(bordered_widget, 'is_autocompleting', False):
            # Solid autocomplete color background
            base = QColor(getattr(bordered_widget, 'autocomplete_color', QColor(0, 92, 92)))
            base.setAlphaF(self.background_opacity)
            painter.fillRect(rect, base)
        else:
            # Rotating gradient using bordered widget's colors and animation_offset
            colors = None
            if bordered_widget and hasattr(bordered_widget, 'colors'):
                colors = getattr(bordered_widget, 'colors')

            if not colors or len(colors) == 0:
                colors = [QColor(58, 78, 178), QColor(46, 135, 175), QColor(30, 155, 145), QColor(58, 78, 178)]

            animation_offset = 0
            if bordered_widget and hasattr(bordered_widget, 'animation_offset'):
                animation_offset = getattr(bordered_widget, 'animation_offset', 0)

            angle = float(animation_offset) * 3.6
            radians = angle * math.pi / 180.0

            length = max(self.width(), self.height()) * 1.2
            cx = self.width() / 2.0
            cy = self.height() / 2.0
            end_x = cx + length * math.cos(radians)
            end_y = cy + length * math.sin(radians)

            grad = QLinearGradient(cx - length * math.cos(radians),
                                   cy - length * math.sin(radians),
                                   end_x, end_y)
            # Populate gradient stops
            n = max(2, len(colors))
            for i, col in enumerate(colors):
                pos = i / float(n - 1)
                grad.setColorAt(pos, QColor(col))

            # Apply opacity by drawing onto a semi-transparent brush
            painter.save()
            painter.setBrush(QBrush(grad))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setOpacity(self.background_opacity)
            painter.drawRect(rect)
            painter.restore()

        # Subtle border to match UI style
        painter.setPen(QPen(self.border_color, self.border_width))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(path)

        super().paintEvent(event)


