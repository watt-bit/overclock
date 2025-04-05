from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGraphicsScene
from PyQt5.QtGui import QColor, QBrush
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.patheffects as path_effects

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
        self.initialize_historian_scene()
    
    def initialize_historian_scene(self):
        """
        Create the historian scene with a dark grey background
        """
        self.historian_scene = QGraphicsScene()
        
        # Set dark grey background
        background_color = QColor("#141414")
        self.historian_scene.setBackgroundBrush(QBrush(background_color))
        
        # Create a widget to hold the chart
        self.chart_widget = QWidget()
        self.chart_layout = QVBoxLayout(self.chart_widget)
        
        # Create matplotlib figure for the generation chart
        self.figure = plt.figure(figsize=(12, 6))
        self.figure.patch.set_facecolor('#141414')  # Dark background for figure
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
        
        # Create empty line for generation data with the same color as in analytics
        self.generation_line, = self.ax.plot([], [], '-', color='#4CAF50', linewidth=0.5, 
                                            label='Total Generation', alpha=0.8,
                                            path_effects=[
                                                path_effects.SimpleLineShadow(
                                                    shadow_color='#4CAF50', alpha=0.2, 
                                                    offset=(0,0), linewidth=10
                                                ),
                                                path_effects.Normal()
                                            ])
        
        # Update legend with dark mode styling
        legend = self.ax.legend(framealpha=0.8)
        legend.get_frame().set_facecolor('#2D2D2D')
        for text in legend.get_texts():
            text.set_color('white')
            text.set_fontsize(9)  # Reduce font size for legend text
        
        # Set fixed horizontal scale for all 8760 hours
        self.ax.set_xlim(0, 8760)
        self.ax.set_ylim(0, 1000)  # Initial y scale, will auto-adjust
        
        # Add the chart widget to the scene
        self.chart_proxy = self.historian_scene.addWidget(self.chart_widget)
        
        # Remove fixed positioning, rely on resize
        # chart_proxy.setPos(0, 0)
        
        # Initially draw the empty chart
        self.canvas.draw()
    
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
            
        # Get the generation data up to the current time
        x_values = list(range(current_time))
        y_values = historian_data['total_generation'][:current_time]

        # Update the chart data
        self.generation_line.set_data(x_values, y_values)
        
        # Auto-adjust y scale based on the data
        if y_values:
            max_val = max(y_values)
            if max_val > 0:
                self.ax.set_ylim(0, max_val * 1.1)  # 10% headroom
        
        # Redraw the canvas
        self.canvas.draw()

    def clear_chart(self):
        """Clear the historian chart display."""
        # Clear plot lines
        self.generation_line.set_data([], [])
        
        # Reset view limits
        self.ax.set_xlim(0, 8760)
        self.ax.set_ylim(0, 1000)
        
        # Redraw canvas
        self.canvas.draw()
        print("Historian chart cleared.") 