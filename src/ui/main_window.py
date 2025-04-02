import sys
import json
import re
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QPushButton, QSlider, QFileDialog, 
                            QGraphicsView, QGraphicsScene, QDockWidget, 
                            QFormLayout, QLineEdit, QComboBox, QToolBar, 
                            QAction, QMessageBox, QSplitter, QGraphicsLineItem,
                            QApplication, QSpacerItem, QMenu, QShortcut, QFrame,
                            QToolButton, QSizePolicy)
from PyQt5.QtCore import Qt, QPointF, QRectF, QTimer, pyqtSignal, QObject, QSize
from PyQt5.QtGui import QPainter, QPen, QCursor, QPixmap, QColor, QDoubleValidator, QIntValidator, QBrush, QKeySequence, QIcon
import math

from src.components.base import ComponentBase
from src.components.generator import GeneratorComponent
from src.components.load import LoadComponent
from src.components.bus import BusComponent
from src.components.connection import Connection
from src.components.grid_import import GridImportComponent
from src.components.grid_export import GridExportComponent
from src.components.battery import BatteryComponent
from src.components.tree import TreeComponent
from src.components.bush import BushComponent
from src.components.pond import PondComponent
from src.components.house1 import House1Component
from src.components.house2 import House2Component
from src.components.factory import FactoryComponent
from src.components.cloud_workload import CloudWorkloadComponent
from src.components.solar_panel import SolarPanelComponent
from src.simulation.engine import SimulationEngine
from .analytics import AnalyticsPanel
from .properties_manager import ComponentPropertiesManager
from .connection_manager import ConnectionManager
from src.models.model_manager import ModelManager

# TODO: This file needs to be refactored to be more modular and easier to understand. A lot of the setup and initialization / UI code can be pushed to other separate files.

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
        self.background_color = QColor("#2D2D2D")
    
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
                painter.drawLine(x, rect.top(), x, rect.bottom())
                
            # Draw horizontal grid lines  
            for y in range(top, int(rect.bottom()) + grid_size, grid_size):
                painter.drawLine(rect.left(), y, rect.right(), y)
                
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

