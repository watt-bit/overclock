from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QPushButton, QSlider, QGraphicsView, QDockWidget, 
                            QToolBar, 
                            QAction, QMenu, QFrame,
                            QToolButton, QSizePolicy, QGraphicsTextItem)
from PyQt5.QtCore import Qt, QRectF, QRect, QTimer, QTime, QSize
from PyQt5.QtGui import QPainter, QPen, QPixmap, QColor, QKeySequence, QPainterPath, QLinearGradient, QFontMetrics, QIcon
import math

# Import or reference modules and classes needed from main_window
from .analytics import AnalyticsPanel
from .tiled_background_widget import TiledBackgroundWidget
from .terminal_widget import TerminalWidget
from .selected_component_display import SelectedComponentDisplay
from src.utils.resource import resource_path
from .classes.gradient_border_text import GradientBorderText
from .classes.bordered_main_widget import BorderedMainWidget

# Export this button style as a module-level variable for use in other files
opaque_button_style = """
    QPushButton { 
        background-color: #3D3D3D; 
        color: white; 
        border: 1px solid #777777; 
        border-radius: 3px; 
    }
    QPushButton:hover { 
        background-color: #7D7D7D; 
        border: 1px solid #BBBBBB;
    }
    QPushButton:pressed { 
        background-color: #2D2D2D; 
        border: 1px solid #777777;
    }
"""

# Custom Widget for Main Layout
# BorderedMainWidget has been moved to src/ui/classes/bordered_main_widget.py

