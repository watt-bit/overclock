from PyQt5.QtWidgets import QGraphicsRectItem, QPushButton, QGraphicsProxyWidget
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QBrush, QColor, QPen, QRadialGradient, QFont, QPainterPath, QPolygonF, QLinearGradient
import math

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
        
        # Hover state tracking
        self.is_hovered = False
        self.component_id = id(self)  # Use object id as default component_id
        # Remove "Component" suffix if it exists
        class_name = self.__class__.__name__
        self.component_type = class_name.replace('Component', ' ID:') if class_name.endswith('Component') else class_name
        
        # Shadow properties
        self.shadow_opacity = 0.2  # Shadow transparency (0-1)
        self.shadow_blur = 30      # Shadow blur radius
        self.shadow_y_offset = -90   # Shadow offset from component bottom (reduced from 10)
        
        # Selection highlight pen
        self.selection_pen = QPen(QColor(255, 255, 255), 3, Qt.SolidLine)
        self.selection_pen.setCosmetic(True)  # Keep width constant regardless of zoom
        
        # Flag to track if properties panel is open for this component
        self.properties_open = False
        
        # Create the open button (initially hidden)
        self.open_button = QPushButton("Open")
        font = QFont()
        font.setFamilies(["Menlo", "Consolas", "Courier", "monospace"])
        font.setPointSize(10)
        self.open_button.setFont(font)
        self.open_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(37, 47, 52, 1.0); 
                color: white; 
                border: 1px solid #777777;
                border-radius: 5px;
                padding: 2px 5px;
            }
            QPushButton:hover {
                background-color: #3498db;
            }
            QPushButton:pressed {
                background-color: #2C80B4;
            }
        """)
        self.open_button.setFixedSize(50, 20)  # Small fixed size button
        self.open_button.clicked.connect(self.open_properties)
        
        # Prevent space bar from triggering the button
        self.open_button.setFocusPolicy(Qt.NoFocus)
        
        # Add the button to the scene using a proxy widget
        self.button_proxy = QGraphicsProxyWidget(self)
        self.button_proxy.setWidget(self.open_button)
        self.button_proxy.setVisible(False)  # Initially hidden
        
        # Status Jewel properties
        self.jewel_size = 20  # Size of the hexagonal jewel
        self.jewel_active = True  # Whether to show the jewel
    
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
            
            # Position and show the Open button above the top-left corner of the selection box
            self.button_proxy.setPos(highlight_rect.x(), highlight_rect.y() - 25)
            if not self.button_proxy.isVisible():
                self.button_proxy.setVisible(True)
        else:
            # Hide the button when not selected
            if self.button_proxy.isVisible():
                self.button_proxy.setVisible(False)
        
        # Draw hover text if component is being hovered
        if self.is_hovered:
            # Get component ID string (last 6 digits)
            component_id_str = str(self.component_id)[-6:]
            
            # Setup text appearance
            painter.save()
            font = QFont()
            font.setPointSize(12)
            painter.setFont(font)
            

            type_color = QColor(205, 205, 205)
            
            # Darker blue for component ID
            id_color = QColor(80, 150, 225)  # Darker blue for ID
            
            # Position text at top of component
            text_x = rect.x() + 5  # Small margin from left edge
            text_y = rect.y() + 15  # Adjust for text height
            
            # Draw the component type
            painter.setPen(type_color)
            painter.drawText(int(text_x), int(text_y), self.component_type)
            
            # Calculate position for ID text (right after component type)
            metrics = painter.fontMetrics()
            type_width = metrics.horizontalAdvance(self.component_type + " ")
            
            # Draw the ID with darker blue
            painter.setPen(id_color)
            painter.drawText(int(text_x + type_width), int(text_y), component_id_str)
            
            painter.restore()
            
        # Draw the status jewel if active and scene is available
        if self.jewel_active and self.scene() and hasattr(self.scene(), 'parent'):
            main_window = self.scene().parent()
            if hasattr(main_window, 'centralWidget') and main_window.centralWidget():
                bordered_widget = main_window.centralWidget()
                
                # Position the jewel at top right corner with a small margin
                jewel_x = rect.right() - self.jewel_size - 5
                jewel_y = rect.top() + 5
                
                # Create a hexagon path
                hex_path = QPainterPath()
                polygon = QPolygonF()
                
                # Calculate hexagon points
                center_x = jewel_x + self.jewel_size / 2
                center_y = jewel_y + self.jewel_size / 2
                radius = self.jewel_size / 2
                
                for i in range(6):
                    angle = math.pi / 3 * i
                    x = center_x + radius * math.cos(angle)
                    y = center_y + radius * math.sin(angle)
                    polygon.append(QRectF(x, y, 0, 0).center())
                
                hex_path.addPolygon(polygon)
                hex_path.closeSubpath()
                
                # Draw the jewel with same colors/effects as the bordered widget
                painter.save()
                
                # Check if autocomplete is active
                if hasattr(bordered_widget, 'is_autocompleting') and bordered_widget.is_autocompleting:
                    # Use autocomplete color
                    painter.setBrush(QBrush(bordered_widget.autocomplete_color))
                    painter.setPen(QPen(bordered_widget.autocomplete_color.lighter(130), 1))
                    painter.drawPath(hex_path)
                else:
                    # Use current border colors from the bordered widget
                    # Get gradient colors from the bordered widget
                    colors = bordered_widget.colors if hasattr(bordered_widget, 'colors') else [QColor(58, 78, 178)]
                    
                    # Create a rotating gradient that matches the main widget animation
                    if len(colors) > 1:
                        # Get the animation offset from the bordered widget
                        animation_offset = bordered_widget.animation_offset if hasattr(bordered_widget, 'animation_offset') else 0
                        
                        # Calculate rotation angle based on animation offset (same as in bordered_main_widget)
                        angle = animation_offset * 3.6  # Convert percentage to degrees (0-100 to 0-360)
                        radians = angle * math.pi / 180.0  # Convert to radians
                        
                        # Calculate endpoint based on angle to create rotating linear gradient
                        length = self.jewel_size * 1.25
                        center_x = center_x
                        center_y = center_y
                        
                        end_x = center_x + length * math.cos(radians)
                        end_y = center_y + length * math.sin(radians)
                        
                        # Create rotating linear gradient
                        gradient = QLinearGradient(
                            center_x - length * math.cos(radians),
                            center_y - length * math.sin(radians),
                            end_x, end_y
                        )
                        
                        # Set gradient colors
                        num_colors = len(colors)
                        for i in range(num_colors):
                            pos = i / (num_colors - 1)
                            gradient.setColorAt(pos, colors[i])
                            
                        painter.setBrush(QBrush(gradient))
                    else:
                        painter.setBrush(QBrush(colors[0]))
                    
                    # Add a subtle border
                    painter.setPen(QPen(QColor(255, 255, 255, 80), 2))
                    painter.drawPath(hex_path)
                
                painter.restore()
        
        # Draw standardized text box at the bottom of the component
        self.draw_standard_text_box(painter, rect)
    
    def is_decorative_component(self):
        """Check if this component is purely decorative"""
        decorative_types = [
            "TreeComponent", 
            "BushComponent", 
            "PondComponent", 
            "House1Component", 
            "House2Component", 
            "FactoryComponent", 
            "TraditionalDataCenterComponent", 
            "DistributionPoleComponent"
        ]
        return self.__class__.__name__ in decorative_types
        
    def draw_standard_text_box(self, painter, rect):
        """Draw the standardized text box at the bottom of the component"""
        # Skip drawing text box for decorative components
        if self.is_decorative_component():
            return
            
        # Save painter state
        painter.save()
        
        # Get the current view scale factor to adjust text size
        scale_factor = 1.0
        if self.scene() and self.scene().views():
            view = self.scene().views()[0]
            if hasattr(view, 'transform'):
                scale_factor = 1.0 / view.transform().m11()  # Get inverse of horizontal scale
        
        # Set font for text - use same fixed-width fonts as terminal for compatibility
        font = QFont()
        font.setFamilies(["Menlo", "Consolas", "Courier", "monospace"])
        font.setPointSize(int(10 * scale_factor))
        painter.setFont(font)
        
        # Get the content for both lines of text
        first_line = self.get_capacity_and_mode_text()
        second_line = self.get_cost_or_revenue_text()
        
        # Calculate width needed for text content
        metrics = painter.fontMetrics()
        first_line_width = metrics.horizontalAdvance(first_line)
        second_line_width = metrics.horizontalAdvance(second_line)
        
        # Use the wider of the two lines plus padding
        content_width = max(first_line_width, second_line_width)
        
        # Add padding (scaled with zoom factor)
        horizontal_padding = 10 * max(1.0, scale_factor * 0.8)  # Left + right padding
        vertical_padding = 10 * max(1.0, scale_factor * 0.8)  # Top + bottom padding
        
        # Minimum width to prevent very narrow boxes
        min_width = 100 * max(1.0, scale_factor * 0.8)
        
        # Calculate final text box width
        text_box_width = max(min_width, content_width + horizontal_padding)
        
        # Fixed height for two lines of text plus vertical padding
        line_height = metrics.height() + 2  # Add a bit of extra space between lines
        text_box_height = (line_height * 2) + vertical_padding  # Two lines plus padding

        # Calculate relative position from center of component
        # Horizontally centered
        text_box_x = rect.x() + (rect.width() - text_box_width) / 2
        
        # Position vertically relative to component center
        vertical_offset_percent = 0.4  # 40% of height down from center
        center_y = rect.y() + rect.height() / 2
        text_box_y = center_y + (rect.height() * vertical_offset_percent) - (text_box_height / 2)
        
        # Create text box rectangle
        text_box_rect = QRectF(
            text_box_x,
            text_box_y,
            text_box_width,
            text_box_height
        )
        
        # Draw the rounded rectangle background with specified color
        corner_radius = 10 * max(1.0, scale_factor * 0.8)  # Scale corner radius
        background_color = QColor(37, 47, 52, 191)  # rgba(37, 47, 52, 0.75) - 191 is 75% of 255
        
        # Create a grayer version of the background color for the border with same transparency
        border_color = QColor(60, 70, 75, 191)  # Slightly grayer than background but same transparency
        
        # Set the brush with background color
        painter.setBrush(QBrush(background_color))
        # Set 1px border with the border color
        painter.setPen(QPen(border_color, 1))
        
        # Draw rounded rectangle
        painter.drawRoundedRect(text_box_rect, corner_radius, corner_radius)
        
        # Calculate text positions within the text box
        vertical_padding_half = vertical_padding / 2
        
        first_line_rect = QRectF(
            text_box_x + horizontal_padding/2,  # Left padding
            text_box_y + vertical_padding_half,  # Top padding
            text_box_width - horizontal_padding,  # Width - padding
            line_height  # Line height
        )
        
        second_line_rect = QRectF(
            text_box_x + horizontal_padding/2,  # Left padding
            text_box_y + vertical_padding_half + line_height,  # First line height + top padding
            text_box_width - horizontal_padding,  # Width - padding
            line_height  # Line height
        )
        
        # Get the two lines of text
        
        # Draw the first line (capacity and mode) with white color
        painter.setPen(QPen(Qt.white))
        painter.drawText(first_line_rect, Qt.AlignLeft | Qt.AlignVCenter, first_line)
        
        # Set color based on whether showing cost or revenue for the second line
        # Use the same palette as in AutocompleteManager._get_irr_color
        if hasattr(self, 'accumulated_revenue') and self.accumulated_revenue > 0:
            # Green for revenue (same as IRR display)
            painter.setPen(QPen(QColor(139, 255, 74)))
        elif hasattr(self, 'accumulated_cost') and self.accumulated_cost > 0:
            # Red for cost (same as IRR display)
            painter.setPen(QPen(QColor(255, 50, 50)))
        else:
            # Default white for neutral or zero values
            painter.setPen(QPen(Qt.white))
            
        painter.drawText(second_line_rect, Qt.AlignLeft | Qt.AlignVCenter, second_line)
        
        # Restore painter state
        painter.restore()
    
    def get_capacity_and_mode_text(self):
        """Get the text for capacity and operating mode"""
        # Default implementation - to be overridden by subclasses if needed
        capacity_text = "MW: -"
        
        # Check if this is a component with a capacity property
        # Handle different capacity properties based on component type
        class_name = self.__class__.__name__
        
        # For battery components, use power_capacity
        if class_name == "BatteryComponent" and hasattr(self, 'power_capacity'):
            capacity_mw = self.power_capacity / 1000 if self.power_capacity else 0
            capacity_text = f"MW: {capacity_mw:.1f}"
        # For load components, use demand
        elif class_name == "LoadComponent" and hasattr(self, 'demand'):
            capacity_mw = self.demand / 1000 if self.demand else 0
            capacity_text = f"MW: {capacity_mw:.1f}"
        # For other components, use capacity if available
        elif hasattr(self, 'capacity'):
            capacity_mw = self.capacity / 1000 if self.capacity else 0
            capacity_text = f"MW: {capacity_mw:.1f}"
        
        # Check for operating mode
        mode_text = ""
        if hasattr(self, 'operating_mode'):
            mode_text = f"| {self.operating_mode}"
        elif class_name == "BusComponent":
            # Special handling for Bus component - check if it has load connections
            if hasattr(self, 'has_load_connections') and callable(getattr(self, 'has_load_connections')):
                has_loads = self.has_load_connections()
                mode_text = "| LOADED" if has_loads else "| AUTO"
            else:
                # Fallback to checking is_on if has_load_connections is not available
                mode_text = "| LOADED" if hasattr(self, 'is_on') and self.is_on else "| AUTO"
        
        return f"{capacity_text} {mode_text}"
    
    def get_cost_or_revenue_text(self):
        """Get the text for cost or revenue"""
        # Default implementation - to be overridden by subclasses if needed
        if hasattr(self, 'accumulated_cost'):
            return f"$: {int(self.accumulated_cost):,}"
        elif hasattr(self, 'accumulated_revenue'):
            return f"$: {int(self.accumulated_revenue):,}"
        else:
            return "$: -"
    
    def open_properties(self):
        """Toggle the properties panel open/closed state"""
        if self.scene() and hasattr(self.scene(), 'component_clicked'):
            if not self.properties_open:
                # Open the properties panel
                self.scene().component_clicked.emit(self)
                self.properties_open = True
                self.open_button.setText("Close")
            else:
                # Close the properties panel
                if self.scene() and hasattr(self.scene(), 'parent'):
                    scene_parent = self.scene().parent()
                    if hasattr(scene_parent, 'properties_manager'):
                        scene_parent.properties_manager.clear_properties_panel()
                        if hasattr(scene_parent, 'properties_dock'):
                            scene_parent.properties_dock.setVisible(False)
                        self.properties_open = False
                        self.open_button.setText("Open")
    
    def set_properties_panel_state(self, is_open):
        """Update the properties panel state and button text"""
        self.properties_open = is_open
        if is_open:
            self.open_button.setText("Close")
        else:
            self.open_button.setText("Open")
    
    def hoverEnterEvent(self, event):
        # Set hover state flag
        self.is_hovered = True
        
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
        
        # Force repaint to show hover text
        self.update()
        
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        # Reset hover state flag
        self.is_hovered = False
        
        # Only unset cursor if not in connection mode
        if not self.scene() or not hasattr(self.scene(), 'parent') or not self.scene().parent().creating_connection:
            self.unsetCursor()
        # Restore original brush and pen
        if hasattr(self, 'original_brush'):
            self.setBrush(self.original_brush)
        if hasattr(self, 'original_pen'):
            self.setPen(self.original_pen)
            
        # Force repaint to remove hover text
        self.update()
        
        super().hoverLeaveEvent(event)
    
    def mousePressEvent(self, event):
        # Scale up slightly when clicked
        self.setScale(1.05)
        super().mousePressEvent(event)
        
        # Emit component_clicked signal when in connection mode
        if self.scene() and hasattr(self.scene(), 'parent') and hasattr(self.scene().parent(), 'creating_connection') and self.scene().parent().creating_connection:
            if hasattr(self.scene(), 'component_clicked'):
                self.scene().component_clicked.emit(self)
    
    def mouseDoubleClickEvent(self, event):
        # Handle double click to show properties panel
        super().mouseDoubleClickEvent(event)
        if self.scene() and hasattr(self.scene(), 'component_clicked'):
            self.scene().component_clicked.emit(self)
            self.properties_open = True
            self.open_button.setText("Close")
    
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
            # Reset properties_open state when deselected
            if not value:
                self.properties_open = False
                self.open_button.setText("Open")
            # When component is selected, close any open properties panels
            elif value and self.scene() and hasattr(self.scene(), 'parent'):
                scene_parent = self.scene().parent()
                if hasattr(scene_parent, 'properties_manager'):
                    # Close any open properties panel
                    scene_parent.properties_manager.clear_properties_panel()
                    # Hide the properties dock
                    if hasattr(scene_parent, 'properties_dock'):
                        scene_parent.properties_dock.setVisible(False)
                    # Reset properties_open state for all components
                    if hasattr(scene_parent, 'components'):
                        for component in scene_parent.components:
                            if hasattr(component, 'set_properties_panel_state'):
                                component.set_properties_panel_state(False)
        return super().itemChange(change, value) 