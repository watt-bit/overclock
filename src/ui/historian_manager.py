from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGraphicsScene, QHBoxLayout, QPushButton, QLabel, QScrollArea, QFrame
from PyQt5.QtGui import QColor, QBrush
from PyQt5.QtCore import Qt
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.patheffects as path_effects
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
        self.colors = {  # Default colors for known data types
            'total_generation': '#4CAF50',  # Green
            'total_load': '#FF5722',  # Orange
            'battery_soc': '#2196F3',  # Blue
            'grid_import': '#9C27B0',  # Purple
            'grid_export': '#FFC107',  # Amber
            'cumulative_revenue': '#FF4081',  # Pink for revenue on second axis
            'cumulative_cost': '#8B0000'  # Dark red
        }
        
        # Define which series use secondary y-axis
        self.secondary_axis_series = ['cumulative_revenue', 'cumulative_cost']
        
        # Track buttons to maintain ordering
        self.primary_buttons = []
        self.secondary_buttons = []
        
        self.initialize_historian_scene()
    
    def initialize_historian_scene(self):
        """
        Create the historian scene with a dark grey background
        """
        self.historian_scene = QGraphicsScene()
        
        # Set dark grey background
        background_color = QColor("#1E1E1E")
        self.historian_scene.setBackgroundBrush(QBrush(background_color))
        
        # Create a widget to hold the chart and controls
        self.main_widget = QWidget()
        self.main_layout = QHBoxLayout(self.main_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create left panel for toggle buttons
        self.controls_widget = QWidget()
        self.controls_layout = QVBoxLayout(self.controls_widget)
        self.controls_layout.setAlignment(Qt.AlignTop)
        
        # Add a label for the controls section
        controls_label = QLabel("\n\n\nData Series")
        controls_label.setStyleSheet("color: white; font-weight: bold;")
        self.controls_layout.addWidget(controls_label)
        
        # Create a scroll area for the buttons (in case there are many)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setMinimumWidth(150)  # Set a minimum width
        
        # Create a widget to hold the buttons
        self.buttons_widget = QWidget()
        self.buttons_layout = QVBoxLayout(self.buttons_widget)
        self.buttons_layout.setAlignment(Qt.AlignTop)
        self.buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_area.setWidget(self.buttons_widget)
        
        # Add the scroll area to the controls layout
        self.controls_layout.addWidget(self.scroll_area)
        
        # Create a widget to hold the chart
        self.chart_widget = QWidget()
        self.chart_layout = QVBoxLayout(self.chart_widget)
        self.chart_layout.setContentsMargins(1, 1, 1, 1)
        
        # Add controls and chart widgets to the main layout
        self.main_layout.addWidget(self.controls_widget)
        self.main_layout.addWidget(self.chart_widget)
        self.main_layout.setStretch(0, 0)  # Controls don't stretch
        self.main_layout.setStretch(1, 1)  # Chart stretches to fill space
        
        # Create matplotlib figure for the generation chart
        self.figure = plt.figure(figsize=(12, 6))
        self.figure.patch.set_facecolor('#1E1E1E')  # Dark background for figure
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor('#1E1E1E')  # Dark background for plot area
        
        # Create secondary y-axis
        self.ax2 = self.ax.twinx()
        self.ax2.set_facecolor('#1E1E1E')  # Dark background for plot area
        self.ax2.tick_params(colors='#FF4081')  # Pink ticks for revenue axis
        
        # Adjust subplot parameters to give specified padding
        self.figure.subplots_adjust(left=0.05, right=0.95, bottom=0.09, top=0.96)
        
        # Create canvas for the figure
        self.canvas = FigureCanvas(self.figure)
        self.chart_layout.addWidget(self.canvas)
        
        # Set up the plot - primary axis
        self.ax.set_xlabel('Time Step (hour)', color='white')
        self.ax.set_ylabel('Power (kW)', color='white')
        self.ax.tick_params(colors='white')  # Make tick labels white
        self.ax.grid(True, color='#555555')  # Lighter gray grid
        
        # Set up the plot - secondary axis
        self.ax2.set_ylabel('Amount ($)', color='white')
        self.ax2.tick_params(axis='y', colors='white')
        
        # Set fixed horizontal scale for all 8760 hours
        self.ax.set_xlim(0, 8760)
        self.ax.set_ylim(0, 1000)  # Initial y scale, will auto-adjust
        self.ax2.set_ylim(0, 1000)  # Initial y scale, will auto-adjust
        
        # Add the main widget to the scene
        self.chart_proxy = self.historian_scene.addWidget(self.main_widget)
        
        # Initially draw the empty chart
        self.canvas.draw()
    
    def get_color_for_data(self, data_key):
        """
        Get a color for a data series. Uses predefined colors if available,
        otherwise generates a random color.
        
        Args:
            data_key: Key name for the data series
            
        Returns:
            Color string in hex format
        """
        if data_key in self.colors:
            return self.colors[data_key]
        
        # Generate a new color for unknown keys
        # Use golden ratio to get diverse colors
        golden_ratio_conjugate = 0.618033988749895
        h = hash(data_key) * golden_ratio_conjugate % 1
        rgba = plt.cm.hsv(h)  # This returns 4 values (r, g, b, a)
        r, g, b, _ = rgba  # Unpack and ignore alpha
        
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
        
        # Get color for this data series
        color = self.get_color_for_data(data_key)
        
        # Create button with the data key as text
        button = QPushButton(label)
        
        # Set button appearance
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: black;
                border: none;
                padding: 5px;
                border-radius: 3px;
                text-align: left;
                font-weight: bold;
            }}
            QPushButton:checked {{
                background-color: #444444;
                color: #888888;
            }}
        """)
        
        # Make it checkable (toggle button)
        button.setCheckable(True)
        
        # Set initial state - total_generation and cumulative_revenue are unchecked (visible) by default
        button.setChecked(data_key != 'total_generation' and data_key != 'cumulative_revenue')
        
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
                            if key in self.secondary_axis_series:
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
            
            # Update axis visibility
            self.update_axis_visibility()
            
            # Redraw the canvas
            self.canvas.draw()
    
    def update_axis_visibility(self):
        """Update the visibility of the secondary y-axis based on visible lines"""
        # Check if any secondary axis series are visible
        any_secondary_visible = False
        for key in self.secondary_axis_series:
            if key in self.lines and self.line_visibility.get(key, True):
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
        ax = self.ax2 if data_key in self.secondary_axis_series else self.ax
        
        # Create the line with appropriate styling
        line, = ax.plot(
            [], [], '-', 
            color=color, 
            linewidth=0.5,
            alpha=0.8,
            path_effects=[
                path_effects.SimpleLineShadow(
                    shadow_color=color, alpha=0.2, 
                    offset=(0,0), linewidth=10
                ),
                path_effects.Normal()
            ]
        )
        
        # Initialize visibility state
        # total_generation and cumulative_revenue start visible by default
        initial_visible = data_key == 'total_generation' or data_key == 'cumulative_revenue'
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
            is_cumulative = data_key in self.secondary_axis_series

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
                is_cumulative = data_key in self.secondary_axis_series

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
                        self.buttons_layout.addWidget(button) # Add to the end
                    else:
                        self.primary_buttons.append(button)
                        # Insert primary buttons before the separator/secondary buttons
                        insert_index = self.buttons_layout.count() - len(self.secondary_buttons)
                        if self.secondary_buttons: # If secondary buttons exist, account for the separator
                             insert_index -= 1
                        # Insert at calculated index, ensuring it's not negative
                        self.buttons_layout.insertWidget(max(0, insert_index), button)

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
        
        # Reset all toggle buttons to their default states
        for key, button in self.toggle_buttons.items():
            if key == 'total_generation' or key == 'cumulative_revenue':
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