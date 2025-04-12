from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QPushButton, QSlider, QFileDialog, 
                            QGraphicsView, QGraphicsScene, QDockWidget, 
                            QFormLayout, QLineEdit, QComboBox, QToolBar, 
                            QAction, QMessageBox, QSplitter, QGraphicsLineItem,
                            QApplication, QSpacerItem, QMenu, QShortcut, QFrame,
                            QToolButton, QSizePolicy, QGraphicsItem)
from PyQt5.QtCore import Qt, QPointF, QRectF, QTimer, pyqtSignal, QObject, QSize
from PyQt5.QtGui import QPainter, QPen, QCursor, QPixmap, QColor, QDoubleValidator, QIntValidator, QBrush, QKeySequence, QIcon, QRadialGradient

# Import or reference modules and classes needed from main_window
from .analytics import AnalyticsPanel

class UIInitializer:
    @staticmethod
    def initialize_ui(main_window):
        """Initialize the UI components for the PowerSystemSimulator"""
        # Main layout
        main_widget = QWidget()
        main_window.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        
        # Set the corners to give priority to left and right dock areas
        main_window.setCorner(Qt.TopLeftCorner, Qt.LeftDockWidgetArea)
        main_window.setCorner(Qt.TopRightCorner, Qt.RightDockWidgetArea)
        main_window.setCorner(Qt.BottomLeftCorner, Qt.BottomDockWidgetArea)
        main_window.setCorner(Qt.BottomRightCorner, Qt.BottomDockWidgetArea)
        
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
        main_window.setStyleSheet(dock_title_style)
        
        # Create canvas for drag and drop
        main_window.view = QGraphicsView(main_window.scene)
        main_window.view.setDragMode(QGraphicsView.RubberBandDrag)
        main_window.view.setRenderHint(QPainter.Antialiasing)
        main_window.view.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        
        # Set initial scaling for view
        main_window.current_zoom = 0.8
        
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
        logo_pixmap = QPixmap("src/ui/assets/overclocklogo.png")
        if not logo_pixmap.isNull():
            # Calculate 10% of the original size while maintaining aspect ratio
            scaled_width = int(logo_pixmap.width() * 0.1)
            scaled_height = int(logo_pixmap.height() * 0.1)
            scaled_logo = logo_pixmap.scaled(scaled_width, scaled_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            main_window.logo_overlay.setPixmap(scaled_logo)
            main_window.logo_overlay.setAttribute(Qt.WA_TransparentForMouseEvents)  # Make it click-through
            
            # Position in bottom right corner with padding
            main_window.logo_overlay.move(main_window.view.width() - scaled_width - 10, main_window.view.height() - scaled_height - 10)
            
            # Connect to view's resize event to maintain position
            main_window.view.resizeEvent = main_window.on_view_resize
            
            # Make the logo visible
            main_window.logo_overlay.show()
        
        # Create Mode/Historian toggle button in top-left corner
        main_window.mode_toggle_btn = QPushButton("🧩 Model (TAB)", main_window.view)
        main_window.mode_toggle_btn.setStyleSheet("""
            QPushButton { 
                background-color: #3D3D3D; 
                color: white; 
                border: 1px solid #555555; 
                border-radius: 3px; 
                padding: 5px; 
                width: 125px; 
                font-weight: bold; 
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
        """)
        main_window.mode_toggle_btn.clicked.connect(main_window.toggle_mode_button)
        # Position in top left corner with padding
        main_window.mode_toggle_btn.move(10, 10)
        # Make the button visible
        main_window.mode_toggle_btn.show()
        
        # Create a custom class for the analytics toggle button
        class AnalyticsToggleButton(QLabel):
            def __init__(self, parent=None):
                super().__init__(parent)
                self.normal_pixmap = QPixmap("src/ui/assets/analyticsbutton.png")
                self.hover_pixmap = QPixmap("src/ui/assets/analyticsbuttonhover.png")
                self.clicked_pixmap = QPixmap("src/ui/assets/analyticsbuttonclick.png")
                
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
        
        # Create Analytics toggle button in top-right corner
        main_window.analytics_toggle_btn = AnalyticsToggleButton(main_window.view)
        # Set the click handler
        main_window.analytics_toggle_btn.on_click = main_window.toggle_analytics_panel
        # Position in top right corner with padding
        main_window.analytics_toggle_btn.move(main_window.view.width() - 85, 0)
        # Make the button visible
        main_window.analytics_toggle_btn.show()
        
        # Component palette
        main_window.component_dock = QDockWidget("Components", main_window)
        main_window.component_dock.setObjectName("component_dock")
        # Remove title bar and prevent undocking/closing
        main_window.component_dock.setTitleBarWidget(QWidget())
        main_window.component_dock.setFeatures(QDockWidget.NoDockWidgetFeatures)
        # Set fixed width to 200px
        main_window.component_dock.setFixedWidth(200)
        # Ensure no borders are visible
        main_window.component_dock.setStyleSheet("QDockWidget { border: none; }")
        
        # Use TiledBackgroundWidget from main_window
        # We need to use the class from main_window instead of creating it here
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

        # Add WBR logo overlay
        main_window.wbr_logo_label = QLabel(top_image_label)  # Set parent to top_image_label
        main_window.wbr_logo_label.setStyleSheet("border: none; background: transparent;")
        wbr_logo_pixmap = QPixmap("src/ui/assets/wbrlogo.png")
        if not wbr_logo_pixmap.isNull():
            # Scale to 125px width while preserving aspect ratio
            aspect_ratio = wbr_logo_pixmap.height() / wbr_logo_pixmap.width()
            scaled_height = int(125 * aspect_ratio)
            scaled_logo = wbr_logo_pixmap.scaled(125, scaled_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            main_window.wbr_logo_label.setPixmap(scaled_logo)
            # Will position after top_image_label is sized

        # Define a common button style with opaque background
        opaque_button_style = """
            QPushButton { 
                background-color: #3D3D3D; 
                color: white; 
                border: 1px solid #555555; 
                border-radius: 3px; 
                padding: 5px; 
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
        
        generator_btn = QPushButton("🔥 (G)as Generator")
        generator_btn.setStyleSheet(opaque_button_style)
        generator_btn.clicked.connect(lambda: main_window.add_component("generator"))
        
        battery_btn = QPushButton("🔋 Battery (S)torage")
        battery_btn.setStyleSheet(opaque_button_style)
        battery_btn.clicked.connect(lambda: main_window.add_component("battery"))
                
        bus_btn = QPushButton("⚡ Electrical (B)us")
        bus_btn.setStyleSheet(opaque_button_style)
        bus_btn.clicked.connect(lambda: main_window.add_component("bus"))

        load_btn = QPushButton("💡 Electrical (L)oad")
        load_btn.setStyleSheet(opaque_button_style)
        load_btn.clicked.connect(lambda: main_window.add_component("load"))
        
        cloud_workload_btn = QPushButton("🌐 Cloud (W)orkload")
        cloud_workload_btn.setStyleSheet(opaque_button_style)
        cloud_workload_btn.clicked.connect(lambda: main_window.add_component("cloud_workload"))

        # Create a popup menu for renewables
        renewables_menu = QMenu(main_window)
        
        # Add actions for each renewable type
        solar_panel_action = renewables_menu.addAction("Add Solar Array")
        solar_panel_action.triggered.connect(lambda: main_window.add_component("solar_panel"))
        
        wind_turbine_action = renewables_menu.addAction("Add Wind Turbine")
        wind_turbine_action.triggered.connect(lambda: main_window.add_component("wind_turbine"))
        
        # Create the Add Renewables button with dropdown menu
        main_window.renewables_btn = QPushButton("🌱 Renewables")
        main_window.renewables_btn.setStyleSheet(opaque_button_style)
        main_window.renewables_btn.clicked.connect(lambda: renewables_menu.exec_(main_window.renewables_btn.mapToGlobal(main_window.renewables_btn.rect().bottomLeft())))
        
        # Add a third horizontal line separator
        separator3 = QFrame()
        separator3.setFrameShape(QFrame.HLine)
        separator3.setFrameShadow(QFrame.Sunken)
        separator3.setLineWidth(1)

        grid_import_btn = QPushButton("⬇ Grid (I)mport Pathway")
        grid_import_btn.setStyleSheet(opaque_button_style)
        grid_import_btn.clicked.connect(lambda: main_window.add_component("grid_import"))
        
        grid_export_btn = QPushButton("⬆ Grid (E)xport Pathway")
        grid_export_btn.setStyleSheet(opaque_button_style)
        grid_export_btn.clicked.connect(lambda: main_window.add_component("grid_export"))
        
        # Add a horizontal line separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setLineWidth(1)
        
        main_window.connection_btn = QPushButton("Create (C)onnection")
        main_window.connection_btn.setStyleSheet(opaque_button_style)
        main_window.connection_btn.clicked.connect(main_window.start_connection)
        
        autoconnect_btn = QPushButton("(A)utoconnect All")
        autoconnect_btn.setStyleSheet(opaque_button_style)
        autoconnect_btn.clicked.connect(main_window.autoconnect_all_components)
        
        main_window.sever_connection_btn = QPushButton("Sever Connections")
        main_window.sever_connection_btn.setStyleSheet(opaque_button_style)
        main_window.sever_connection_btn.clicked.connect(main_window.start_sever_connection)

        # Add a second horizontal line separator
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.HLine)
        separator2.setFrameShadow(QFrame.Sunken)
        separator2.setLineWidth(1)

        # Create a popup menu for props
        props_menu = QMenu(main_window)
        
        # Add actions for each prop type
        tree_action = props_menu.addAction("Add Tree")
        tree_action.triggered.connect(lambda: main_window.add_component("tree"))
        
        bush_action = props_menu.addAction("Add Bush")
        bush_action.triggered.connect(lambda: main_window.add_component("bush"))
        
        pond_action = props_menu.addAction("Add Pond")
        pond_action.triggered.connect(lambda: main_window.add_component("pond"))
        
        house1_action = props_menu.addAction("Add House")
        house1_action.triggered.connect(lambda: main_window.add_component("house1"))
        
        house2_action = props_menu.addAction("Add Greenhouse")
        house2_action.triggered.connect(lambda: main_window.add_component("house2"))
        
        factory_action = props_menu.addAction("Add Factory")
        factory_action.triggered.connect(lambda: main_window.add_component("factory"))
        
        trad_data_center_action = props_menu.addAction("Add Data Center")
        trad_data_center_action.triggered.connect(lambda: main_window.add_component("traditional_data_center"))
        
        distribution_pole_action = props_menu.addAction("Add Distribution Pole")
        distribution_pole_action.triggered.connect(lambda: main_window.add_component("distribution_pole"))
        
        # Create the Add Props button with dropdown menu
        main_window.props_btn = QPushButton("🏡 Add Props")
        main_window.props_btn.setStyleSheet(opaque_button_style)
        main_window.props_btn.clicked.connect(lambda: props_menu.exec_(main_window.props_btn.mapToGlobal(main_window.props_btn.rect().bottomLeft())))
        
        component_layout.addWidget(generator_btn)
        component_layout.addWidget(battery_btn)
        component_layout.addWidget(bus_btn)
        component_layout.addWidget(load_btn)
        component_layout.addWidget(cloud_workload_btn)
        component_layout.addWidget(main_window.renewables_btn)
        component_layout.addWidget(separator3)
        component_layout.addWidget(grid_import_btn)
        component_layout.addWidget(grid_export_btn)
        component_layout.addWidget(separator)
        component_layout.addWidget(main_window.connection_btn)
        component_layout.addWidget(autoconnect_btn)
        component_layout.addWidget(main_window.sever_connection_btn)
        component_layout.addWidget(separator2)
        component_layout.addWidget(main_window.props_btn)
        component_layout.addStretch()
        
        # Now that we have a button, set the top image size to match component width
        if not top_pixmap.isNull():
            top_aspect_ratio = top_pixmap.height() / top_pixmap.width()
            top_scaled_height = int(generator_btn.sizeHint().width() + 75 * top_aspect_ratio)
            scaled_top_pixmap = top_pixmap.scaled(generator_btn.sizeHint().width() + 75, top_scaled_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            top_image_label.setPixmap(scaled_top_pixmap)
            
            # Position the WBR logo in the bottom left corner of top image
            if hasattr(main_window, 'wbr_logo_label') and not main_window.wbr_logo_label.pixmap().isNull():
                main_window.wbr_logo_label.move(0, top_scaled_height - main_window.wbr_logo_label.pixmap().height())
                main_window.wbr_logo_label.raise_()  # Ensure it renders on top
        
        # Store references to all component and connection buttons for later enabling/disabling
        main_window.component_buttons = [
            generator_btn, 
            grid_import_btn, 
            grid_export_btn, 
            bus_btn, 
            load_btn, 
            battery_btn,
            cloud_workload_btn,
            main_window.renewables_btn,
            main_window.props_btn,
            main_window.connection_btn,
            autoconnect_btn,
            main_window.sever_connection_btn
        ]
        
        main_window.component_dock.setWidget(component_widget)
        main_window.addDockWidget(Qt.LeftDockWidgetArea, main_window.component_dock)
        
        # Properties panel
        main_window.properties_dock = QDockWidget("Properties", main_window)
        main_window.properties_dock.setObjectName("properties_dock")
        main_window.properties_dock.setWidget(main_window.properties_manager.properties_widget)
        # Allow the dock widget to resize when its contents change
        main_window.properties_dock.setFeatures(QDockWidget.DockWidgetFloatable | 
                                        QDockWidget.DockWidgetMovable | 
                                        QDockWidget.DockWidgetClosable)
        # Prevent the properties panel from being docked
        main_window.properties_dock.setAllowedAreas(Qt.NoDockWidgetArea)
        # Ensure the dock resizes to the minimum size of its contents
        main_window.properties_dock.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        main_window.addDockWidget(Qt.RightDockWidgetArea, main_window.properties_dock)
        # Make properties panel floating and hidden by default
        main_window.properties_dock.setFloating(True)
        main_window.properties_dock.setVisible(False)
        
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
        time_dock.setFixedHeight(70)
        # Ensure no borders are visible
        time_dock.setStyleSheet("QDockWidget { border: none; }")
        
        time_widget = TiledBackgroundWidget()
        time_widget.set_background("src/ui/assets/backgroundstars.png")
        time_layout = QVBoxLayout(time_widget)
        
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
        
        main_window.play_btn = QPushButton("Run (Space)")
        main_window.play_btn.clicked.connect(main_window.toggle_simulation)
        main_window.play_btn.setStyleSheet(common_button_style + """
            QPushButton { 
                background-color: #0D47A1; 
                color: white; 
                font-weight: bold; 
                font-size: 16px; 
            }
            QPushButton:hover { 
                background-color: #1565C0; 
            }
            QPushButton:pressed { 
                background-color: #0A367B; 
            }
        """)
        main_window.play_btn.setFixedWidth(140)
        
        main_window.reset_btn = QPushButton("🔴 (R)eset")
        main_window.reset_btn.clicked.connect(main_window.reset_simulation)
        main_window.reset_btn.setStyleSheet(common_button_style + """
            QPushButton { 
                background-color: #B71C1C; 
                color: white; 
                font-weight: bold; 
                font-size: 14px; 
            }
            QPushButton:hover { 
                background-color: #C62828; 
            }
            QPushButton:pressed { 
                background-color: #9B1818; 
            }
        """)
        main_window.reset_btn.setFixedWidth(90)

        # Add speed control
        speed_label = QLabel("⏩ Speed:")
        main_window.speed_selector = QPushButton("▶▷▷")
        main_window.speed_selector.clicked.connect(main_window.cycle_simulation_speed)
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
        main_window.zoom_slider = QSlider(Qt.Horizontal)
        main_window.zoom_slider.setMinimum(40)  # 0.4x zoom (changed from 20/0.2x)
        main_window.zoom_slider.setMaximum(100)  # 1.0x zoom
        main_window.zoom_slider.setValue(80)    # Default to 0.8x
        main_window.zoom_slider.setFixedWidth(150)
        main_window.zoom_slider.valueChanged.connect(main_window.zoom_changed)
        main_window.zoom_slider.setStyleSheet("QSlider::groove:horizontal { background: #3D3D3D; height: 8px; border-radius: 4px; } QSlider::handle:horizontal { background: #5D5D5D; width: 16px; margin: -4px 0; border-radius: 8px; }")
        
        # Add screenshot button
        main_window.screenshot_btn = QPushButton("📷 Screenshot")
        main_window.screenshot_btn.clicked.connect(main_window.take_screenshot)
        main_window.screenshot_btn.setStyleSheet(default_button_style)
        main_window.screenshot_btn.setFixedWidth(150)

        # Add Autocomplete button
        main_window.autocomplete_btn = QPushButton("🚀 Autocomplete (Enter)")
        main_window.autocomplete_btn.clicked.connect(main_window.run_autocomplete)
        main_window.autocomplete_btn.setStyleSheet(common_button_style + """
            QPushButton { 
                background-color: #1B5E20; 
                color: white; 
                font-weight: bold; 
                font-size: 16px; 
            }
            QPushButton:hover { 
                background-color: #2E7D32; 
            }
            QPushButton:pressed { 
                background-color: #154919; 
            }
        """)
        main_window.autocomplete_btn.setFixedWidth(250)

        # Add background toggle button
        main_window.background_toggle_btn = QPushButton("🌄 Background Off")
        main_window.background_toggle_btn.clicked.connect(main_window.toggle_background)
        main_window.background_toggle_btn.setStyleSheet(default_button_style)
        main_window.background_toggle_btn.setFixedWidth(150)
        
        # Create time slider
        main_window.time_slider = QSlider(Qt.Horizontal)
        main_window.time_slider.setMinimum(0)
        main_window.time_slider.setMaximum(8760)  # 8760 hours in a year
        main_window.time_slider.valueChanged.connect(main_window.time_slider_changed)
        # Add new connections for scrub mode detection
        main_window.time_slider.sliderPressed.connect(main_window.start_scrubbing)
        main_window.time_slider.sliderReleased.connect(main_window.stop_scrubbing)
        # Set the time slider to expand horizontally
        main_window.time_slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        main_window.time_slider.setStyleSheet("QSlider::groove:horizontal { background: #3D3D3D; height: 8px; border-radius: 4px; } QSlider::sub-page:horizontal { background: rgb(255, 215, 0); height: 8px; border-radius: 4px; } QSlider::handle:horizontal { background: #5D5D5D; width: 16px; margin: -4px 0; border-radius: 8px; }")
        
        # Add logo on the left side instead of a spacer
        sim_logo_label = QLabel()
        sim_logo_pixmap = QPixmap("src/ui/assets/augurvibelogosmall.png")
        if not sim_logo_pixmap.isNull():
            # Set fixed width to 175px (same as the left spacer it's replacing)
            sim_logo_label.setFixedWidth(175)
            # Calculate the correct height based on aspect ratio
            aspect_ratio = sim_logo_pixmap.height() / sim_logo_pixmap.width()
            scaled_width = 175
            scaled_height = int(scaled_width * aspect_ratio)
            # Scale the logo while maintaining aspect ratio
            scaled_logo = sim_logo_pixmap.scaled(scaled_width, scaled_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            sim_logo_label.setPixmap(scaled_logo)
            # Center the logo vertically in the label
            sim_logo_label.setAlignment(Qt.AlignCenter)
        
        time_controls.addWidget(sim_logo_label)
        time_controls.addWidget(main_window.reset_btn)
        time_controls.addWidget(main_window.play_btn)
        time_controls.addWidget(main_window.speed_selector)
        time_controls.addWidget(main_window.time_slider)
        time_controls.addWidget(main_window.autocomplete_btn)
        time_controls.addWidget(main_window.background_toggle_btn)
        time_controls.addWidget(main_window.screenshot_btn)
        time_controls.addWidget(zoom_label)
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
        new_action.triggered.connect(main_window.new_scenario)
        
        save_action = QAction("Save", main_window)
        save_action.triggered.connect(main_window.save_scenario)
        
        load_action = QAction("Load", main_window)
        load_action.triggered.connect(main_window.load_scenario)
        
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
        toolbar.addWidget(model_button)
        
        # Add separator
        toolbar.addSeparator()
        
        # Create View menu for showing/hiding panels
        view_menu = QMenu("View", main_window)
        
        # Create actions for toggling panel visibility - store references for later updates
        main_window.properties_action = QAction("Show Properties Panel", main_window)
        main_window.properties_action.triggered.connect(main_window.toggle_properties_panel)

        main_window.analytics_action = QAction("Show Analytics Panel", main_window)
        main_window.analytics_action.triggered.connect(main_window.toggle_analytics_panel)
        view_menu.addAction(main_window.analytics_action)

        # Use QToolButton instead of QAction for View menu to make text clickable
        view_button = QToolButton()
        view_button.setText("View")
        view_button.setMenu(view_menu)
        view_button.setPopupMode(QToolButton.InstantPopup)  # Show menu when clicking anywhere on button
        toolbar.addWidget(view_button)

        # Connect visibility changed signals to update menu text
        main_window.properties_dock.visibilityChanged.connect(main_window.update_properties_menu_text)
        main_window.analytics_dock.visibilityChanged.connect(main_window.update_analytics_menu_text)
        
        # Create a keyboard shortcut for Tab to switch between views
        main_window.tab_shortcut = QShortcut(QKeySequence(Qt.Key_Tab), main_window)
        main_window.tab_shortcut.activated.connect(main_window.toggle_mode_button)

# Import TiledBackgroundWidget from main_window.py to avoid circular imports
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