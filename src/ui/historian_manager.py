from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGraphicsScene
from PyQt5.QtGui import QColor, QBrush
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
        self.colors = {  # Default colors for known data types
            'total_generation': '#4CAF50',  # Green
            'load': '#FF5722',  # Orange
            'battery_soc': '#2196F3',  # Blue
            'grid_import': '#9C27B0',  # Purple
            'grid_export': '#FFC107',  # Amber
        }
        self.initialize_historian_scene()
    
    def initialize_historian_scene(self):
        """
        Create the historian scene with a dark grey background
        """
        self.historian_scene = QGraphicsScene()
        
        # Set dark grey background
        background_color = QColor("#1E1E1E")
        self.historian_scene.setBackgroundBrush(QBrush(background_color))
        
        # Create a widget to hold the chart
        self.chart_widget = QWidget()
        self.chart_layout = QVBoxLayout(self.chart_widget)
        
        # Create matplotlib figure for the generation chart
        self.figure = plt.figure(figsize=(12, 6))
        self.figure.patch.set_facecolor('#1E1E1E')  # Dark background for figure
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor('#1E1E1E')  # Dark background for plot area
        
        # Adjust subplot parameters to give specified padding
        self.figure.subplots_adjust(left=0.05, right=0.99, bottom=0.09, top=0.96)
        
        # Create canvas for the figure
        self.canvas = FigureCanvas(self.figure)
        self.chart_layout.addWidget(self.canvas)
        
        # Set up the plot
        self.ax.set_xlabel('Time Step (hour)', color='white')
        self.ax.set_ylabel('Power (kW)', color='white')
        self.ax.tick_params(colors='white')  # Make tick labels white
        self.ax.grid(True, color='#555555')  # Lighter gray grid
        
        # Set fixed horizontal scale for all 8760 hours
        self.ax.set_xlim(0, 8760)
        self.ax.set_ylim(0, 1000)  # Initial y scale, will auto-adjust
        
        # Add the chart widget to the scene
        self.chart_proxy = self.historian_scene.addWidget(self.chart_widget)
        
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
    
    def create_line_for_data(self, data_key):
        """
        Create a new line for the given data key
        
        Args:
            data_key: Key for the data in the historian dictionary
            
        Returns:
            The created line object
        """
        # Format the label (replace underscores with spaces and capitalize words)
        label = ' '.join(word.capitalize() for word in data_key.split('_'))
        
        # Get color for this data series
        color = self.get_color_for_data(data_key)
        
        # Create the line with appropriate styling
        line, = self.ax.plot(
            [], [], '-', 
            color=color, 
            linewidth=0.5,
            label=label, 
            alpha=0.8,
            path_effects=[
                path_effects.SimpleLineShadow(
                    shadow_color=color, alpha=0.2, 
                    offset=(0,0), linewidth=10
                ),
                path_effects.Normal()
            ]
        )
        
        return line
    
    def resize_chart_widget(self, width, height):
        """Resize the chart widget to fit the given dimensions"""
        # Check if chart_widget exists before resizing
        if hasattr(self, 'chart_widget'):
            self.chart_widget.resize(width, height)
            # Optionally, force the layout to update immediately
            self.chart_layout.activate()
    
    def update_chart(self):
        """
        Update the histogram chart with current data from the simulation engine
        """
        # Get the historian data from the simulation engine
        historian_data = self.parent.simulation_engine.historian
        current_time = self.parent.simulation_engine.current_time_step
        
        if current_time <= 0:
            return
        
        # Common x values for all data series
        x_values = list(range(current_time))
        
        # Track maximum value across all series for y-axis scaling
        max_val = 0
        
        # Create/update lines for each data series in the historian
        for data_key, data_values in historian_data.items():
            # Skip if not enough data
            if len(data_values) < current_time:
                continue
                
            # Get y values up to current time
            y_values = data_values[:current_time]
            
            # Create a new line if this data series doesn't have one yet
            if data_key not in self.lines:
                self.lines[data_key] = self.create_line_for_data(data_key)
            
            # Update the line data
            self.lines[data_key].set_data(x_values, y_values)
            
            # Update max value
            if y_values:
                series_max = max(y_values)
                if series_max > max_val:
                    max_val = series_max
        
        # Update the legend
        if self.lines:
            legend = self.ax.legend(framealpha=0.8)
            legend.get_frame().set_facecolor('#2D2D2D')
            for text in legend.get_texts():
                text.set_color('white')
                text.set_fontsize(9)
        
        # Auto-adjust y scale based on the max value
        if max_val > 0:
            self.ax.set_ylim(0, max_val * 1.1)  # 10% headroom
        
        # Redraw the canvas
        self.canvas.draw()

    def clear_chart(self):
        """Clear the historian chart display."""
        # Clear all plot lines
        for line in self.lines.values():
            line.set_data([], [])
        
        # Reset view limits
        self.ax.set_xlim(0, 8760)
        self.ax.set_ylim(0, 1000)
        
        # Redraw canvas
        self.canvas.draw()
        print("Historian chart cleared.") 