# Power System Simulator Architecture

This document provides an overview of the high-level architecture of the Power System Simulator application, including its core modules, responsibilities, and data flow. The goal is to help developers and maintainers understand how the application is structured and how various parts interact.

## Overview

The simulator is composed of several modules under the `src` directory, each handling specific layers of functionality:

1. **Main Application Entrypoint**  
   - **File:** `src/main.py`
   - **Responsibility:** Starts the Qt application, creates the main window (`PowerSystemSimulator`), and runs the event loop.

2. **Main Window & UI**  
   - **File:** `src/ui/main_window.py`
   - **Responsibility:** Defines the primary GUI class `PowerSystemSimulator`. Manages UI initialization, user interaction (e.g., button clicks, adding components, scrubbing the timeline), and orchestrates simulation updates.
   - **Key Elements:**
     - Methods for creating and placing components on the scene.
     - Methods to start/cancel connections, sever connections, toggle simulation, and handle advanced UI features like scrubbing time, zooming, or toggling backgrounds.

3. **Analytics Panel**  
   - **File:** `src/ui/analytics.py`
   - **Responsibility:** Provides a `QWidget` (`AnalyticsPanel`) containing:
     - Time-series plots using Matplotlib.
     - Progress bars and labels to display real-time power metrics (e.g., generation, load, battery power, grid import/export).
     - Methods for updating plots and numeric data based on the simulation engine's output.

4. **Simulation Engine**  
   - **File:** `src/simulation/engine.py`
   - **Responsibility:** Implements `SimulationEngine` to perform step-by-step calculations of power flows.  
   - **Core functionality** includes:
     - Maintaining simulation state (time steps, flags like `simulation_running`, total energy imported/exported).
     - Processing loads, generators, batteries, grid imports, and exports in the correct priority order.
     - Handling bus connectivity (via `validate_bus_states` in the main window).
     - Providing methods to step and update simulation results, which then get sent to the `AnalyticsPanel`.

5. **Connection Management**  
   - **File:** `src/ui/connection_manager.py`
   - **Responsibility:** Orchestrates the creation of connections (wires/links) between different components in the scene.  
   - **Key points**:
     - Listens for user clicks on components to form or sever connections.
     - Shows temporary connection lines as the user selects source and target components.
     - Enables "autoconnect" features that automatically create valid networks.

6. **Properties Panel Management**  
   - **File:** `src/ui/properties_manager.py`
   - **Responsibility:** Provides a form-like UI for editing properties of a selected component (e.g., generator capacity, load demand, battery parameters).
   - **Highlights**:
     - Dynamically creates Qt widgets (sliders, text fields, combo boxes) appropriate for the selected component type.
     - Includes features to load custom load profiles, generate random/sine wave profiles, or manage data-center load patterns.
     - Allows deletion of the selected component and refreshes the simulation state after changes.

7. **Model Management (Saving/Loading)**  
   - **File:** `src/models/model_manager.py`
   - **Responsibility:** Contains logic for serializing and deserializing the simulator's state (components and connections) to/from JSON files.
   - **Behavior**:
     - `save_scenario()` organizes components (and decorative items) into a JSON structure, including references for connections.
     - `load_scenario()` reconstructs components and connections in the scene from JSON data.

8. **Component Classes**
   - **File Paths:** `src/components/*`
   - **Responsibility:** Each file defines a specific component or a group of related components.  
   - **Examples**:
     - **GeneratorComponent** for power generation.  
     - **LoadComponent** for consuming power.  
     - **BusComponent** representing a bus with optional states for toggling loads.  
     - **BatteryComponent** for energy storage.  
     - **GridImportComponent** / **GridExportComponent** for grid tie-in.  
     - **Various decorative components** (e.g., `TreeComponent`, `BushComponent`, `PondComponent`) that appear on the scene but do not impact the simulation logic.

9. **Utilities**
   - **File Paths:** `src/utils/*`
   - **Responsibility:** Contains utility functions and helper classes that support the main application functionality.

## Directory Structure

```
src/
├── __init__.py
├── main.py                # Application entry point
├── components/            # Power system component classes
├── models/                # Model saving and loading functionality
├── simulation/            # Simulation engine and calculation logic
├── ui/                    # User interface modules
└── utils/                 # Utility functions and helper classes
```

## Data Flow and Key Interactions

1. **Main Event Loop**  
   The file `src/main.py` launches the Qt event loop. User interactions (mouse clicks, button presses, etc.) are fed to the `PowerSystemSimulator` in `main_window.py`.

2. **Scene and Components**  
   - `PowerSystemSimulator` manages a `QGraphicsScene` where all components (generators, loads, buses, etc.) are placed.  
   - The user can click to add new components or connect them with wires.

3. **Simulation Updates**  
   - When the simulation advances (`step_simulation()`), `SimulationEngine` collects data from each component, calculates power flows, battery charges, and grid imports/exports, and then updates the scene and the `AnalyticsPanel`.

4. **Analytics & Visualization**  
   - The `AnalyticsPanel` (in `analytics.py`) reads aggregated power metrics and updates progress bars, time-series charts, and stats (e.g., Net Grid Energy, Surplus/Deficit, Battery Charge).

5. **Properties Editing**  
   - Selecting a component (e.g., generator or load) opens the `PropertiesManager` UI. Users can change parameters (capacity, demand, custom profiles, etc.), triggering a re-run of the simulation logic.

6. **Saving/Loading**  
   - At any time, the user may save the scenario using `ModelManager.save_scenario()`. The entire scene state (components and connections) is serialized to JSON.  
   - Loading a scenario (`ModelManager.load_scenario()`) rebuilds the scene, recreating components and re-establishing connections exactly as saved.

## Design Considerations

1. **Separation of Concerns**  
   - The code is organized so that each piece (UI, simulation logic, storage, property editing) resides in its own module or class.  
   - This allows for easier maintenance and testing.

2. **Extendability**  
   - New component types or new UI panels (e.g., a new analytics display) can be added with minimal changes to existing code, following the patterns set in `src/components/*` and in the managers.

3. **DRY Principle**  
   - Shared functionality such as archiving component properties or iterating the scene is minimized to single points (e.g., `ModelManager` for load/save, `SimulationEngine` for stepping logic).

4. **Qt Integration**  
   - The application uses PyQt5 for rendering and user interaction. The `QGraphicsScene`, `QMainWindow`, and `QWidget` classes are central to the UI.

## Custom Scene and Graphics Framework

The application implements a custom `CustomScene` class that extends `QGraphicsScene` to handle component interactions and background rendering. This provides:

1. **Component Interaction** - Emitting signals when components are clicked
2. **Custom Background Support** - Allowing background images to be set and rendered
3. **Graphics Layer Management** - Ensuring proper z-ordering of scene elements 

## Conclusion

This architecture is designed to keep the simulation logic transparent, user interactions structured, and code maintainable. The core loop remains in `main.py`, delegating nearly all functionality to specialized classes scattered across UI managers (`main_window`, `connection_manager`, `properties_manager`), the simulation engine (`engine.py`), component definitions, and serialization logic (`model_manager`).

By adhering to these boundaries and responsibilities, developers can more easily update or extend individual pieces of functionality without risking breakage in other parts of the system. 