class UIInitializer:
    @staticmethod
    def initialize_ui(main_window):
        """Initialize the UI components for the PowerSystemSimulator"""
        # Main layout
        main_widget = BorderedMainWidget()  # Use our custom widget with border
        main_window.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(4, 4, 4, 4)  # Use 10px margins to account for the border
        
        # Set the corners to give priority to left and right dock areas
        main_window.setCorner(Qt.TopLeftCorner, Qt.LeftDockWidgetArea)
        main_window.setCorner(Qt.TopRightCorner, Qt.RightDockWidgetArea)
        main_window.setCorner(Qt.BottomLeftCorner, Qt.LeftDockWidgetArea)
        main_window.setCorner(Qt.BottomRightCorner, Qt.RightDockWidgetArea)
        
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
        main_window.setStyleSheet(dock_title_style + """
        QToolTip { 
            background-color: #2A2A2A;
            color: white;
            border: 1px solid #555555;
            border-radius: 3px;
            padding: 5px;
            font-weight: bold;
            font-size: 12px;
            opacity: 255;
        }
        """)
        
        # Create canvas for drag and drop
        main_window.view = QGraphicsView(main_window.scene)
        main_window.view.setDragMode(QGraphicsView.ScrollHandDrag)
        main_window.view.setRenderHint(QPainter.Antialiasing)
        main_window.view.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        main_window.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        main_window.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Set initial scaling for view
        main_window.current_zoom = 1.0
        
        # Apply initial zoom transform
        transform = main_window.view.transform()
        transform.scale(main_window.current_zoom, main_window.current_zoom)
        main_window.view.setTransform(transform)
        
        # Enable key events on the view
        main_window.view.setFocusPolicy(Qt.StrongFocus)
        
        # Install event filter for key events
        main_window.view.installEventFilter(main_window)
        
        # Create Overclock logo overlay
        main_window.logo_overlay = QLabel(main_window.view)
        logo_pixmap = QPixmap(resource_path("src/ui/assets/overclocklogo.png"))
        if not logo_pixmap.isNull():
            # Calculate 10% of the original size while maintaining aspect ratio
            scaled_width = int(logo_pixmap.width() * 0.1)
            scaled_height = int(logo_pixmap.height() * 0.1)
            scaled_logo = logo_pixmap.scaled(scaled_width, scaled_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            main_window.logo_overlay.setPixmap(scaled_logo)
            main_window.logo_overlay.setAttribute(Qt.WA_TransparentForMouseEvents)  # Make it click-through
            
            # Position in bottom right corner with padding
            main_window.logo_overlay.move(main_window.view.width() - scaled_width - 5, main_window.view.height() - scaled_height + 5)
            
            # Connect to view's resize event to maintain position
            main_window.view.resizeEvent = main_window.on_view_resize
            
            # Make the logo visible
            main_window.logo_overlay.show()
        
        # Create CAPEX label overlay in bottom left corner
        main_window.capex_label = QLabel(main_window.view)
        main_window.capex_label.setText("CAPEX <span style='color: #FFCA28;'>$0</span>")
        main_window.capex_label.setTextFormat(Qt.RichText)
        main_window.capex_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                font-size: 14px;
                background-color: #262626; 
                color: rgba(255, 255, 255, 0.8);
                border-radius: 3px; 
                padding: 5px;
                border: 1px solid #555555;
                font-family: Menlo, Consolas, Courier, monospace; 
            }
        """)
        main_window.capex_label.adjustSize()  # Size to fit content
        main_window.capex_label.setAttribute(Qt.WA_TransparentForMouseEvents)  # Make it click-through
        
        # Create IRR label overlay below CAPEX label
        main_window.irr_label = QLabel(main_window.view)
        main_window.irr_label.setText("Refresh Cycle IRR: --.-% (12 Mo.) | --.-% (18 Mo.) | --.-% (36 Mo.)")
        main_window.irr_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                font-size: 14px;
                background-color: #262626; 
                color: rgba(255, 255, 255, 0.8); 
                border-radius: 3px; 
                padding: 5px; 
                border: 1px solid #555555; 
                font-family: Menlo, Consolas, Courier, monospace; 
            }
        """)
        main_window.irr_label.adjustSize()  # Size to fit content
        main_window.irr_label.setAttribute(Qt.WA_TransparentForMouseEvents)  # Make it click-through
        
        # Position labels in bottom left corner with padding
        # CAPEX label is positioned 35px up from the bottom
        main_window.capex_label.move(10, main_window.view.height() - main_window.capex_label.height() - 65)
        # IRR label is positioned below the CAPEX label
        main_window.irr_label.move(10, main_window.view.height() - main_window.irr_label.height() - 20)
        
        # Make the labels visible
        main_window.capex_label.show()
        main_window.irr_label.show()
        
        # Create Mode/Historian toggle button in top-left corner
        main_window.mode_toggle_btn = QPushButton("🏗️ Build", main_window.view)
        main_window.mode_toggle_btn.setStyleSheet("""
            QPushButton { 
                background-color: #3D3D3D; 
                color: white; 
                border: 1px solid #777777; 
                border-radius: 3px; 
                padding: 5px; 
                font-family: Menlo, Consolas, Courier, monospace;
                font-size: 12px; 
                font-weight: bold;
            }
            QPushButton:hover { 
                background-color: #6D6D6D; 
                border: 1px solid #BBBBBB;
            }
            QPushButton:pressed { 
                background-color: #2D2D2D; 
                border: 1px solid #777777;
                padding: 4px; 
            }
        """)
        main_window.mode_toggle_btn.clicked.connect(lambda: main_window.cancel_connection_if_active(main_window.toggle_mode_button))
        main_window.mode_toggle_btn.setToolTip("Build / Historian Mode ( \\ )")
        # Position in top left corner with padding
        main_window.mode_toggle_btn.move(10, 10)
        # Make the button visible
        main_window.mode_toggle_btn.show()
        main_window.mode_toggle_btn.setFixedWidth(125)
        
        # Create a custom class for the analytics toggle button
        class AnalyticsToggleButton(QLabel):
            def __init__(self, parent=None):
                super().__init__(parent)
                self.normal_pixmap = QPixmap(resource_path("src/ui/assets/analyticsbutton.png"))
                self.hover_pixmap = QPixmap(resource_path("src/ui/assets/analyticsbuttonhover.png"))
                self.clicked_pixmap = QPixmap(resource_path("src/ui/assets/analyticsbuttonclick.png"))
                
                # Scale pixmaps to 40x40 while maintaining aspect ratio
                self.normal_pixmap = self.normal_pixmap.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.hover_pixmap = self.hover_pixmap.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.clicked_pixmap = self.clicked_pixmap.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                
                # Set the default pixmap
                self.setPixmap(self.normal_pixmap)
                self.setFixedSize(80, 80)
                self.is_pressed = False
                
            def mousePressEvent(self, event):
                self.is_pressed = True
                self.setPixmap(self.clicked_pixmap)
                super().mousePressEvent(event)
                
            def mouseReleaseEvent(self, event):
                self.is_pressed = False
                self.setPixmap(self.hover_pixmap if self.underMouse() else self.normal_pixmap)
                # Emit a fake click signal
                if self.underMouse() and hasattr(self, 'on_click') and callable(self.on_click):
                    self.on_click()
                super().mouseReleaseEvent(event)
                
            def enterEvent(self, event):
                if not self.is_pressed:
                    self.setPixmap(self.hover_pixmap)
                super().enterEvent(event)
                
            def leaveEvent(self, event):
                if not self.is_pressed:
                    self.setPixmap(self.normal_pixmap)
                super().leaveEvent(event)
        
        # Create horizontal container for analytics button and future UI components
        main_window.analytics_container = QWidget(main_window.view)
        main_window.analytics_container_layout = QHBoxLayout(main_window.analytics_container)
        main_window.analytics_container_layout.setContentsMargins(0, 0, 0, 0)
        main_window.analytics_container_layout.setSpacing(5)  # 5px spacing between items
        
        # Create Selected Component Display
        main_window.selected_component_display = SelectedComponentDisplay(main_window.analytics_container)
        
        # Create Analytics toggle button
        main_window.analytics_toggle_btn = AnalyticsToggleButton(main_window.analytics_container)
        # Set the click handler
        main_window.analytics_toggle_btn.on_click = lambda: main_window.cancel_connection_if_active(main_window.toggle_analytics_panel)
        
        # Add the selected component display and analytics button to the container
        main_window.analytics_container_layout.addWidget(main_window.selected_component_display)
        main_window.analytics_container_layout.addWidget(main_window.analytics_toggle_btn)
        
        # Position container in top right corner with padding (adjusted for wider container)
        main_window.analytics_container.move(main_window.view.width() - 390, 0)
        # Make the container visible
        main_window.analytics_container.show()
        
        # Component palette
        main_window.component_dock = QDockWidget("Components", main_window)
        main_window.component_dock.setObjectName("component_dock")
        # Remove title bar and prevent undocking/closing
        main_window.component_dock.setTitleBarWidget(QWidget())
        main_window.component_dock.setFeatures(QDockWidget.NoDockWidgetFeatures)
        # Set fixed width to 200px
        main_window.component_dock.setFixedWidth(250)
        # Ensure no borders are visible
        main_window.component_dock.setStyleSheet("QDockWidget { border: none; }")
        
        # Use TiledBackgroundWidget from main_window
        # We need to use the class from main_window instead of creating it here
        component_widget = TiledBackgroundWidget()
        component_widget.set_background(resource_path("src/ui/assets/backgroundstars.png"))
        component_layout = QVBoxLayout(component_widget)
        
        # Add component panel top image
        top_image_label = QLabel()
        top_image_label.setStyleSheet("border: none;")
        top_pixmap = QPixmap(resource_path("src/ui/assets/componentspaneltop.png"))
        if not top_pixmap.isNull():
            # Will set the actual image after layout is set up
            top_image_label.setAlignment(Qt.AlignCenter)
            top_image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            component_layout.addWidget(top_image_label)

        # # Add WBR logo overlay
        # main_window.wbr_logo_label = QLabel(top_image_label)  # Set parent to top_image_label
        # main_window.wbr_logo_label.setStyleSheet("border: none; background: transparent;")
        # wbr_logo_pixmap = QPixmap(resource_path("src/ui/assets/wbrlogo.png"))
        # if not wbr_logo_pixmap.isNull():
        #     # Scale to 125px width while preserving aspect ratio
        #     aspect_ratio = wbr_logo_pixmap.height() / wbr_logo_pixmap.width()
        #     scaled_height = int(125 * aspect_ratio)
        #     scaled_logo = wbr_logo_pixmap.scaled(125, scaled_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        #     main_window.wbr_logo_label.setPixmap(scaled_logo)
        #     # Will position after top_image_label is sized

        # Use the module-level opaque_button_style variable instead of redefining it
        
        generator_btn = QPushButton()
        generator_btn.setToolTip("🔥 (G)as Generator")
        generator_pixmap = QPixmap(resource_path("src/ui/assets/menu_icons/gasgenerator.png"))
        generator_icon = QIcon(generator_pixmap)
        generator_btn.setIcon(generator_icon)
        generator_btn.setIconSize(QSize(50, 50))
        generator_btn.setFixedSize(50, 50)
        generator_btn.setStyleSheet(opaque_button_style)
        generator_btn.clicked.connect(lambda: main_window.cancel_connection_if_active(main_window.add_component, "generator"))
        
        battery_btn = QPushButton()
        battery_btn.setToolTip("🔋 Battery (S)torage")
        battery_pixmap = QPixmap(resource_path("src/ui/assets/menu_icons/batterystorage.png"))
        battery_icon = QIcon(battery_pixmap)
        battery_btn.setIcon(battery_icon)
        battery_btn.setIconSize(QSize(50, 50))
        battery_btn.setFixedSize(50, 50)
        battery_btn.setStyleSheet(opaque_button_style)
        battery_btn.clicked.connect(lambda: main_window.cancel_connection_if_active(main_window.add_component, "battery"))
                
        bus_btn = QPushButton()
        bus_btn.setToolTip("⚡ Electrical (B)us")
        bus_pixmap = QPixmap(resource_path("src/ui/assets/menu_icons/electricalbus.png"))
        bus_icon = QIcon(bus_pixmap)
        bus_btn.setIcon(bus_icon)
        bus_btn.setIconSize(QSize(50, 50))
        bus_btn.setFixedSize(50, 50)
        bus_btn.setStyleSheet(opaque_button_style)
        bus_btn.clicked.connect(lambda: main_window.cancel_connection_if_active(main_window.add_component, "bus"))

        load_btn = QPushButton()
        load_btn.setToolTip("💡 Electrical (L)oad")
        load_pixmap = QPixmap(resource_path("src/ui/assets/menu_icons/electricalload.png"))
        load_icon = QIcon(load_pixmap)
        load_btn.setIcon(load_icon)
        load_btn.setIconSize(QSize(50, 50))
        load_btn.setFixedSize(50, 50)
        load_btn.setStyleSheet(opaque_button_style)
        load_btn.clicked.connect(lambda: main_window.cancel_connection_if_active(main_window.add_component, "load"))
        
        cloud_workload_btn = QPushButton()
        cloud_workload_btn.setToolTip("🌐 Cloud (W)orkload")
        cloud_workload_pixmap = QPixmap(resource_path("src/ui/assets/menu_icons/cloudworkload.png"))
        cloud_workload_icon = QIcon(cloud_workload_pixmap)
        cloud_workload_btn.setIcon(cloud_workload_icon)
        cloud_workload_btn.setIconSize(QSize(50, 50))
        cloud_workload_btn.setFixedSize(50, 50)
        cloud_workload_btn.setStyleSheet(opaque_button_style)
        cloud_workload_btn.clicked.connect(lambda: main_window.cancel_connection_if_active(main_window.add_component, "cloud_workload"))

        # Create Solar Array button
        solar_array_btn = QPushButton()
        solar_array_btn.setToolTip("Solar Array")
        solar_array_pixmap = QPixmap(resource_path("src/ui/assets/menu_icons/solarpanel.png"))
        solar_array_icon = QIcon(solar_array_pixmap)
        solar_array_btn.setIcon(solar_array_icon)
        solar_array_btn.setIconSize(QSize(50, 50))
        solar_array_btn.setFixedSize(50, 50)
        solar_array_btn.setStyleSheet(opaque_button_style)
        solar_array_btn.clicked.connect(lambda: main_window.cancel_connection_if_active(main_window.add_component, "solar_panel"))
        
        # Create Wind Turbine button
        wind_turbine_btn = QPushButton()
        wind_turbine_btn.setToolTip("Wind Turbine")
        wind_turbine_pixmap = QPixmap(resource_path("src/ui/assets/menu_icons/windturbine.png"))
        wind_turbine_icon = QIcon(wind_turbine_pixmap)
        wind_turbine_btn.setIcon(wind_turbine_icon)
        wind_turbine_btn.setIconSize(QSize(50, 50))
        wind_turbine_btn.setFixedSize(50, 50)
        wind_turbine_btn.setStyleSheet(opaque_button_style)
        wind_turbine_btn.clicked.connect(lambda: main_window.cancel_connection_if_active(main_window.add_component, "wind_turbine"))

        grid_import_btn = QPushButton()
        grid_import_btn.setToolTip("Grid (I)mport Pathway")
        grid_import_pixmap = QPixmap(resource_path("src/ui/assets/menu_icons/gridimport.png"))
        grid_import_icon = QIcon(grid_import_pixmap)
        grid_import_btn.setIcon(grid_import_icon)
        grid_import_btn.setIconSize(QSize(50, 50))
        grid_import_btn.setFixedSize(50, 50)
        grid_import_btn.setStyleSheet(opaque_button_style)
        grid_import_btn.clicked.connect(lambda: main_window.cancel_connection_if_active(main_window.add_component, "grid_import"))
        
        grid_export_btn = QPushButton()
        grid_export_btn.setToolTip("Grid (E)xport Pathway")
        grid_export_pixmap = QPixmap(resource_path("src/ui/assets/menu_icons/gridexport.png"))
        grid_export_icon = QIcon(grid_export_pixmap)
        grid_export_btn.setIcon(grid_export_icon)
        grid_export_btn.setIconSize(QSize(50, 50))
        grid_export_btn.setFixedSize(50, 50)
        grid_export_btn.setStyleSheet(opaque_button_style)
        grid_export_btn.clicked.connect(lambda: main_window.cancel_connection_if_active(main_window.add_component, "grid_export"))
        
        main_window.connection_btn = QPushButton()
        main_window.connection_btn.setToolTip("Create (C)onnection")
        connection_pixmap = QPixmap(resource_path("src/ui/assets/menu_icons/createconnection.png"))
        connection_icon = QIcon(connection_pixmap)
        main_window.connection_btn.setIcon(connection_icon)
        main_window.connection_btn.setIconSize(QSize(50, 50))
        main_window.connection_btn.setFixedSize(50, 50)
        main_window.connection_btn.setStyleSheet(opaque_button_style)
        main_window.connection_btn.clicked.connect(main_window.start_connection)
        
        autoconnect_btn = QPushButton()
        autoconnect_btn.setToolTip("(A)utoconnect All")
        autoconnect_pixmap = QPixmap(resource_path("src/ui/assets/menu_icons/autoconnectall.png"))
        autoconnect_icon = QIcon(autoconnect_pixmap)
        autoconnect_btn.setIcon(autoconnect_icon)
        autoconnect_btn.setIconSize(QSize(50, 50))
        autoconnect_btn.setFixedSize(50, 50)
        autoconnect_btn.setStyleSheet(opaque_button_style)
        autoconnect_btn.clicked.connect(lambda: main_window.cancel_connection_if_active(main_window.autoconnect_all_components))

        # Create a popup menu for props
        props_menu = QMenu(main_window)
        
        # Add actions for each prop type
        tree_action = props_menu.addAction("Add Tree")
        tree_action.triggered.connect(lambda: main_window.cancel_connection_if_active(main_window.add_component, "tree"))
        
        bush_action = props_menu.addAction("Add Bush")
        bush_action.triggered.connect(lambda: main_window.cancel_connection_if_active(main_window.add_component, "bush"))
        
        pond_action = props_menu.addAction("Add Pond")
        pond_action.triggered.connect(lambda: main_window.cancel_connection_if_active(main_window.add_component, "pond"))
        
        house1_action = props_menu.addAction("Add House")
        house1_action.triggered.connect(lambda: main_window.cancel_connection_if_active(main_window.add_component, "house1"))
        
        house2_action = props_menu.addAction("Add Greenhouse")
        house2_action.triggered.connect(lambda: main_window.cancel_connection_if_active(main_window.add_component, "house2"))
        
        factory_action = props_menu.addAction("Add Factory")
        factory_action.triggered.connect(lambda: main_window.cancel_connection_if_active(main_window.add_component, "factory"))
        
        trad_data_center_action = props_menu.addAction("Add Data Center")
        trad_data_center_action.triggered.connect(lambda: main_window.cancel_connection_if_active(main_window.add_component, "traditional_data_center"))
        
        distribution_pole_action = props_menu.addAction("Add Distribution Pole")
        distribution_pole_action.triggered.connect(lambda: main_window.cancel_connection_if_active(main_window.add_component, "distribution_pole"))
        
        # Create the Add Props button with dropdown menu
        main_window.props_btn = QPushButton()
        main_window.props_btn.setToolTip("🏡 Add Props")
        props_pixmap = QPixmap(resource_path("src/ui/assets/menu_icons/props.png"))
        props_icon = QIcon(props_pixmap)
        main_window.props_btn.setIcon(props_icon)
        main_window.props_btn.setIconSize(QSize(50, 50))
        main_window.props_btn.setFixedSize(50, 50)
        main_window.props_btn.setStyleSheet(opaque_button_style)
        main_window.props_btn.clicked.connect(lambda: main_window.cancel_connection_if_active(lambda: props_menu.exec_(main_window.props_btn.mapToGlobal(main_window.props_btn.rect().bottomLeft()))))
        
        # Create a horizontal layout for the first row of buttons
        first_row_layout = QHBoxLayout()
        first_row_layout.addWidget(generator_btn)
        first_row_layout.addWidget(load_btn)
        first_row_layout.addWidget(battery_btn)
        first_row_layout.addWidget(cloud_workload_btn)

        # Add the horizontal layout to the main component layout
        component_layout.addLayout(first_row_layout)
        
        # Create a horizontal layout for the second row of buttons
        second_row_layout = QHBoxLayout()
        second_row_layout.addWidget(solar_array_btn)
        second_row_layout.addWidget(wind_turbine_btn)
        second_row_layout.addWidget(bus_btn)
        second_row_layout.addWidget(grid_import_btn)
        
        # Add the second horizontal layout to the main component layout
        component_layout.addLayout(second_row_layout)
        
        # Create a horizontal layout for the third row of buttons
        third_row_layout = QHBoxLayout()
        third_row_layout.addWidget(grid_export_btn)
        third_row_layout.addWidget(main_window.connection_btn)
        third_row_layout.addWidget(autoconnect_btn)
        third_row_layout.addWidget(main_window.props_btn)
        
        # Add the third horizontal layout to the main component layout
        component_layout.addLayout(third_row_layout)
        
        # Add the terminal widget below the component buttons
        main_window.terminal_widget = TerminalWidget()
        # Make the terminal widget expand to fill available space
        main_window.terminal_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        component_layout.addWidget(main_window.terminal_widget)
        
        # Now that we have a button, set the top image size to match the full component width
        if not top_pixmap.isNull():
            # Create a timer to update the image once the widget is visible
            update_timer = QTimer(main_window)
            update_timer.setSingleShot(True)
            
            def update_top_image():
                if component_widget.isVisible() and component_widget.width() > 0:
                    width = component_widget.width() - component_layout.contentsMargins().left() - component_layout.contentsMargins().right()
                    top_aspect_ratio = top_pixmap.height() / top_pixmap.width()
                    top_scaled_height = int(width * top_aspect_ratio)
                    scaled_top_pixmap = top_pixmap.scaled(width, top_scaled_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    top_image_label.setPixmap(scaled_top_pixmap)
                else:
                    # Try again in 100ms if widget not visible yet
                    update_timer.start(100)
            
            update_timer.timeout.connect(update_top_image)
            update_timer.start(100)  # Start timer to update image after UI is shown
        
        # Store references to all component and connection buttons for later enabling/disabling
        main_window.component_buttons = [
            generator_btn, 
            grid_import_btn, 
            grid_export_btn, 
            bus_btn, 
            load_btn, 
            battery_btn,
            cloud_workload_btn,
            solar_array_btn,
            wind_turbine_btn,
            main_window.props_btn,
            main_window.connection_btn,
            autoconnect_btn
        ]
        
        main_window.component_dock.setWidget(component_widget)
        main_window.addDockWidget(Qt.LeftDockWidgetArea, main_window.component_dock)
        
        # Properties panel - positioned as overlay on view like analytics container
        main_window.properties_dock = QDockWidget("Properties", main_window.view)
        main_window.properties_dock.setObjectName("properties_dock")
        main_window.properties_dock.setWidget(main_window.properties_manager.properties_widget)
        main_window.properties_dock.setStyleSheet("QDockWidget { background-color: rgba(37, 47, 52, 0.75); border: none; }")
        
        # Remove title bar and prevent undocking/closing
        main_window.properties_dock.setTitleBarWidget(QWidget())
        main_window.properties_dock.setFeatures(QDockWidget.NoDockWidgetFeatures)
        
        # Set fixed width of 300px while allowing height to adjust to contents
        main_window.properties_dock.setFixedWidth(300)
        main_window.properties_dock.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        
        # Position panel: right edge 90px from right side, top edge 75px from top
        main_window.properties_dock.move(main_window.view.width() - 300 - 90, 52)
        
        # Make properties panel hidden by default
        main_window.properties_dock.setVisible(False)
        main_window.properties_dock.show()
        
        # Analytics panel
        main_window.analytics_dock = QDockWidget("Analytics", main_window)
        main_window.analytics_dock.setObjectName("analytics_dock")
        # Remove title bar and prevent undocking/closing
        main_window.analytics_dock.setTitleBarWidget(QWidget())
        main_window.analytics_dock.setFeatures(QDockWidget.NoDockWidgetFeatures)
        # Ensure no borders are visible
        main_window.analytics_dock.setStyleSheet("QDockWidget { border: none; }")
        main_window.analytics_panel = AnalyticsPanel()
        main_window.analytics_dock.setWidget(main_window.analytics_panel)
        main_window.addDockWidget(Qt.RightDockWidgetArea, main_window.analytics_dock)
        # Make analytics panel hidden by default
        main_window.analytics_dock.setVisible(False)
        
        # Time controls
        time_dock = QDockWidget("Simulation Controls", main_window)
        # Remove title bar and prevent undocking/closing
        time_dock.setTitleBarWidget(QWidget())
        time_dock.setFeatures(QDockWidget.NoDockWidgetFeatures)
        # Set fixed height to 70px
        time_dock.setFixedHeight(45)
        # Ensure no borders are visible
        time_dock.setStyleSheet("QDockWidget { border: none; }")
        
        time_widget = TiledBackgroundWidget()
        time_widget.set_background(resource_path("src/ui/assets/backgroundstars.png"))
        time_layout = QVBoxLayout(time_widget)
        time_layout.setContentsMargins(0, 0, 0, 0)
        
        time_controls = QHBoxLayout()
        
        # Define common button style
        common_button_style = """
            QPushButton { 
                border: 1px solid #555555; 
                border-radius: 3px; 
                padding: 5px; 
            }
            QPushButton:hover { 
                border: 1px solid #666666;
                background-color: rgba(255, 255, 255, 0.1); 
            }
            QPushButton:pressed { 
                border: 2px solid #777777;
                padding: 4px; 
                background-color: rgba(0, 0, 0, 0.1);
            }
        """
        # Style for default grey buttons
        default_button_style = """
            QPushButton { 
                background-color: #3D3D3D; 
                color: white; 
                border: 1px solid #555555; 
                border-radius: 3px; 
                padding: 5px;
                font-size: 14px;
            }
            QPushButton:hover { 
                background-color: #4D4D4D; 
                border: 1px solid #666666;
            }
            QPushButton:pressed { 
                background-color: #2D2D2D; 
                border: 2px solid #777777;
                padding: 4px; 
            }
        """
        
        # Create a custom button class for icon-based buttons that change on hover/press
        class IconStateButton(QLabel):
            def __init__(self, normal_icon_path, hover_icon_path=None, pressed_icon_path=None, size=(25, 25), parent=None):
                super().__init__(parent)
                
                # Load the normal icon
                self.normal_pixmap = QPixmap(resource_path(normal_icon_path))
                
                # Load hover and pressed icons
                if hover_icon_path:
                    self.hover_pixmap = QPixmap(resource_path(hover_icon_path))
                else:
                    self.hover_pixmap = self.normal_pixmap  # Fallback to normal if not provided
                
                if pressed_icon_path:
                    self.pressed_pixmap = QPixmap(resource_path(pressed_icon_path))
                else:
                    self.pressed_pixmap = self.normal_pixmap  # Fallback to normal if not provided
                
                # Scale pixmaps if needed
                if size:
                    self.normal_pixmap = self.normal_pixmap.scaled(size[0], size[1], Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self.hover_pixmap = self.hover_pixmap.scaled(size[0], size[1], Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self.pressed_pixmap = self.pressed_pixmap.scaled(size[0], size[1], Qt.KeepAspectRatio, Qt.SmoothTransformation)
                
                # Set the default pixmap
                self.setPixmap(self.normal_pixmap)
                self.setFixedSize(size[0], size[1])
                self.is_pressed = False
                self.on_click = None
                
            def mousePressEvent(self, event):
                self.is_pressed = True
                self.setPixmap(self.pressed_pixmap)
                super().mousePressEvent(event)
                
            def mouseReleaseEvent(self, event):
                self.is_pressed = False
                self.setPixmap(self.hover_pixmap if self.underMouse() else self.normal_pixmap)
                # Emit a fake click signal
                if self.underMouse() and self.on_click:
                    self.on_click()
                super().mouseReleaseEvent(event)
                
            def enterEvent(self, event):
                if not self.is_pressed:
                    self.setPixmap(self.hover_pixmap)
                super().enterEvent(event)
                
            def leaveEvent(self, event):
                if not self.is_pressed:
                    self.setPixmap(self.normal_pixmap)
                super().leaveEvent(event)
                
            def setToolTip(self, text):
                super().setToolTip(text)
        
        # Replace play button with custom button
        main_window.play_btn = IconStateButton(
            "src/ui/assets/simulation_controls/playpausebutton.png",
            hover_icon_path="src/ui/assets/simulation_controls/playpausebuttonhover.png",
            pressed_icon_path="src/ui/assets/simulation_controls/playpausebuttonpress.png",
            size=(40, 40)
        )
        main_window.play_btn.setToolTip("Run/Pause (Space)")
        main_window.play_btn.on_click = lambda: main_window.cancel_connection_if_active(main_window.toggle_simulation)
        
        # Replace reset button with custom button
        main_window.reset_btn = IconStateButton(
            "src/ui/assets/simulation_controls/resetbutton.png",
            hover_icon_path="src/ui/assets/simulation_controls/resetbuttonhover.png",
            pressed_icon_path="src/ui/assets/simulation_controls/resetbuttonpress.png",
            size=(30, 30)
        )
        main_window.reset_btn.setToolTip("🔴 (R)eset")
        main_window.reset_btn.on_click = lambda: main_window.cancel_connection_if_active(main_window.reset_simulation)
        
        # Add speed control
        speed_label = QLabel("⏩ Speed:")
        main_window.speed_selector = QPushButton("▶▷▷")
        main_window.speed_selector.clicked.connect(lambda: main_window.cancel_connection_if_active(main_window.cycle_simulation_speed))
        main_window.speed_selector.setStyleSheet("""
            QPushButton { 
                background-color: #3D3D3D; 
                color: white; 
                border: 1px solid #555555; 
                border-radius: 3px; 
                padding: 4px; 
                font-weight: bold; 
                font-size: 16px;
            }
            QPushButton:hover { 
                background-color: #4D4D4D; 
                border: 1px solid #666666;
            }
            QPushButton:pressed { 
                background-color: #2D2D2D; 
                border: 2px solid #777777;
                padding: 3px; 
            }
        """)
        main_window.speed_selector.setFixedWidth(90)  # Set minimum width to prevent text cutoff
        
        # Add zoom control to time controls (moved from toolbar)
        zoom_label = QLabel("🔭")
        zoom_label.setStyleSheet("font-size: 16px;")
        main_window.zoom_slider = QSlider(Qt.Horizontal)
        main_window.zoom_slider.setMinimum(40)  # 0.4x zoom (changed from 20/0.2x)
        main_window.zoom_slider.setMaximum(100)  # 1.0x zoom
        main_window.zoom_slider.setValue(100)    # Default to 1.0x
        main_window.zoom_slider.setFixedWidth(150)
        main_window.zoom_slider.valueChanged.connect(lambda value: main_window.cancel_connection_if_active(main_window.zoom_changed, value))
        main_window.zoom_slider.setStyleSheet("QSlider::groove:horizontal { background: #3D3D3D; height: 8px; border-radius: 4px; } QSlider::handle:horizontal { background: #5D5D5D; width: 16px; margin: -4px 0; border-radius: 8px; }")
        
        # Add screenshot button
        main_window.screenshot_btn = IconStateButton(
            "src/ui/assets/simulation_controls/screenshotbutton.png",
            hover_icon_path="src/ui/assets/simulation_controls/screenshotbuttonhover.png",
            pressed_icon_path="src/ui/assets/simulation_controls/screenshotbuttonpress.png",
            size=(40, 40)
        )
        main_window.screenshot_btn.setToolTip("📷 Take Screenshot")
        main_window.screenshot_btn.on_click = lambda: main_window.cancel_connection_if_active(lambda: (
            main_window.centralWidget().trigger_dark_gray_flash(),
            main_window.take_screenshot()
        ))

        # Add Autocomplete button
        main_window.autocomplete_btn = IconStateButton(
            "src/ui/assets/simulation_controls/autocompletebutton.png",
            hover_icon_path="src/ui/assets/simulation_controls/autocompletebuttonhover.png",
            pressed_icon_path="src/ui/assets/simulation_controls/autocompletebuttonpress.png",
            size=(40, 40)
        )
        main_window.autocomplete_btn.setToolTip("🚀 Autocomplete (Enter)")
        main_window.autocomplete_btn.on_click = lambda: main_window.cancel_connection_if_active(main_window.run_autocomplete)

        # Add background toggle button
        main_window.background_toggle_btn = QPushButton("🌄 Off")
        main_window.background_toggle_btn.clicked.connect(lambda: main_window.cancel_connection_if_active(main_window.toggle_background))
        # Create a fixed-width font for the button
        background_button_style = default_button_style + """
            QPushButton { 
                font-family: Menlo, Consolas, Courier, monospace;
                font-size: 12px;
            }
        """
        main_window.background_toggle_btn.setStyleSheet(background_button_style)
        main_window.background_toggle_btn.setFixedWidth(150)
        
        # Create time slider
        main_window.time_slider = QSlider(Qt.Horizontal)
        main_window.time_slider.setMinimum(0)
        main_window.time_slider.setMaximum(8760)  # 8760 hours in a year
        main_window.time_slider.valueChanged.connect(lambda value: main_window.cancel_connection_if_active(main_window.time_slider_changed, value))
        # Add new connections for scrub mode detection
        main_window.time_slider.sliderPressed.connect(lambda: main_window.cancel_connection_if_active(main_window.start_scrubbing))
        main_window.time_slider.sliderReleased.connect(lambda: main_window.cancel_connection_if_active(main_window.stop_scrubbing))
        # Set the time slider to expand horizontally
        main_window.time_slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        main_window.time_slider.setStyleSheet("QSlider::groove:horizontal { background: #3D3D3D; height: 8px; border-radius: 4px; } QSlider::sub-page:horizontal { background: rgb(255, 215, 0); height: 8px; border-radius: 4px; } QSlider::handle:horizontal { background: #5D5D5D; width: 16px; margin: -4px 0; border-radius: 8px; }")
        
        time_controls.addWidget(main_window.reset_btn)
        time_controls.addWidget(main_window.play_btn)
        # time_controls.addWidget(main_window.speed_selector) // Removed speed selector as it doesnt get a lot of use, but just uncomment this line to add it back
        time_controls.addWidget(main_window.time_slider)
        time_controls.addWidget(main_window.autocomplete_btn)
        # time_controls.addWidget(main_window.background_toggle_btn) // Removed background toggle button as it doesnt get a lot of use, but just uncomment this line to add it back
        time_controls.addWidget(main_window.screenshot_btn)
        # time_controls.addWidget(zoom_label)
        time_controls.addWidget(main_window.zoom_slider)
        
        time_layout.addLayout(time_controls)
        
        time_dock.setWidget(time_widget)
        main_window.addDockWidget(Qt.BottomDockWidgetArea, time_dock)
        
        # Main canvas in the center
        main_layout.addWidget(main_window.view)
        
        # Create toolbar
        toolbar = QToolBar("Main Toolbar")
        main_window.addToolBar(toolbar)
        
        # Increase font size for toolbar - using stylesheet for better compatibility
        toolbar_style = "QToolBar { font-size: 14pt; } QToolButton { font-size: 14pt; }"
        toolbar.setStyleSheet(toolbar_style)
        
        # Create actions for model operations
        new_action = QAction("New", main_window)
        new_action.triggered.connect(lambda: main_window.cancel_connection_if_active(main_window.new_scenario))
        
        save_action = QAction("Save", main_window)
        save_action.triggered.connect(lambda: main_window.cancel_connection_if_active(main_window.save_scenario))
        
        load_action = QAction("Load", main_window)
        load_action.triggered.connect(lambda: main_window.cancel_connection_if_active(main_window.load_scenario))
        
        # Create Model menu and add actions
        model_menu = QMenu("Model", main_window)
        model_menu.addAction(new_action)
        model_menu.addAction(save_action)
        model_menu.addAction(load_action)
        
        # Use QToolButton for Model menu to make text clickable
        model_button = QToolButton()
        model_button.setText("Model")
        model_button.setMenu(model_menu)
        model_button.setPopupMode(QToolButton.InstantPopup)  # Show menu when clicking anywhere on button
        # Cancel connection mode when the button is clicked
        model_button.clicked.connect(lambda: main_window.cancel_connection_if_active())
        toolbar.addWidget(model_button)
        
        # Add separator
        toolbar.addSeparator()
        
        # Create View menu for showing/hiding panels
        view_menu = QMenu("View", main_window)
        
        # Create actions for toggling panel visibility - store references for later updates
        main_window.properties_action = QAction("Show Properties Panel", main_window)
        main_window.properties_action.triggered.connect(lambda: main_window.cancel_connection_if_active(main_window.toggle_properties_panel))
        
        main_window.analytics_action = QAction("Show Analytics (P)anel", main_window)
        main_window.analytics_action.triggered.connect(lambda: main_window.cancel_connection_if_active(main_window.toggle_analytics_panel))
        view_menu.addAction(main_window.analytics_action)

        # Use QToolButton instead of QAction for View menu to make text clickable
        view_button = QToolButton()
        view_button.setText("View")
        view_button.setMenu(view_menu)
        view_button.setPopupMode(QToolButton.InstantPopup)  # Show menu when clicking anywhere on button
        # Cancel connection mode when the button is clicked
        view_button.clicked.connect(lambda: main_window.cancel_connection_if_active())
        toolbar.addWidget(view_button)

        # Create Window menu for window size control
        window_menu = QMenu("Window", main_window)
        
        # Create actions for window size control
        maximize_action = QAction("Maximize", main_window)
        maximize_action.triggered.connect(lambda: main_window.cancel_connection_if_active(main_window.showMaximized))
        window_menu.addAction(maximize_action)
        
        restore_default_action = QAction("Restore Default", main_window)
        restore_default_action.triggered.connect(lambda: main_window.cancel_connection_if_active(lambda: main_window.resize(1600, 900)))
        window_menu.addAction(restore_default_action)
        
        # Use QToolButton for Window menu
        window_button = QToolButton()
        window_button.setText("Window")
        window_button.setMenu(window_menu)
        window_button.setPopupMode(QToolButton.InstantPopup)
        # Cancel connection mode when the button is clicked
        window_button.clicked.connect(lambda: main_window.cancel_connection_if_active())
        toolbar.addWidget(window_button)

        # Add spacer to push clock to the right side of toolbar
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        toolbar.addWidget(spacer)
        
        # Add clock display
        main_window.clock_label = QLabel()
        main_window.clock_label.setStyleSheet("QLabel { color: white; font-size: 14pt; margin-right: 15px; }")
        toolbar.addWidget(main_window.clock_label)
        
        # Set up timer to update clock every second
        main_window.clock_timer = QTimer(main_window)
        main_window.clock_timer.timeout.connect(lambda: UIInitializer.update_clock(main_window))
        main_window.clock_timer.start(1000)  # Update every second
        
        # Initialize clock immediately
        UIInitializer.update_clock(main_window)

        # Connect visibility changed signals to update menu text
        main_window.properties_dock.visibilityChanged.connect(main_window.update_properties_menu_text)
        main_window.analytics_dock.visibilityChanged.connect(main_window.update_analytics_menu_text)

    def on_view_resize(self, event):
        """Handle resize events to reposition the logo overlay and historian chart"""
        if hasattr(self, 'logo_overlay') and not self.logo_overlay.pixmap().isNull():
            # Reposition logo in bottom right when view is resized
            logo_width = self.logo_overlay.pixmap().width()
            logo_height = self.logo_overlay.pixmap().height()
            self.logo_overlay.move(self.view.width() - logo_width - 5, self.view.height() - logo_height + 5)
        
        # Reposition mode toggle button in top left corner
        if hasattr(self, 'mode_toggle_btn'):
            self.mode_toggle_btn.move(10, 10)
            
        # Reposition analytics container in top right corner
        if hasattr(self, 'analytics_container'):
            self.analytics_container.move(self.view.width() - 340, 0)
            
        # Reposition capex label in bottom left corner
        if hasattr(self, 'capex_label'):
            self.capex_label.move(10, self.view.height() - self.capex_label.height() - 65)
        
        # Reposition irr label in bottom left corner
        if hasattr(self, 'irr_label'):
            self.irr_label.move(10, self.view.height() - self.irr_label.height() - 20)
        
        # Resize historian chart if in historian view
        if not self.is_model_view and hasattr(self, 'historian_manager'):
            view_size = self.view.viewport().size()
            self.historian_manager.resize_chart_widget(view_size.width(), view_size.height())
        
        # Call original resize event if it was saved
        if hasattr(self, 'original_resize_event'):
            self.original_resize_event(event)
        else:
            # Call base QGraphicsView implementation
            QGraphicsView.resizeEvent(self.view, event)

    @staticmethod
    def update_clock(main_window):
        """Update the clock label with current time in 12-hour format"""
        current_time = QTime.currentTime()
        # Use h for hour without leading zero in 12-hour format
        # Use AP for AM/PM indicator
        hour = current_time.hour()
        # Convert to 12-hour format
        if hour == 0:
            hour_12 = 12
        elif hour > 12:
            hour_12 = hour - 12
        else:
            hour_12 = hour
            
        minute = current_time.toString("mm")
        am_pm = "AM" if hour < 12 else "PM"
        
        # Flash the colon (visible on even seconds, hidden on odd seconds)
        seconds = current_time.second()
        colon = ":" if seconds % 2 == 0 else " "
        
        # Combine parts to create the time string
        time_text = f"{hour_12}{colon}{minute} {am_pm}"
        main_window.clock_label.setText(time_text)

# Import TiledBackgroundWidget from main_window.py to avoid circular imports

# TiledBackgroundWidget was moved to a separate file (src/ui/tiled_background_widget.py) 