class TiledBackgroundWidget(QWidget):
    """Widget that supports a tiled background image"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.background_image = None
        self.tile_size = 300  # Fixed tile size of 100x100 pixels
        
    def set_background(self, image_path):
        """Set the background image from a file path"""
        self.background_image = QPixmap(image_path)
        self.update()
        
    def paintEvent(self, event):
        """Override paintEvent to draw the tiled background"""
        painter = QPainter(self)
        
        # First call the base implementation to clear the background
        super().paintEvent(event)
        
        # Only proceed if we have a valid background image
        if not self.background_image or self.background_image.isNull():
            return
            
        # Get the size of the widget
        rect = self.rect()
        
        # Scale the background image to our fixed tile size
        scaled_image = self.background_image.scaled(self.tile_size, self.tile_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        
        # Calculate the grid based on the view rect
        left = int(rect.left()) - (int(rect.left()) % self.tile_size)
        top = int(rect.top()) - (int(rect.top()) % self.tile_size)
        
        # Draw the tiled background
        for x in range(left, int(rect.right()) + self.tile_size, self.tile_size):
            for y in range(top, int(rect.bottom()) + self.tile_size, self.tile_size):
                painter.drawPixmap(x, y, self.tile_size, self.tile_size, scaled_image)

class PowerSystemSimulator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Overclock Watt-Bit Sandbox | augur vc | https://augurvc.com")
        self.resize(2400, 1200)
        
        # Initialize variables
        self.components = []
        self.connections = []
        self.creating_connection = False
        self.connection_source = None
        self.temp_connection = None
        self.cursor_phase = 0
        self.is_scrubbing = False
        self.scrub_timer = None
        
        # Track if the properties panel has been positioned yet
        self.properties_panel_positioned = False
        
        # Background mode: 0 = background1, 1 = background2, 2 = solid color
        self.background_mode = 2  # Set default to solid color (Background Off)
        
        # Create simulation engine
        self.simulation_engine = SimulationEngine(self)
        
        # Create properties manager
        self.properties_manager = ComponentPropertiesManager(self)
        
        # Create model manager
        self.model_manager = ModelManager(self)
        
        # Cursor animation
        self.cursor_timer = QTimer()
        self.cursor_timer.timeout.connect(self.update_cursor)
        self.cursor_size = 32
        
        # Create scene with custom signal
        self.scene = CustomScene()
        self.scene.parent = lambda: self
        self.scene.component_clicked.connect(self.properties_manager.show_component_properties)
        
        # Set the initial background mode to solid color
        self.scene.set_background(self.background_mode)
        
        self.init_ui()
        
        # Setup simulation timer
        self.sim_timer = QTimer()
        self.sim_timer.timeout.connect(lambda: self.step_simulation(1))
        self.simulation_speed = 1
        
        # Create connection manager
        self.connection_manager = ConnectionManager(self)
        
        # Welcome text for new users
        self.welcome_text = None
        self.add_welcome_text()
        
        # Center the window on the screen
        self.center_on_screen()
    
    def center_on_screen(self):
        """Center the window on the screen"""
        screen_geometry = QApplication.desktop().screenGeometry()
        window_geometry = self.geometry()
        
        x = (screen_geometry.width() - window_geometry.width()) // 2
        y = (screen_geometry.height() - window_geometry.height()) // 2 - 50
        
        self.move(x, y)
    
    def validate_bus_states(self):
        """Ensure all bus components without load connections are set to ON"""
        for component in self.components:
            if isinstance(component, BusComponent):
                if not component.has_load_connections() and not component.is_on:
                    component.is_on = True
                    component.update()  # Redraw the component
    
    def init_ui(self):
        # Main layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        
        # Create a stylesheet for dock widgets to have modern flat dark gray title bars
        dock_title_style = """
        QMainWindow::separator {
            width: 0px;
            height: 0px;
            background-color: transparent;
        }
        QDockWidget {
            border: none;
        }
        QDockWidget::title {
            background-color: #2A2A2A;
            color: white;
            text-align: center;
            height: 25px;
            border-bottom: 1px solid #555555;
            font-weight: bold;
        }
        QDockWidget::close-button, QDockWidget::float-button {
            background-color: #2A2A2A;
            border: none;
        }
        QDockWidget::close-button:hover, QDockWidget::float-button:hover {
            background-color: #404040;
            border-radius: 2px;
        }
        """
        
        # Apply the stylesheet to the application
        self.setStyleSheet(dock_title_style)
        
        # Create canvas for drag and drop
        self.view = QGraphicsView(self.scene)
        self.view.setDragMode(QGraphicsView.RubberBandDrag)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        
        # Set initial scaling for view
        self.current_zoom = 0.8
        
        # Apply initial zoom transform
        transform = self.view.transform()
        transform.scale(self.current_zoom, self.current_zoom)
        self.view.setTransform(transform)
        
        # Enable key events on the view
        self.view.setFocusPolicy(Qt.StrongFocus)
        
        # Install event filter for key events
        self.view.installEventFilter(self)
        
        # Component palette
        self.component_dock = QDockWidget("Components", self)
        self.component_dock.setObjectName("component_dock")
        # Remove title bar and prevent undocking/closing
        self.component_dock.setTitleBarWidget(QWidget())
        self.component_dock.setFeatures(QDockWidget.NoDockWidgetFeatures)
        # Set fixed width to 200px
        self.component_dock.setFixedWidth(200)
        # Ensure no borders are visible
        self.component_dock.setStyleSheet("QDockWidget { border: none; }")
        
        # Use TiledBackgroundWidget instead of regular QWidget
        component_widget = TiledBackgroundWidget()
        component_widget.set_background("src/ui/assets/backgroundstars.png")
        component_layout = QVBoxLayout(component_widget)
        
        # Add component panel top image
        top_image_label = QLabel()
        top_image_label.setStyleSheet("border: none;")
        top_pixmap = QPixmap("src/ui/assets/componentspaneltop.png")
        if not top_pixmap.isNull():
            # Get the width of the component widget minus layout margins
            # We'll wait to set the actual image after the first button is created
            top_image_label.setAlignment(Qt.AlignCenter)
            component_layout.addWidget(top_image_label)
        
        # Define a common button style with opaque background
        opaque_button_style = "QPushButton { background-color: #3D3D3D; color: white; border: 1px solid #555555; border-radius: 3px; padding: 5px; }"
        
        generator_btn = QPushButton("(G)as Generator")
        generator_btn.setStyleSheet(opaque_button_style)
        generator_btn.clicked.connect(lambda: self.add_component("generator"))
        
        battery_btn = QPushButton("Battery (S)torage")
        battery_btn.setStyleSheet(opaque_button_style)
        battery_btn.clicked.connect(lambda: self.add_component("battery"))
        
        load_btn = QPushButton("Electrical (L)oad")
        load_btn.setStyleSheet(opaque_button_style)
        load_btn.clicked.connect(lambda: self.add_component("load"))
        
        bus_btn = QPushButton("Power (B)us")
        bus_btn.setStyleSheet(opaque_button_style)
        bus_btn.clicked.connect(lambda: self.add_component("bus"))
        
        cloud_workload_btn = QPushButton("Cloud (W)orkload")
        cloud_workload_btn.setStyleSheet(opaque_button_style)
        cloud_workload_btn.clicked.connect(lambda: self.add_component("cloud_workload"))
        
        # Add a third horizontal line separator
        separator3 = QFrame()
        separator3.setFrameShape(QFrame.HLine)
        separator3.setFrameShadow(QFrame.Sunken)
        separator3.setLineWidth(1)

        grid_import_btn = QPushButton("Grid (I)mport Pathway")
        grid_import_btn.setStyleSheet(opaque_button_style)
        grid_import_btn.clicked.connect(lambda: self.add_component("grid_import"))
        
        grid_export_btn = QPushButton("Grid (E)xport Pathway")
        grid_export_btn.setStyleSheet(opaque_button_style)
        grid_export_btn.clicked.connect(lambda: self.add_component("grid_export"))
        
        # Add a horizontal line separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setLineWidth(1)
        
        self.connection_btn = QPushButton("Create (C)onnection")
        self.connection_btn.setStyleSheet(opaque_button_style)
        self.connection_btn.clicked.connect(self.start_connection)
        
        autoconnect_btn = QPushButton("(A)utoconnect All")
        autoconnect_btn.setStyleSheet(opaque_button_style)
        autoconnect_btn.clicked.connect(self.autoconnect_all_components)
        
        self.sever_connection_btn = QPushButton("Sever Connections")
        self.sever_connection_btn.setStyleSheet(opaque_button_style)
        self.sever_connection_btn.clicked.connect(self.start_sever_connection)

        # Add a second horizontal line separator
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.HLine)
        separator2.setFrameShadow(QFrame.Sunken)
        separator2.setLineWidth(1)

        solar_panel_btn = QPushButton("Solar Array")
        solar_panel_btn.setStyleSheet(opaque_button_style)
        solar_panel_btn.clicked.connect(lambda: self.add_component("solar_panel"))

        # Create a popup menu for props
        props_menu = QMenu(self)
        
        # Add actions for each prop type
        tree_action = props_menu.addAction("Add Tree")
        tree_action.triggered.connect(lambda: self.add_component("tree"))
        
        bush_action = props_menu.addAction("Add Bush")
        bush_action.triggered.connect(lambda: self.add_component("bush"))
        
        pond_action = props_menu.addAction("Add Pond")
        pond_action.triggered.connect(lambda: self.add_component("pond"))
        
        house1_action = props_menu.addAction("Add House")
        house1_action.triggered.connect(lambda: self.add_component("house1"))
        
        house2_action = props_menu.addAction("Add Greenhouse")
        house2_action.triggered.connect(lambda: self.add_component("house2"))
        
        factory_action = props_menu.addAction("Add Factory")
        factory_action.triggered.connect(lambda: self.add_component("factory"))
        
        # Create the Add Props button with dropdown menu
        self.props_btn = QPushButton("Add Props")
        self.props_btn.setStyleSheet(opaque_button_style)
        self.props_btn.clicked.connect(lambda: props_menu.exec_(self.props_btn.mapToGlobal(self.props_btn.rect().bottomLeft())))
        
        component_layout.addWidget(generator_btn)
        component_layout.addWidget(battery_btn)
        component_layout.addWidget(load_btn)
        component_layout.addWidget(bus_btn)
        component_layout.addWidget(cloud_workload_btn)
        component_layout.addWidget(separator3)
        component_layout.addWidget(grid_import_btn)
        component_layout.addWidget(grid_export_btn)
        component_layout.addWidget(separator)
        component_layout.addWidget(self.connection_btn)
        component_layout.addWidget(autoconnect_btn)
        component_layout.addWidget(self.sever_connection_btn)
        component_layout.addWidget(separator2)
        component_layout.addWidget(solar_panel_btn)
        component_layout.addWidget(self.props_btn)
        component_layout.addStretch()
        
        # Add logo at the bottom of the component palette
        logo_label = QLabel()
        logo_pixmap = QPixmap("src/ui/assets/augurvibelogosmall.png")
        if not logo_pixmap.isNull():
            # Calculate the scaled size to match component button width while maintaining aspect ratio
            button_width = generator_btn.sizeHint().width() + 75
            aspect_ratio = logo_pixmap.height() / logo_pixmap.width()
            scaled_height = int(button_width * aspect_ratio)
            logo_pixmap = logo_pixmap.scaled(button_width, scaled_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(logo_pixmap)
            logo_label.setAlignment(Qt.AlignCenter)
            component_layout.addWidget(logo_label)
            
            # Now that we have a button, set the top image size to match component width
            if not top_pixmap.isNull():
                top_aspect_ratio = top_pixmap.height() / top_pixmap.width()
                top_scaled_height = int(button_width * top_aspect_ratio)
                scaled_top_pixmap = top_pixmap.scaled(button_width, top_scaled_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                top_image_label.setPixmap(scaled_top_pixmap)
        
        # Store references to all component and connection buttons for later enabling/disabling
        self.component_buttons = [
            generator_btn, 
            solar_panel_btn,
            grid_import_btn, 
            grid_export_btn, 
            bus_btn, 
            load_btn, 
            battery_btn,
            cloud_workload_btn,
            self.props_btn,
            self.connection_btn,
            autoconnect_btn,
            self.sever_connection_btn
        ]
        
        self.component_dock.setWidget(component_widget)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.component_dock)
        
        # Properties panel
        self.properties_dock = QDockWidget("Properties", self)
        self.properties_dock.setObjectName("properties_dock")
        self.properties_dock.setWidget(self.properties_manager.properties_widget)
        # Allow the dock widget to resize when its contents change
        self.properties_dock.setFeatures(QDockWidget.DockWidgetFloatable | 
                                        QDockWidget.DockWidgetMovable | 
                                        QDockWidget.DockWidgetClosable)
        # Ensure the dock resizes to the minimum size of its contents
        self.properties_dock.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.addDockWidget(Qt.RightDockWidgetArea, self.properties_dock)
        # Make properties panel floating and hidden by default
        self.properties_dock.setFloating(True)
        self.properties_dock.setVisible(False)
        
        # Analytics panel
        self.analytics_dock = QDockWidget("Analytics", self)
        self.analytics_dock.setObjectName("analytics_dock")
        self.analytics_panel = AnalyticsPanel()
        self.analytics_dock.setWidget(self.analytics_panel)
        self.addDockWidget(Qt.RightDockWidgetArea, self.analytics_dock)
        # Make analytics panel hidden by default
        self.analytics_dock.setVisible(False)
        
        # Time controls
        time_dock = QDockWidget("Simulation Controls", self)
        # Remove title bar and prevent undocking/closing
        time_dock.setTitleBarWidget(QWidget())
        time_dock.setFeatures(QDockWidget.NoDockWidgetFeatures)
        # Set fixed height to 70px
        time_dock.setFixedHeight(70)
        # Ensure no borders are visible
        time_dock.setStyleSheet("QDockWidget { border: none; }")
        
        time_widget = TiledBackgroundWidget()
        time_widget.set_background("src/ui/assets/backgroundstars.png")
        time_layout = QVBoxLayout(time_widget)
        
        time_controls = QHBoxLayout()
        
        # Define common button style
        common_button_style = "QPushButton { border: 1px solid #555555; border-radius: 3px; padding: 5px; }"
        # Style for default grey buttons
        default_button_style = "QPushButton { background-color: #3D3D3D; color: white; border: 1px solid #555555; border-radius: 3px; padding: 5px; }"
        
        self.play_btn = QPushButton("Play (Space)")
        self.play_btn.clicked.connect(self.toggle_simulation)
        self.play_btn.setStyleSheet(common_button_style + "QPushButton { background-color: #2196F3; color: white; font-weight: bold; font-size: 16px; }")
        
        self.reset_btn = QPushButton("⟲ (R)eset")
        self.reset_btn.clicked.connect(self.reset_simulation)
        self.reset_btn.setStyleSheet(common_button_style + "QPushButton { background-color: #f44336; color: white; font-weight: bold; font-size: 16px; }")
        
        # Add speed control
        speed_label = QLabel("⏩ Speed:")
        self.speed_selector = QComboBox()
        self.speed_selector.addItems(["0.1x", "1x", "2x", "3x"])
        self.speed_selector.setCurrentIndex(1)  # Set default to 1x (now index 1)
        self.speed_selector.currentIndexChanged.connect(self.change_simulation_speed)
        self.speed_selector.setStyleSheet("QComboBox { background-color: #3D3D3D; color: white; border: 1px solid #555555; border-radius: 3px; padding: 5px; }")
        self.speed_selector.setMinimumWidth(80)  # Set minimum width to prevent text cutoff
        
        # Add zoom control to time controls (moved from toolbar)
        zoom_label = QLabel("🔭 Zoom:")
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setMinimum(40)  # 0.4x zoom (changed from 20/0.2x)
        self.zoom_slider.setMaximum(100)  # 1.0x zoom
        self.zoom_slider.setValue(80)    # Default to 0.8x
        self.zoom_slider.setFixedWidth(150)
        self.zoom_slider.valueChanged.connect(self.zoom_changed)
        self.zoom_slider.setStyleSheet("QSlider::groove:horizontal { background: #3D3D3D; height: 8px; border-radius: 4px; } QSlider::handle:horizontal { background: #5D5D5D; width: 16px; margin: -4px 0; border-radius: 8px; }")
        self.zoom_label = QLabel("0.8x")
        
        # Add screenshot button
        self.screenshot_btn = QPushButton("📷 Screenshot")
        self.screenshot_btn.clicked.connect(self.take_screenshot)
        self.screenshot_btn.setStyleSheet(default_button_style)
        
        # Add background toggle button
        self.background_toggle_btn = QPushButton("🌄 Background Off")
        self.background_toggle_btn.clicked.connect(self.toggle_background)
        self.background_toggle_btn.setStyleSheet(default_button_style)
        
        # Create time slider
        self.time_slider = QSlider(Qt.Horizontal)
        self.time_slider.setMinimum(0)
        self.time_slider.setMaximum(8760)  # 8760 hours in a year
        self.time_slider.valueChanged.connect(self.time_slider_changed)
        # Add new connections for scrub mode detection
        self.time_slider.sliderPressed.connect(self.start_scrubbing)
        self.time_slider.sliderReleased.connect(self.stop_scrubbing)
        # Set the time slider to expand horizontally
        self.time_slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.time_slider.setStyleSheet("QSlider::groove:horizontal { background: #3D3D3D; height: 8px; border-radius: 4px; } QSlider::handle:horizontal { background: #5D5D5D; width: 16px; margin: -4px 0; border-radius: 8px; }")
        
        time_controls.addWidget(self.reset_btn)
        time_controls.addWidget(self.play_btn)
        time_controls.addWidget(self.time_slider)
        time_controls.addWidget(self.background_toggle_btn)
        time_controls.addWidget(self.screenshot_btn)
        time_controls.addWidget(zoom_label)
        time_controls.addWidget(self.zoom_slider)
        time_controls.addWidget(self.zoom_label)
        time_controls.addWidget(speed_label)
        time_controls.addWidget(self.speed_selector)
        
        time_layout.addLayout(time_controls)
        
        time_dock.setWidget(time_widget)
        self.addDockWidget(Qt.BottomDockWidgetArea, time_dock)
        
        # Main canvas in the center
        main_layout.addWidget(self.view)
        
        # Create toolbar
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)
        
        # Increase font size for toolbar - using stylesheet for better compatibility
        toolbar_style = "QToolBar { font-size: 14pt; } QToolButton { font-size: 14pt; }"
        toolbar.setStyleSheet(toolbar_style)
        
        # Add actions to toolbar
        new_action = QAction("New", self)
        new_action.triggered.connect(self.new_scenario)
        
        save_action = QAction("Save", self)
        save_action.triggered.connect(self.save_scenario)
        
        load_action = QAction("Load", self)
        load_action.triggered.connect(self.load_scenario)
        
        toolbar.addAction(new_action)
        toolbar.addAction(save_action)
        toolbar.addAction(load_action)
        
        # Add separator
        toolbar.addSeparator()
        
        # Create View menu for showing/hiding panels
        view_menu = QMenu("View", self)
        
        # Create actions for toggling panel visibility
        show_components_action = QAction("Show Components Panel", self)
        show_components_action.triggered.connect(self.show_components_panel)
        view_menu.addAction(show_components_action)
        
        show_properties_action = QAction("Show (P)roperties Panel", self)
        show_properties_action.triggered.connect(self.show_properties_panel)
        view_menu.addAction(show_properties_action)
        
        show_analytics_action = QAction("Show Analytics Panel", self)
        show_analytics_action.triggered.connect(self.show_analytics_panel)
        view_menu.addAction(show_analytics_action)
        
        # Use QToolButton instead of QAction for View menu to make text clickable
        view_button = QToolButton()
        view_button.setText("View")
        view_button.setMenu(view_menu)
        view_button.setPopupMode(QToolButton.InstantPopup)  # Show menu when clicking anywhere on button
        toolbar.addWidget(view_button)
    
    def add_welcome_text(self):
        """Add welcome text to the middle of the canvas"""
        # Create text item with welcome message
        self.welcome_text = self.scene.addText("")
        
        # Set font and style
        font = self.welcome_text.font()
        font.setPointSize(60)
        font.setBold(True)
        self.welcome_text.setFont(font)
        
        # Set text color to white with a semi-transparent look
        self.welcome_text.setDefaultTextColor(QColor(255, 255, 255, 140))
        
        # Set text width and center-align the text
        self.welcome_text.setTextWidth(300)
        self.welcome_text.setHtml("<div align='center'>Welcome<br>Build Here</div>")
        
        # Center the text (will be properly positioned after view is shown)
        QTimer.singleShot(100, self.center_welcome_text)
    
    def center_welcome_text(self):
        """Center the welcome text in the view after the view is shown"""
        if self.welcome_text:
            # Get scene rect to center the text
            view_center = self.view.mapToScene(self.view.viewport().rect().center())
            text_width = self.welcome_text.boundingRect().width()
            text_height = self.welcome_text.boundingRect().height()
            
            # Position text in the center
            self.welcome_text.setPos(view_center.x() - text_width/2, view_center.y() - text_height/2)
    
    def add_component(self, component_type):
        if component_type == "generator":
            component = GeneratorComponent(0, 0)
            self.scene.addItem(component)
            self.components.append(component)
        elif component_type == "grid_import":
            component = GridImportComponent(0, 0)
            self.scene.addItem(component)
            self.components.append(component)
        elif component_type == "grid_export":
            component = GridExportComponent(0, 0)
            self.scene.addItem(component)
            self.components.append(component)
        elif component_type == "bus":
            component = BusComponent(0, 0)
            self.scene.addItem(component)
            self.components.append(component)
        elif component_type == "load":
            component = LoadComponent(0, 0)
            self.scene.addItem(component)
            self.components.append(component)
        elif component_type == "battery":
            component = BatteryComponent(0, 0)
            self.scene.addItem(component)
            self.components.append(component)
        elif component_type == "cloud_workload":
            component = CloudWorkloadComponent(0, 0)
            self.scene.addItem(component)
            self.components.append(component)
        elif component_type == "solar_panel":
            component = SolarPanelComponent(0, 0)
            self.scene.addItem(component)
            self.components.append(component)
        elif component_type == "tree":
            component = TreeComponent(0, 0)
            self.scene.addItem(component)
            # Do not add trees to the components list as they are decorative
            # and should not affect network connectivity checks
        elif component_type == "bush":
            component = BushComponent(0, 0)
            self.scene.addItem(component)
            # Do not add bushes to the components list as they are decorative
            # and should not affect network connectivity checks
        elif component_type == "pond":
            component = PondComponent(0, 0)
            self.scene.addItem(component)
            # Do not add ponds to the components list as they are decorative
            # and should not affect network connectivity checks
        elif component_type == "house1":
            component = House1Component(0, 0)
            self.scene.addItem(component)
            # Do not add houses to the components list as they are decorative
            # and should not affect network connectivity checks
        elif component_type == "house2":
            component = House2Component(0, 0)
            self.scene.addItem(component)
            # Do not add houses to the components list as they are decorative
            # and should not affect network connectivity checks
        elif component_type == "factory":
            component = FactoryComponent(0, 0)
            self.scene.addItem(component)
            # Do not add factory to the components list as it is decorative
            # and should not affect network connectivity checks
        
        # Hide welcome text after adding the first component (if it's not decorative)
        if component_type in ["generator", "grid_import", "grid_export", "bus", "load", "battery", "cloud_workload", "solar_panel"]:
            if self.welcome_text and self.welcome_text.isVisible():
                self.welcome_text.setVisible(False)
    
    def start_connection(self):
        self.connection_manager.start_connection()
    
    def cancel_connection(self):
        """Cancel the current connection creation"""
        self.connection_manager.cancel_connection()
    
    def handle_connection_click(self, component):
        self.connection_manager.handle_connection_click(component)
    
    def eventFilter(self, obj, event):
        # Handle ESC key press
        if (obj is self.view and 
            event.type() == event.KeyPress and 
            event.key() == Qt.Key_Escape):
            if self.creating_connection:
                self.cancel_connection()
                return True
            # Check if sever connection button is disabled (indicating we're in sever mode)
            elif not self.sever_connection_btn.isEnabled():
                self.connection_manager.cancel_sever_connection()
                return True
        
        # Handle mouse movement for connection line
        if (obj is self.view.viewport() and 
            event.type() == event.MouseMove and 
            self.connection_manager.temp_connection and 
            self.connection_manager.connection_source):
            return self.connection_manager.handle_mouse_move_for_connection(event)
        return super().eventFilter(obj, event)
    
    def set_default_cursor(self):
        """Set the default cursor state when not in connection mode"""
        self.cursor_timer.stop()
        self.view.setCursor(Qt.ArrowCursor)
        self.view.viewport().setCursor(Qt.ArrowCursor)
    
    def check_network_connectivity(self):
        """Check if all components are connected in a single network"""
        if not self.components:
            return False
            
        # Use first component as starting point
        visited = set()
        to_visit = [self.components[0]]
        
        # Perform breadth-first search through connections
        while to_visit:
            current = to_visit.pop(0)
            if current not in visited:
                visited.add(current)
                # Add all connected components to visit
                for conn in current.connections:
                    if conn.source not in visited:
                        to_visit.append(conn.source)
                    if conn.target not in visited:
                        to_visit.append(conn.target)
        
        # Check if all components were visited
        return len(visited) == len(self.components)

    def start_scrubbing(self):
        """Enter scrub mode when slider is pressed"""
        self.is_scrubbing = True
        
        # Cancel any pending scrub timer
        if self.scrub_timer:
            self.scrub_timer.stop()
    
    def stop_scrubbing(self):
        """Exit scrub mode when slider is released"""
        # Update simulation immediately when slider is released
        self.is_scrubbing = False
        self.update_simulation()
    
    def time_slider_changed(self, value):
        # Check network connectivity before updating
        if not self.simulation_engine.simulation_running and not self.check_network_connectivity():
            # Show the same warning as when trying to play with unconnected components
            QMessageBox.warning(self, "Simulation Error",
                              "All components must be connected in a single network to run the simulation.\n\n"
                              "Please ensure all generators and loads are connected before starting.")
            # Reset the slider to 0 since we can't run the simulation
            self.time_slider.setValue(0)
            return
            
        self.simulation_engine.current_time_step = value
        
        # Update time label in the analytics panel even during scrubbing
        # But only show minimal time update info without rendering data
        self.minimal_analytics_update()
        
        # Only update full simulation if not in scrub mode
        if not self.simulation_engine.simulation_running and not self.is_scrubbing:
            self.update_simulation()
    
    def minimal_analytics_update(self):
        """Update only the time display in analytics during scrubbing"""
        if self.is_scrubbing:
            # Pass is_scrubbing=True to prevent chart updates
            self.analytics_panel.update_analytics(
                0,  # power_produced
                0,  # power_consumed
                self.simulation_engine.current_time_step,  # current_time
                0,  # total_capacity
                is_scrubbing=True
            )
    
    def change_simulation_speed(self, index):
        """Change the simulation speed based on the selected option"""
        speeds = [0.1, 1, 2, 3]  # Maps to 0.1x, 1x, 2x, 3x
        self.simulation_speed = speeds[index]
        
        # If simulation is running, restart the timer with the new interval
        if self.simulation_engine.simulation_running:
            self.sim_timer.stop()
            # Base interval is 100ms (0.1 second) for 1x speed - twice as fast as the original
            # Faster speeds use shorter intervals, slower speeds use longer intervals
            interval = int(100 / self.simulation_speed)
            self.sim_timer.start(interval)
    
    def toggle_simulation(self):
        """Toggle the simulation between running and paused"""
        # Check network connectivity before starting simulation
        if not self.simulation_engine.simulation_running and not self.check_network_connectivity():
            QMessageBox.warning(self, "Simulation Error",
                              "All components must be connected in a single network to run the simulation.\n\n"
                              "Please ensure all generators and loads are connected before starting.")
            return
        
        # Make sure we're not in scrub mode when starting playback
        if not self.simulation_engine.simulation_running:
            self.simulation_engine.is_scrubbing = False
            
        self.simulation_engine.simulation_running = not self.simulation_engine.simulation_running
        if self.simulation_engine.simulation_running:
            interval = int(100 / self.simulation_speed)
            self.sim_timer.start(interval)
            self.play_btn.setText("Pause (Space)")
            self.disable_component_buttons(True)
        else:
            self.sim_timer.stop()
            self.play_btn.setText("Play (Space)")
            self.disable_component_buttons(False)
    
    def step_simulation(self, steps):
        # Check if simulation was running but has been stopped (end of timeline)
        if not self.simulation_engine.simulation_running and self.play_btn.text() == "Pause (Space)":
            # Update UI to reflect that simulation has stopped
            self.play_btn.setText("Play (Space)")
            self.sim_timer.stop()
            self.disable_component_buttons(False)
            
        if self.simulation_engine.step_simulation(steps):
            self.time_slider.setValue(self.simulation_engine.current_time_step)
            self.simulation_engine.update_simulation()
    
    def update_simulation(self):
        self.simulation_engine.update_simulation()
    
    def reset_simulation(self):
        self.simulation_engine.current_time_step = 0
        self.simulation_engine.simulation_running = False
        self.simulation_engine.total_energy_imported = 0
        self.simulation_engine.total_energy_exported = 0
        self.simulation_engine.last_time_step = 0
        
        # Reset the gross revenue data
        self.simulation_engine.gross_revenue_data = [0.0] * 8761
        
        # Also reset accumulated revenue in all load components
        for item in self.scene.items():
            if isinstance(item, LoadComponent):
                item.accumulated_revenue = 0.0
                item.update()  # Refresh the visual display
            # Reset accumulated revenue for Cloud Workload components as well
            elif isinstance(item, CloudWorkloadComponent):
                item.accumulated_revenue = 0.0
                item.update()  # Refresh the visual display
        
        self.play_btn.setText("Play (Space)")
        self.time_slider.setValue(0)
        
        # Clear the analytics chart history
        self.analytics_panel.clear_chart_history()
        
        self.update_simulation()
    
    def new_scenario(self):
        """Create a new blank scenario"""
        # First reset the simulation state
        self.reset_simulation()
        
        # Safely handle welcome text before clearing the scene
        self.welcome_text = None  # Clear reference first
        
        # Then create a new blank scenario
        self.model_manager.new_scenario()
        
        # Add new welcome text after the scene has been cleared
        self.add_welcome_text()
    
    def save_scenario(self):
        """Save the current scenario to a file"""
        self.model_manager.save_scenario()
    
    def load_scenario(self):
        """Load a scenario from a file"""
        self.model_manager.load_scenario()

    def create_connection_cursor(self, phase):
        """Create a custom cursor for connection mode with pulsing effect"""
        return self.connection_manager.create_connection_cursor(phase)

    def update_cursor(self):
        """Update the cursor appearance for the pulsing effect"""
        self.connection_manager.update_cursor()

    def autoconnect_all_components(self):
        """Automatically connect all components in the scene to form a valid network"""
        self.connection_manager.autoconnect_all_components()

    def start_sever_connection(self):
        """Start the sever connection mode"""
        self.connection_manager.start_sever_connection()
    
    def handle_sever_connection(self, component):
        """Remove all connections from the selected component"""
        self.connection_manager.handle_sever_connection(component)
    
    def cancel_sever_connection(self):
        """Cancel the sever connection mode"""
        self.connection_manager.cancel_sever_connection()

    def keyPressEvent(self, event):
        """Handle key press events for hotkeys"""
        # Skip if we're typing in a text field
        if isinstance(self.focusWidget(), QLineEdit):
            super().keyPressEvent(event)
            return
            
        key = event.key()
        
        # Space for play/pause - always active regardless of mode
        if key == Qt.Key_Space:
            self.toggle_simulation()
            return
            
        # Delete key for deleting selected component - active regardless of mode
        if key == Qt.Key_Delete:
            # Check if a component is selected and the properties manager has a current component
            if hasattr(self.properties_manager, 'current_component') and self.properties_manager.current_component:
                self.properties_manager.delete_component()
                return
                
        # R key for reset simulation - always active regardless of mode
        if key == Qt.Key_R:
            self.reset_simulation()
            return
            
        # P key to toggle properties panel visibility - always active
        if key == Qt.Key_P:
            if not self.properties_dock.isVisible():
                self.properties_dock.setVisible(True)
                self.position_properties_panel_if_needed()
            else:
                self.properties_dock.setVisible(False)
            return
        
        # Only process if not in connection mode, sever mode, and simulation is not running
        if (not self.creating_connection and 
            self.connection_btn.isEnabled() and 
            self.sever_connection_btn.isEnabled() and
            not self.simulation_engine.simulation_running):
            # G for generator
            if key == Qt.Key_G:
                self.add_component("generator")
            # B for bus
            elif key == Qt.Key_B:
                self.add_component("bus")
            # L for load
            elif key == Qt.Key_L:
                self.add_component("load")
            # I for grid import
            elif key == Qt.Key_I:
                self.add_component("grid_import")
            # E for grid export
            elif key == Qt.Key_E:
                self.add_component("grid_export")
            # S for battery storage
            elif key == Qt.Key_S:
                self.add_component("battery")
            # W for cloud workload
            elif key == Qt.Key_W:
                self.add_component("cloud_workload")
            # C for create connection
            elif key == Qt.Key_C:
                self.start_connection()
            # A for autoconnect
            elif key == Qt.Key_A:
                self.autoconnect_all_components()
        
        super().keyPressEvent(event) 

    def disable_component_buttons(self, disabled):
        """Disable or enable all component and connection manipulation buttons"""
        # Define disabled button style with grey text
        disabled_button_style = "QPushButton { background-color: #3D3D3D; color: #999999; border: 1px solid #555555; border-radius: 3px; padding: 5px; }"
        # Original button style with white text
        enabled_button_style = "QPushButton { background-color: #3D3D3D; color: white; border: 1px solid #555555; border-radius: 3px; padding: 5px; }"
        
        # Use stored references
        for button in self.component_buttons:
            button.setEnabled(not disabled)
            # Update style based on disabled state
            if disabled:
                button.setStyleSheet(disabled_button_style)
            else:
                button.setStyleSheet(enabled_button_style)

    def closeEvent(self, event):
        """Handle application close event with confirmation dialogs"""
        # First check if simulation is running and confirm exit
        if self.simulation_engine.simulation_running:
            reply = QMessageBox.question(
                self, 
                "Confirm Exit", 
                "The simulation is still running. Are you sure you want to quit?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                event.ignore()
                return
                
        # Then prompt to save the scenario
        reply = QMessageBox.question(
            self, 
            "Save Before Exit", 
            "Would you like to save your scenario before exiting?",
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
            QMessageBox.Yes
        )
        
        if reply == QMessageBox.Cancel:
            event.ignore()
        elif reply == QMessageBox.Yes:
            self.save_scenario()
            event.accept()
        else:  # QMessageBox.No
            event.accept() 

    def zoom_changed(self, value):
        """Handle zoom slider value changes"""
        # Convert slider value (40-100) to zoom factor (0.4-1.0)
        zoom_factor = value / 100.0
        
        # Update the zoom label
        self.zoom_label.setText(f"{zoom_factor:.1f}x")
        
        # Save the current zoom level
        self.current_zoom = zoom_factor
        
        # Create a transform for scaling
        transform = self.view.transform()
        
        # Reset the transform first
        transform.reset()
        
        # Create a new transform with the zoom factor
        transform.scale(zoom_factor, zoom_factor)
        
        # Apply the transform to the view
        self.view.setTransform(transform)
        
        # Update the scene
        self.view.update() 

    def take_screenshot(self):
        """Take a screenshot of the modeling view area and copy to clipboard"""
        # Create a pixmap the size of the viewport
        pixmap = QPixmap(self.view.viewport().size())
        pixmap.fill(Qt.transparent)
        
        # Create painter for the pixmap
        painter = QPainter(pixmap)
        
        # Render the view onto the pixmap
        self.view.render(painter)
        
        # End painting
        painter.end()
        
        # Copy pixmap to clipboard
        clipboard = QApplication.clipboard()
        clipboard.setPixmap(pixmap)
        
        # Show confirmation to user
        QMessageBox.information(self, "Screenshot", "Screenshot copied to clipboard") 

    def toggle_background(self):
        """Cycle through background options"""
        # Cycle through background modes: 0 -> 1 -> 2 -> 0
        self.background_mode = (self.background_mode + 1) % 3
        
        # Update background
        self.scene.set_background(self.background_mode)
        
        # Update button text
        if self.background_mode == 0:
            self.background_toggle_btn.setText("🌄 Background 1")
        elif self.background_mode == 1:
            self.background_toggle_btn.setText("🌄 Background 2")
        else:  # mode == 2
            self.background_toggle_btn.setText("🌄 Background Off")
        
        # Update view
        self.view.update()

    def show_components_panel(self):
        """Show the components panel if it's hidden"""
        self.component_dock.setVisible(True)
    
    def position_properties_panel_if_needed(self):
        """Position the properties panel 475px up and 725px right from the center of the screen if not already positioned"""
        if not self.properties_panel_positioned and self.properties_dock.isFloating():
            # Get the screen geometry
            screen_rect = QApplication.desktop().screenGeometry()
            screen_center = screen_rect.center()
            
            # Calculate the new position 
            panel_width = self.properties_dock.width()
            panel_height = self.properties_dock.height()
            new_x = screen_center.x() + 725 - panel_width // 2
            new_y = screen_center.y() - 475 - panel_height // 2
            
            # Ensure the panel stays within the screen boundaries
            new_x = max(0, min(new_x, screen_rect.width() - panel_width))
            new_y = max(0, min(new_y, screen_rect.height() - panel_height))
            
            # Set the position
            self.properties_dock.move(new_x, new_y)
            
            # Mark as positioned
            self.properties_panel_positioned = True
    
    def show_properties_panel(self):
        """Show the properties panel if it's hidden"""
        self.properties_dock.setVisible(True)
        self.position_properties_panel_if_needed()
    
    def show_analytics_panel(self):
        """Show the analytics panel if it's hidden"""
        self.analytics_dock.setVisible(True) 