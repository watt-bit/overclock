from PyQt5.QtCore import QTimer, QPointF

from src.simulation.engine import SimulationEngine
from .properties_manager import ComponentPropertiesManager
from src.models.model_manager import ModelManager
from .historian_manager import HistorianManager
from .particle_system import ParticleSystem
from .component_adder import ComponentAdder
from .connection_manager import ConnectionManager
from .autocomplete_manager import AutocompleteManager
from .mode_toggle_manager import ModeToggleManager
from .simulation_controller import SimulationController
from .screenshot_manager import ScreenshotManager
from .custom_scene import CustomScene
from .ui_initializer import UIInitializer
from .key_handler import KeyHandler
from .capex_manager import CapexManager


class SimulatorInitializer:
    @staticmethod
    def initialize(simulator):
        """Initialize the PowerSystemSimulator with all necessary components and settings"""
        # Set window properties
        simulator.setWindowTitle("OVERCLOCK | Watt-Bit Research | https://watt-bit.com | research preview presented by Augur VC | https://augurvc.com")
        simulator.resize(1600, 900)
        
        # Initialize variables
        simulator.components = []
        simulator.connections = []
        simulator.creating_connection = False
        simulator.connection_source = None
        simulator.temp_connection = None
        simulator.cursor_phase = 0
        simulator.is_scrubbing = False
        simulator.scrub_timer = None
        
        # Create particle system for visual effects
        simulator.particle_system = None  # Will initialize after scene is created
        
        # Autocomplete state
        simulator.is_autocompleting = False
        simulator.autocomplete_timer = None
        simulator.autocomplete_end_time = 0
        
        # Track if the properties panel has been positioned yet
        simulator.properties_panel_positioned = False
        
        # Background mode: 0 = background1, 1 = background2, 2 = solid color
        simulator.background_mode = 2  # Set default to solid color (Background Off)
        
        # Create simulation engine
        simulator.simulation_engine = SimulationEngine(simulator)
        
        # Create properties manager
        simulator.properties_manager = ComponentPropertiesManager(simulator)
        
        # Create model manager
        simulator.model_manager = ModelManager(simulator)
        
        # Create historian manager
        simulator.historian_manager = HistorianManager(simulator)
        
        # Cursor animation
        simulator.cursor_timer = QTimer()
        simulator.cursor_timer.timeout.connect(simulator.update_cursor)
        simulator.cursor_size = 32
        
        # Create scene with custom signal
        simulator.scene = CustomScene()
        simulator.scene.parent = lambda: simulator
        simulator.scene.component_clicked.connect(simulator.properties_manager.show_component_properties)
        
        # Initialize particle system now that scene exists
        simulator.particle_system = ParticleSystem(simulator.scene)
        simulator.particle_system.main_window = simulator  # Set reference to main window
        
        # Initialize CAPEX manager
        simulator.capex_manager = CapexManager(simulator)
        
        # Initialize the component adder
        simulator.component_adder = ComponentAdder(simulator)
        
        # Set the initial background mode to solid color
        simulator.scene.set_background(simulator.background_mode)
        
        # Flag to track whether we're in model or historian view
        simulator.is_model_view = True
        
        # Store the previous zoom value when switching to historian
        simulator.previous_zoom_value = None
        
        # Initialize the UI using the new UIInitializer
        UIInitializer.initialize_ui(simulator)
        
        # Setup simulation timer
        simulator.sim_timer = QTimer()
        simulator.sim_timer.timeout.connect(lambda: simulator.step_simulation(1))
        simulator.simulation_speed = 1
        
        # Create connection manager
        simulator.connection_manager = ConnectionManager(simulator)
        
        # Create autocomplete manager
        simulator.autocomplete_manager = AutocompleteManager(simulator)
        
        # Create mode toggle manager
        simulator.mode_toggle_manager = ModeToggleManager(simulator)
        
        # Create simulation controller
        simulator.simulation_controller = SimulationController(simulator)
        
        # Create screenshot manager
        simulator.screenshot_manager = ScreenshotManager(simulator)
        
        # Initialize welcome_text variable but don't add it yet
        simulator.welcome_text = None
         
        # Center the window on the screen
        simulator.center_on_screen()
        
        # Add method to center the view on origin (0,0)
        simulator.center_view_on_origin = lambda: simulator.view.centerOn(QPointF(0, 0))
        
        # Create KeyHandler instance
        simulator.key_handler = KeyHandler(simulator) 