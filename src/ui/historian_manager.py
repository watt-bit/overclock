from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGraphicsScene, QHBoxLayout, QPushButton, QLabel, QScrollArea, QFrame, QSpacerItem, QSizePolicy
from PyQt5.QtGui import QColor, QBrush
from PyQt5.QtCore import Qt
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.patheffects as path_effects
import matplotlib.ticker as ticker
import numpy as np

class HistorianManager:
    """
    Manager for the Historian view content.
    Handles creation and management of the historian scene.
    """
    
    def __init__(self, parent):
        """
        Initialize the historian manager
        
        Args:
            parent: Reference to the main window
        """
        self.parent = parent
        self.historian_scene = None
        self.lines = {}  # Dictionary to store line objects by data key
        self.line_visibility = {}  # Track visibility state of each line
        self.toggle_buttons = {}  # Dictionary to store toggle buttons by data key
        self.colors = {  # Default colors for known data types - dark-mode friendly colors
            'total_generation': '#66BB6A',  # Soft green
            'total_load': '#FF7043',  # Soft orange
            'grid_import': '#AB47BC',  # Soft purple
            'grid_export': '#FFCA28',  # Soft amber
            'cumulative_revenue': '#4FC3F7',  # Bright sky blue for revenue
            'cumulative_cost': '#D32F2F',   # Soft red for cost
            'battery_charge': '#42A5F5',  # Bright blue for battery charge
            'system_instability': '#F06292',  # Pink for system instability
            'satisfied_load': '#8BC34A'   # Light green for satisfied load
        }
        
        # Define which series use secondary y-axis
        self.secondary_axis_series = ['cumulative_revenue', 'cumulative_cost']
        
        # Track buttons to maintain ordering
        self.primary_buttons = []
        self.secondary_buttons = []
        
        self.initialize_historian_scene()
        
        # Initialize default data series buttons
        self.initialize_default_data_series()
    
    def initialize_historian_scene(self):
        """
        Create the historian scene with a dark grey background
        """
        self.historian_scene = QGraphicsScene()
        
        # Set dark navy-blue background
        background_color = QColor("#0A0E22")
        self.historian_scene.setBackgroundBrush(QBrush(background_color))
        
        # Create a widget to hold the chart and controls
        self.main_widget = QWidget()
        self.main_layout = QHBoxLayout(self.main_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Create left panel for toggle buttons
        self.controls_widget = QWidget()
        self.controls_widget.setStyleSheet("background-color: #0A0E22;")
        self.controls_layout = QVBoxLayout(self.controls_widget)
        self.controls_layout.setAlignment(Qt.AlignTop)
        
        # Add a label for the controls section
        controls_label = QLabel("\n\n\nData Series")
        controls_label.setStyleSheet("color: #E1E6F9; font-weight: bold;")
        self.controls_layout.addWidget(controls_label)
        
        # Create a scroll area for the buttons (in case there are many)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setMinimumWidth(175)  # Set a minimum width
        self.scroll_area.setStyleSheet("background-color: #0A0E22; border: none;")
        
        # Create a widget to hold the buttons
        self.buttons_widget = QWidget()
        self.buttons_widget.setStyleSheet("background-color: #0A0E22;")
        self.buttons_layout = QVBoxLayout(self.buttons_widget)
        self.buttons_layout.setAlignment(Qt.AlignTop)
        self.buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_area.setWidget(self.buttons_widget)
        
        # Add the scroll area to the controls layout
        self.controls_layout.addWidget(self.scroll_area)
        
        # Add a 100px transparent vertical spacer
        spacer = QSpacerItem(20, 125, QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.controls_layout.addItem(spacer)
        
        # Create a widget to hold the chart
        self.chart_widget = QWidget()
        self.chart_widget.setStyleSheet("background-color: #0A0E22;")
        self.chart_layout = QVBoxLayout(self.chart_widget)
        self.chart_layout.setContentsMargins(1, 1, 1, 1)
        
        # Add controls and chart widgets to the main layout
        self.main_layout.addWidget(self.controls_widget)
        self.main_layout.addWidget(self.chart_widget)
        self.main_layout.setStretch(0, 0)  # Controls don't stretch
        self.main_layout.setStretch(1, 1)  # Chart stretches to fill space
        
        # Create matplotlib figure for the generation chart
        self.figure = plt.figure(figsize=(12, 6))
        self.figure.patch.set_facecolor('#0A0E22')  # Dark navy-blue background
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor('#11182F')  # Low-glow twilight tone for plot area
        
        # Create secondary y-axis
        self.ax2 = self.ax.twinx()
        self.ax2.set_facecolor('#11182F')  # Low-glow twilight tone for plot area
        self.ax2.tick_params(colors='#EC407A')  # Soft pink ticks to match cumulative_revenue color
        
        # Adjust subplot parameters to give specified padding
        self.figure.subplots_adjust(left=0.05, right=0.95, bottom=0.09, top=0.96)
        
        # Create canvas for the figure
        self.canvas = FigureCanvas(self.figure)
        self.chart_layout.addWidget(self.canvas)
        
        # Set up the plot - primary axis
        self.ax.set_xlabel('Time Step (hour)', color='#B5BEDF')
        self.ax.set_ylabel('Power (kW)', color='#B5BEDF')
        self.ax.tick_params(colors='#B5BEDF')  # Soft powdery blue-lavender for tick labels
        self.ax.grid(True, color='#3B4766', linestyle='-')  # Major gridlines
        self.ax.grid(True, which='minor', color='#2A334F', linestyle='--', alpha=0.5)  # Minor gridlines
        
        # Set spines (borders) color
        for spine in self.ax.spines.values():
            spine.set_color('#29304D')
        
        # Set up the plot - secondary axis
        self.ax2.set_ylabel('Amount ($)', color='#B5BEDF')
        self.ax2.tick_params(axis='y', colors='#B5BEDF')
        
        # Set spines (borders) color for secondary axis
        for spine in self.ax2.spines.values():
            spine.set_color('#29304D')
        
        # Set fixed horizontal scale for all 8760 hours
        self.ax.set_xlim(0, 8760)
        self.ax.set_ylim(0, 1000)  # Initial y scale, will auto-adjust
        self.ax2.set_ylim(0, 1000)  # Initial y scale, will auto-adjust
        
        # Remove scientific notation from top of secondary axis
        # This must be done before setting a custom formatter
        self.ax2.ticklabel_format(useOffset=False)
        
        # Initialize the secondary axis formatting with default values
        self.update_secondary_axis_formatting(1000)
        
        # Add the main widget to the scene
        self.chart_proxy = self.historian_scene.addWidget(self.main_widget)
        
        # Initially draw the empty chart
        self.canvas.draw()
    
    def get_color_for_data(self, data_key):
        """
        Get a color for a data series. Uses predefined colors if available,
        otherwise generates a random color suitable for dark backgrounds.
        
        Args:
            data_key: Key name for the data series
            
        Returns:
            Color string in hex format
        """
        if data_key in self.colors:
            return self.colors[data_key]
        
        # Generate a new color for unknown keys
        # Use component type prefix to ensure different component types get different color families
        component_prefix = data_key.split('_')[0] if '_' in data_key else data_key
        
        # Use a consistent hash seed based on component type
        if component_prefix == "Generator":
            base_hue = 0.1  # Orange-red family
        elif component_prefix == "Solar":
            base_hue = 0.3  # Green family
        elif component_prefix == "Wind":
            base_hue = 0.6  # Blue family
        elif component_prefix == "Load":
            base_hue = 0.9  # Purple family
        elif component_prefix == "Rev":
            base_hue = 0.45  # Teal/cyan family for revenue
        elif component_prefix == "Cost":
            base_hue = 0.0  # Red family for cost
        else:
            base_hue = 0.5  # Default cyan
        
        # Use the unique ID part for small variations within the color family
        # Extract the unique ID part from the data_key
        if '_' in data_key:
            unique_part = data_key.split('_')[-1]
            # Convert unique part to a number between 0 and 1
            unique_value = sum(ord(c) for c in unique_part) % 100 / 100.0
        else:
            unique_value = hash(data_key) % 100 / 100.0
            
        # Apply golden ratio for good distribution but keep within color family
        golden_ratio_conjugate = 0.618033988749895
        h = (base_hue + unique_value * 0.2) % 1.0  # Stay within ±0.1 of base hue
        
        # For dark backgrounds we want:
        # - High enough saturation to be distinct (0.6-0.8)
        # - High enough value/brightness to be visible (0.7-0.9)
        s = 0.7  # Fixed saturation - more vivid but not too harsh
        v = 0.85  # Fixed brightness - visible on dark but not eye-straining
        
        # Convert HSV to RGB
        # This is a simplified implementation of hsv_to_rgb
        h_i = int(h * 6)
        f = h * 6 - h_i
        p = v * (1 - s)
        q = v * (1 - f * s)
        t = v * (1 - (1 - f) * s)
        
        if h_i == 0:
            r, g, b = v, t, p
        elif h_i == 1:
            r, g, b = q, v, p
        elif h_i == 2:
            r, g, b = p, v, t
        elif h_i == 3:
            r, g, b = p, q, v
        elif h_i == 4:
            r, g, b = t, p, v
        else:
            r, g, b = v, p, q
        
        # Convert to hex
        hex_color = "#{:02x}{:02x}{:02x}".format(
            int(r*255), int(g*255), int(b*255)
        )
        
        # Store for future use
        self.colors[data_key] = hex_color
        return hex_color
    
    def create_toggle_button(self, data_key):
        """
        Create a button to toggle the visibility of a data series
        
        Args:
            data_key: Key for the data in the historian dictionary
            
        Returns:
            The created button
        """
        # Format the label (replace underscores with spaces and capitalize words)
        label = ' '.join(word.capitalize() for word in data_key.split('_'))
        
        # For component-specific revenue and cost, use a shorter label format
        if data_key.startswith('Rev_'):
            component_type = data_key.split('_')[1]
            component_id = data_key.split('_')[-1]
            label = f"Rev {component_type} {component_id}"
        elif data_key.startswith('Cost_'):
            component_type = data_key.split('_')[1]
            component_id = data_key.split('_')[-1]
            label = f"Cost {component_type} {component_id}"
        
        # Get color for this data series
        color = self.get_color_for_data(data_key)
        
        # Create button with the data key as text
        button = QPushButton(label)
        button.setFixedWidth(150)
        
        # Set button appearance
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: #0A0E22;
                color: #E1E6F9;
                border: 2px solid {color};
                padding: 5px;
                border-radius: 3px;
                text-align: left;
                font-weight: bold;
            }}
            QPushButton:checked {{
                background-color: #1C223F;
                color: #888888;
                border: 1px solid #888888;
            }}
        """)
        
        # Make it checkable (toggle button)
        button.setCheckable(True)
        
        # Set initial state - only specific buttons are unchecked (visible) by default
        button.setChecked(not (data_key == 'satisfied_load' or 
                             data_key == 'cumulative_revenue' or 
                             data_key == 'cumulative_cost' or 
                             data_key == 'system_instability'))
        
        # Connect the clicked signal to update the chart
        button.clicked.connect(lambda checked, k=data_key: self.toggle_line_visibility(k, checked))
        
        return button
    
    def toggle_line_visibility(self, data_key, visible):
        """
        Toggle the visibility of a line in the chart
        
        Args:
            data_key: Key for the data in the historian dictionary
            visible: Whether the line should be visible
        """
        if data_key in self.lines:
            # Update the line's visibility
            self.lines[data_key].set_visible(not visible)
            self.line_visibility[data_key] = not visible
            
            # If a line is toggled, recalculate both axis scales based on all visible lines
            historian_data = self.parent.simulation_engine.historian
            current_time = self.parent.simulation_engine.current_time_step
            
            if current_time > 0:
                # Track maximum values for both axes
                max_val_primary = 0
                max_val_secondary = 0
                
                # Calculate max values considering all visible lines
                for key, line in self.lines.items():
                    if key in historian_data and self.line_visibility.get(key, False):
                        y_values = historian_data[key][:current_time]
                        if y_values and len(y_values) > 0:
                            series_max = max(y_values)
                            if key in self.secondary_axis_series or key.startswith('Rev_') or key.startswith('Cost_'):
                                if series_max > max_val_secondary:
                                    max_val_secondary = series_max
                            else:
                                if series_max > max_val_primary:
                                    max_val_primary = series_max
                
                # Set axis scales based on all visible lines
                if max_val_primary > 0:
                    self.ax.set_ylim(0, max_val_primary * 1.1)  # 10% headroom
                
                if max_val_secondary > 0:
                    self.ax2.set_ylim(0, max_val_secondary * 1.1)  # 10% headroom
                    self.update_secondary_axis_formatting(max_val_secondary * 1.1)
            
            # Update axis visibility
            self.update_axis_visibility()
            
            # Redraw the canvas
            self.canvas.draw()
    
    def update_axis_visibility(self):
        """Update the visibility of the secondary y-axis based on visible lines"""
        # Check if any secondary axis series are visible
        any_secondary_visible = False
        for key in self.lines:
            if (key in self.secondary_axis_series or key.startswith('Rev_') or key.startswith('Cost_')) and self.line_visibility.get(key, True):
                any_secondary_visible = True
                break
        
        # Show/hide secondary axis
        self.ax2.yaxis.set_visible(any_secondary_visible)
        
        # Redraw the canvas
        self.canvas.draw()
    
    def create_line_for_data(self, data_key):
        """
        Create a new line for the given data key
        
        Args:
            data_key: Key for the data in the historian dictionary
            
        Returns:
            The created line object
        """
        # Get color for this data series
        color = self.get_color_for_data(data_key)
        
        # Determine which axis to use
        is_secondary = data_key in self.secondary_axis_series or data_key.startswith('Rev_') or data_key.startswith('Cost_')
        ax = self.ax2 if is_secondary else self.ax
        
        # Create the line with appropriate styling
        line, = ax.plot(
            [], [], '-', 
            color=color, 
            linewidth=0.75,
            alpha=0.9,
            path_effects=[
                path_effects.SimpleLineShadow(
                    shadow_color=color, alpha=0.25, 
                    offset=(0,0), linewidth=12
                ),
                path_effects.Normal()
            ]
        )
        
        # Initialize visibility state
        # satisfied_load, cumulative_revenue, and cumulative_cost start visible by default
        # Rev_* and Cost_* start hidden by default
        initial_visible = (data_key == 'satisfied_load' or 
                          data_key == 'cumulative_revenue' or 
                          data_key == 'cumulative_cost' or 
                          data_key == 'system_instability')
        self.line_visibility[data_key] = initial_visible
        line.set_visible(initial_visible)
        
        return line
    
    def resize_chart_widget(self, width, height):
        """Resize the chart widget to fit the given dimensions"""
        # Check if main_widget exists before resizing
        if hasattr(self, 'main_widget'):
            self.main_widget.resize(width, height)
            # Optionally, force the layout to update immediately
            self.main_layout.activate()
    
    def update_secondary_axis_formatting(self, max_value):
        """
        Update the secondary axis formatting based on the maximum value
        
        Args:
            max_value: The maximum value on the secondary axis
        """
        # Remove the current formatter if it exists
        self.ax2.yaxis.set_major_formatter(ticker.ScalarFormatter())
        
        if max_value >= 1_000_000_000:  # Greater than $1B
            # Format in millions with commas
            def format_func(x, pos):
                # Convert to millions and add commas
                x_in_millions = x / 1_000_000
                if x_in_millions >= 1000:
                    return f"{x_in_millions:,.0f}"
                return f"{x_in_millions:.1f}"
            
            self.ax2.yaxis.set_major_formatter(ticker.FuncFormatter(format_func))
            self.ax2.set_ylabel('Amount ($1,000,000s)', color='#B5BEDF')
            
        elif max_value >= 1_000_000:  # Greater than $1M
            # Format in millions
            def format_func(x, pos):
                return f"{x/1_000_000:.1f}"
            
            self.ax2.yaxis.set_major_formatter(ticker.FuncFormatter(format_func))
            self.ax2.set_ylabel('Amount ($1,000,000s)', color='#B5BEDF')
            
        else:  # Less than $1M
            # Format in thousands
            def format_func(x, pos):
                return f"{x/1_000:.1f}"
            
            self.ax2.yaxis.set_major_formatter(ticker.FuncFormatter(format_func))
            self.ax2.set_ylabel('Amount ($ 1,000s)', color='#B5BEDF')
    
    def update_chart(self):
        """
        Update the histogram chart with current data from the simulation engine
        """
        historian_data = self.parent.simulation_engine.historian
        current_time = self.parent.simulation_engine.current_time_step # Next step to be simulated (e.g., 6 if hour 5 just finished)

        if current_time <= 0:
            # Handle the case where simulation hasn't started or is reset
            self.clear_chart() # Ensure chart is empty if time is 0
            return

        # Track maximum values for both axes
        max_val_primary = 0
        max_val_secondary = 0

        # --- Update Existing Lines ---
        # Iterate through a copy of keys in case dictionary changes during iteration (though unlikely here)
        existing_lines_keys = list(self.lines.keys())
        for data_key in existing_lines_keys:
            if data_key not in historian_data:
                # Data key might exist from a previous run but not current one
                self.lines[data_key].set_data([], []) # Clear data
                continue

            data_values = historian_data[data_key]
            is_cumulative = data_key in self.secondary_axis_series or data_key.startswith('Rev_') or data_key.startswith('Cost_')

            # Determine the number of points to plot and the slice index
            if is_cumulative:
                # Cumulative data index T contains value at *end* of hour T.
                # Last calculated index is current_time - 2 (e.g., index 4 if current_time=6).
                # We need to plot points up to and including this last index.
                # Number of points = (last index) + 1 = (current_time - 2) + 1 = current_time - 1.
                # Slice index = number of points = current_time - 1.
                num_points = max(0, current_time - 1)
                slice_index = num_points
            else:
                # Instantaneous data index T contains value *during* hour T.
                # Last calculated index is current_time - 1 (e.g., index 5 if current_time=6).
                # Number of points = (last index) + 1 = (current_time - 1) + 1 = current_time.
                # Slice index = number of points = current_time.
                num_points = current_time
                slice_index = num_points

            # Generate x_values for the determined range
            current_x_values = list(range(num_points))

            # Slice y_values safely based on the required range end index
            if len(data_values) >= slice_index:
                y_values = data_values[:slice_index]
            else:
                # Fallback if data is shorter than expected (e.g., beginning of sim)
                y_values = data_values[:min(len(data_values), slice_index)]

            # Ensure x and y have the same length (adjust x if y was truncated)
            if len(current_x_values) != len(y_values):
                current_x_values = list(range(len(y_values)))

            # Update the line data
            if data_key in self.lines: # Ensure line exists
                self.lines[data_key].set_data(current_x_values, y_values)

                # Update max value calculation (only consider visible lines for scaling)
                if y_values and self.line_visibility.get(data_key, True):
                    series_max = max(y_values) # y_values confirmed non-empty
                    if is_cumulative:
                        if series_max > max_val_secondary: max_val_secondary = series_max
                    else:
                        if series_max > max_val_primary: max_val_primary = series_max

        # --- Add New Lines (if any new keys appear in historian_data) ---
        for data_key in historian_data.keys():
            if data_key not in self.lines:
                # New data series encountered
                data_values = historian_data[data_key]
                is_cumulative = data_key in self.secondary_axis_series or data_key.startswith('Rev_') or data_key.startswith('Cost_')

                # Determine plot range and slice index for the new line
                if is_cumulative:
                    num_points = max(0, current_time - 1)
                    slice_index = num_points
                else:
                    num_points = current_time
                    slice_index = num_points

                current_x_values = list(range(num_points))

                if len(data_values) >= slice_index:
                    y_values = data_values[:slice_index]
                else:
                    y_values = data_values[:min(len(data_values), slice_index)]

                if len(current_x_values) != len(y_values):
                    current_x_values = list(range(len(y_values)))

                # Create line and button objects
                self.lines[data_key] = self.create_line_for_data(data_key)
                self.lines[data_key].set_data(current_x_values, y_values) # Set initial data

                if data_key not in self.toggle_buttons:
                    button = self.create_toggle_button(data_key)
                    self.toggle_buttons[data_key] = button
                    
                    # Add button to layout in correct section
                    if is_cumulative:
                        self.secondary_buttons.append(button)
                        
                        # Add separator only if this is the first secondary button being added
                        if len(self.secondary_buttons) == 1:
                            separator = QFrame()
                            separator.setFrameShape(QFrame.HLine)
                            separator.setFrameShadow(QFrame.Sunken)
                            separator.setStyleSheet("background-color: #555555;")
                            self.buttons_layout.addWidget(separator)
                        
                        # Determine if this is a default button or component-specific button
                        is_component_specific = data_key.startswith('Rev_') or data_key.startswith('Cost_')
                        
                        # Default secondary buttons go before component-specific ones
                        if not is_component_specific:
                            # Find the position right before the first component-specific secondary button
                            insert_index = None
                            for i, btn in enumerate(self.secondary_buttons):
                                btn_key = next((k for k, v in self.toggle_buttons.items() if v == btn), "")
                                if btn_key.startswith('Rev_') or btn_key.startswith('Cost_'):
                                    # Get the actual widget index
                                    for j in range(self.buttons_layout.count()):
                                        if self.buttons_layout.itemAt(j).widget() == btn:
                                            insert_index = j
                                            break
                                    break
                            
                            if insert_index is not None:
                                self.buttons_layout.insertWidget(insert_index, button)
                            else:
                                # No component-specific buttons yet, add at the end
                                self.buttons_layout.addWidget(button)
                        else:
                            # Component-specific secondary buttons always go at the end
                            self.buttons_layout.addWidget(button)
                    else:
                        self.primary_buttons.append(button)
                        
                        # Determine if this is a default button or component-specific button
                        # Default buttons are pre-defined ones like total_generation, total_load, etc.
                        default_primary = ['total_generation', 'total_load', 'grid_import', 'grid_export', 
                                          'battery_charge', 'system_instability', 'satisfied_load']
                        is_component_specific = data_key not in default_primary
                        
                        if not is_component_specific:
                            # Default primary buttons go at the top of the primary section
                            # Find the index after the last default primary button
                            insert_index = 0
                            for i, btn in enumerate(self.primary_buttons):
                                if btn == button:  # Skip the current button we're adding
                                    continue
                                btn_key = next((k for k, v in self.toggle_buttons.items() if v == btn), "")
                                if btn_key in default_primary:
                                    # Get the actual widget index
                                    for j in range(self.buttons_layout.count()):
                                        if self.buttons_layout.itemAt(j).widget() == btn:
                                            insert_index = j + 1  # After this default button
                            
                            # Insert at the calculated position
                            self.buttons_layout.insertWidget(insert_index, button)
                        else:
                            # Component-specific primary buttons go after all default primary buttons
                            # but before the separator and secondary buttons
                            
                            # Find the separator or first secondary button
                            separator_index = None
                            for i in range(self.buttons_layout.count()):
                                widget = self.buttons_layout.itemAt(i).widget()
                                if isinstance(widget, QFrame) or widget in self.secondary_buttons:
                                    separator_index = i
                                    break
                            
                            # If no separator found, add at the end
                            if separator_index is None:
                                self.buttons_layout.addWidget(button)
                            else:
                                # Insert before separator/secondary buttons
                                self.buttons_layout.insertWidget(separator_index, button)

                    # Update max value if this new line is visible
                    if y_values and self.line_visibility.get(data_key, True):
                        series_max = max(y_values)
                        if is_cumulative:
                            if series_max > max_val_secondary: max_val_secondary = series_max
                        else:
                            if series_max > max_val_primary: max_val_primary = series_max


        # --- Final Steps ---
        # Auto-adjust y scales based on the max values found across all visible lines
        if max_val_primary > 0:
            self.ax.set_ylim(0, max_val_primary * 1.1)  # 10% headroom
        # else: # Optional: Reset ylim if no visible primary lines
        #     self.ax.set_ylim(0, 1000)

        if max_val_secondary > 0:
            self.ax2.set_ylim(0, max_val_secondary * 1.1)  # 10% headroom
            self.update_secondary_axis_formatting(max_val_secondary * 1.1)
        # else: # Optional: Reset ylim if no visible secondary lines
        #     self.ax2.set_ylim(0, 1000)


        # Update axis visibility based on *currently* visible lines
        self.update_axis_visibility() # This already checks visibility state and redraws

        # Explicitly redraw the canvas (update_axis_visibility might already do this, but ensures it happens)
        self.canvas.draw()

    def clear_chart(self):
        """Clear the historian chart display."""
        # Clear all plot lines
        for line in self.lines.values():
            line.set_data([], [])
        
        # Reset view limits
        self.ax.set_xlim(0, 8760)
        self.ax.set_ylim(0, 1000)
        self.ax2.set_ylim(0, 1000)
        
        # Reset the secondary axis formatting
        self.update_secondary_axis_formatting(1000)
        
        # Get list of default buttons to keep
        default_primary = ['total_generation', 'total_load', 'grid_import', 'grid_export', 
                          'battery_charge', 'system_instability', 'satisfied_load']
        default_secondary = ['cumulative_revenue', 'cumulative_cost']
        default_keys = default_primary + default_secondary
        
        # Identify component-specific buttons to remove
        component_keys = []
        for key in list(self.toggle_buttons.keys()):
            if key not in default_keys:
                component_keys.append(key)
        
        # Remove component-specific buttons and lines
        for key in component_keys:
            if key in self.toggle_buttons:
                # Remove button from layout
                button = self.toggle_buttons[key]
                self.buttons_layout.removeWidget(button)
                button.deleteLater()  # Schedule for deletion
                
                # Remove from tracking dictionaries
                del self.toggle_buttons[key]
                
                # Remove from appropriate button list
                if key in self.primary_buttons:
                    self.primary_buttons.remove(key)
                elif key in self.secondary_buttons:
                    self.secondary_buttons.remove(key)
                
                # Remove line from chart (keep in self.lines for now to avoid keys changing during iteration)
                if key in self.lines:
                    self.lines[key].set_visible(False)
        
        # Now remove the corresponding lines from our tracking
        for key in component_keys:
            if key in self.lines:
                # Hide the line but don't try to remove it from the axes
                self.lines[key].set_visible(False)
                # Remove from our tracking dictionaries
                del self.lines[key]
                if key in self.line_visibility:
                    del self.line_visibility[key]
        
        # Reset all default toggle buttons to their default states
        for key, button in self.toggle_buttons.items():
            if (key == 'satisfied_load' or key == 'cumulative_revenue' or 
                key == 'cumulative_cost' or key == 'system_instability'):
                # These series start unchecked (on)
                button.setChecked(False)
                self.line_visibility[key] = True
                self.lines[key].set_visible(True)
            else:
                # All other buttons start checked (off)
                button.setChecked(True)
                self.line_visibility[key] = False
                self.lines[key].set_visible(False)
        
        # Update axis visibility
        self.update_axis_visibility()
        
        # Redraw canvas
        self.canvas.draw()
        print("Historian chart cleared.")

    def initialize_default_data_series(self):
        """
        Initialize the default data series buttons and lines
        even before simulation data is available
        """
        # Default primary series
        default_primary = ['total_generation', 'total_load', 'grid_import', 'grid_export', 
                          'battery_charge', 'system_instability', 'satisfied_load']
        
        # Default secondary series
        default_secondary = ['cumulative_revenue', 'cumulative_cost']
        
        # Create buttons and empty lines for all default series
        for data_key in default_primary:
            # Create line with empty data
            self.lines[data_key] = self.create_line_for_data(data_key)
            self.lines[data_key].set_data([], [])
            
            # Create button
            if data_key not in self.toggle_buttons:
                button = self.create_toggle_button(data_key)
                self.toggle_buttons[data_key] = button
                self.primary_buttons.append(button)
                self.buttons_layout.addWidget(button)
        
        # Add separator before secondary buttons
        if default_secondary:
            separator = QFrame()
            separator.setFrameShape(QFrame.HLine)
            separator.setFrameShadow(QFrame.Sunken)
            separator.setStyleSheet("background-color: #555555;")
            self.buttons_layout.addWidget(separator)
        
        # Create secondary series
        for data_key in default_secondary:
            # Create line with empty data
            self.lines[data_key] = self.create_line_for_data(data_key)
            self.lines[data_key].set_data([], [])
            
            # Create button
            if data_key not in self.toggle_buttons:
                button = self.create_toggle_button(data_key)
                self.toggle_buttons[data_key] = button
                self.secondary_buttons.append(button)
                self.buttons_layout.addWidget(button)
        
        # Update axis visibility based on default visibility settings
        self.update_axis_visibility()
        
        # Draw the canvas with the empty lines
        self.canvas.draw() 