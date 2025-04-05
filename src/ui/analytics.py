from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QLabel, 
                            QProgressBar, QGroupBox, QPushButton, QHBoxLayout)
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.patheffects as path_effects

class AnalyticsPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
        # Add safeguard for drawing
        self.is_drawing = False
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Create matplotlib figure and canvas for time series
        chart_group = QGroupBox()
        chart_layout = QVBoxLayout()
        
        # Create figure with adjusted size and margins for power chart
        self.figure = plt.figure(figsize=(6, 4))
        self.figure.patch.set_facecolor('#141414')  # Dark background for figure
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor('#1E1E1E')  # Dark background for plot area
        # Adjust subplot parameters to give specified padding
        self.figure.subplots_adjust(left=0.15, right=0.98, bottom=0.12, top=0.98)
        self.canvas = FigureCanvas(self.figure)
        
        # Initialize empty data lists
        self.time_data = []
        self.generation_data = []
        self.battery_data = []  # Battery power data (positive=discharge, negative=charge)
        self.grid_import_data = []
        self.grid_export_data = []
        self.load_data = []
        self.surplus_data = []
        self.unused_capacity_data = []
        
        # Set up the plot
        self.ax.set_xlabel('Time Step (hour)', color='white')
        self.ax.set_ylabel('Power (kW)', color='white')
        self.ax.tick_params(colors='white')  # Make tick labels white
        self.ax.grid(True, color='#555555')  # Lighter gray grid
        
        # Create empty lines with labels - matching progress bar colors
        self.generation_line, = self.ax.plot([], [], '-', color='#4CAF50', linewidth=2, label='Local Generation', alpha=0.9,
                                            path_effects=[path_effects.SimpleLineShadow(shadow_color='#4CAF50', alpha=0.2, offset=(0,0), linewidth=7),
                                                        path_effects.Normal()])
                                                        
        self.battery_line, = self.ax.plot([], [], '-', color='#9c27b0', linewidth=2, label='Net Battery Power', alpha=0.9,
                                         path_effects=[path_effects.SimpleLineShadow(shadow_color='#9c27b0', alpha=0.2, offset=(0,0), linewidth=7),
                                                     path_effects.Normal()])  # Purple for battery
                                                     
        self.grid_line, = self.ax.plot([], [], '-', color='#2196F3', linewidth=2, label='Grid Import', alpha=0.9,
                                      path_effects=[path_effects.SimpleLineShadow(shadow_color='#2196F3', alpha=0.2, offset=(0,0), linewidth=7),
                                                  path_effects.Normal()])
                                                  
        self.grid_export_line, = self.ax.plot([], [], '-', color='#00bcd4', linewidth=2, label='Grid Export', alpha=0.9,
                                             path_effects=[path_effects.SimpleLineShadow(shadow_color='#00bcd4', alpha=0.2, offset=(0,0), linewidth=7),
                                                         path_effects.Normal()])
                                                         
        self.load_line, = self.ax.plot([], [], '-', color='#FFA500', linewidth=2, label='Load', alpha=0.9,
                                      path_effects=[path_effects.SimpleLineShadow(shadow_color='#FFA500', alpha=0.2, offset=(0,0), linewidth=7),
                                                  path_effects.Normal()])
                                                  
        self.surplus_line, = self.ax.plot([], [], ':', color='#f44336', linewidth=2, label='Surplus/Deficit', alpha=0.9,
                                         path_effects=[path_effects.SimpleLineShadow(shadow_color='#f44336', alpha=0.2, offset=(0,0), linewidth=7),
                                                     path_effects.Normal()])
                                                     
        self.unused_capacity_line, = self.ax.plot([], [], ':', color='#4CAF50', linewidth=2, label='Unused Capacity', alpha=0.7,
                                                 path_effects=[path_effects.SimpleLineShadow(shadow_color='#FFC107', alpha=0.2, offset=(0,0), linewidth=7),
                                                             path_effects.Normal()])
        
        # Update legend with dark mode styling
        legend = self.ax.legend(framealpha=0.8)
        legend.get_frame().set_facecolor('#2D2D2D')
        for text in legend.get_texts():
            text.set_color('white')
            text.set_fontsize(9)  # Reduce font size for legend text
        
        # Add zero line for surplus/deficit reference
        self.ax.axhline(y=0, color='#888888', linestyle='-', alpha=0.5)
        
        # Set initial view limits (modified for 8760-hour view)
        self.ax.set_xlim(0, 96)  # Show first 96 hours by default
        self.ax.set_ylim(-1000, 1000)
        
        # Add matplotlib canvas to layout
        chart_layout.addWidget(self.canvas)
        
        chart_group.setLayout(chart_layout)
        layout.addWidget(chart_group)
        
        # Create container for current values with columns
        bars_group = QGroupBox()
        bars_container_layout = QHBoxLayout()
        
        # Left column for most common bars
        left_column = QFormLayout()
        
        # Time label
        self.time_value_label = QLabel("0 hr")
        self.time_value_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        left_column.addRow("Time:", self.time_value_label)
        
        # Generation bar
        self.generation_bar = QProgressBar()
        self.generation_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid grey;
                border-radius: 5px;
                text-align: center;
                background-color: #f0f0f0;
                color: black;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
            }
        """)
        left_column.addRow("Generation:", self.generation_bar)
        
        # Battery power bar (renamed from battery discharge)
        self.battery_bar = QProgressBar()
        self.battery_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid grey;
                border-radius: 5px;
                text-align: center;
                background-color: #f0f0f0;
                color: black;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #9c27b0;
            }
        """)
        left_column.addRow("Net Battery:", self.battery_bar)
        
        # Grid import bar
        self.grid_import_bar = QProgressBar()
        self.grid_import_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid grey;
                border-radius: 5px;
                text-align: center;
                background-color: #f0f0f0;
                color: black;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #2196F3;
            }
        """)
        left_column.addRow("Grid Import:", self.grid_import_bar)
        
        # Grid export bar
        self.grid_export_bar = QProgressBar()
        self.grid_export_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid grey;
                border-radius: 5px;
                text-align: center;
                background-color: #f0f0f0;
                color: black;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #00bcd4;
            }
        """)
        left_column.addRow("Grid Export:", self.grid_export_bar)
        
        # Load bar
        self.load_bar = QProgressBar()
        self.load_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid grey;
                border-radius: 5px;
                text-align: center;
                background-color: #f0f0f0;
                color: black;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #f44336;
            }
        """)
        left_column.addRow("Load:", self.load_bar)
        
        # Right column
        right_column = QFormLayout()
        
        # Surplus/Deficit bar
        self.surplus_bar = QProgressBar()
        self.surplus_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid grey;
                border-radius: 5px;
                text-align: center;
                background-color: #f0f0f0;
                color: black;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #2196F3;
            }
        """)
        right_column.addRow("Surplus/Deficit:", self.surplus_bar)
        
        # Unused capacity bar
        self.unused_capacity_bar = QProgressBar()
        self.unused_capacity_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid grey;
                border-radius: 5px;
                text-align: center;
                background-color: #f0f0f0;
                color: black;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #FFC107;
            }
        """)
        right_column.addRow("Unused Capacity:", self.unused_capacity_bar)
        
        # Use labels for volumetric metrics instead of progress bars
        # Total imported energy label
        self.total_imported_label = QLabel("0 MWh")
        self.total_imported_label.setStyleSheet("font-weight: bold;")
        right_column.addRow("Total Imported:", self.total_imported_label)
        
        # Total exported energy label
        self.total_exported_label = QLabel("0 MWh")
        self.total_exported_label.setStyleSheet("font-weight: bold;")
        right_column.addRow("Total Exported:", self.total_exported_label)
        
        # Net grid energy label
        self.net_energy_label = QLabel("0 MWh")
        self.net_energy_label.setStyleSheet("font-weight: bold;")
        right_column.addRow("Net To/From Grid:", self.net_energy_label)
        
        # System stability label
        self.stable_label = QLabel("Yes")
        self.stable_label.setStyleSheet("font-weight: bold; color: green;")
        right_column.addRow("Stable:", self.stable_label)
        
        # Add new label for total battery charge
        self.total_battery_charge_label = QLabel("0 MWh")
        self.total_battery_charge_label.setStyleSheet("font-weight: bold;")
        right_column.addRow("Total Battery Charge:", self.total_battery_charge_label)
        
        # Add columns to container
        bars_container_layout.addLayout(left_column)
        bars_container_layout.addLayout(right_column)
        
        # Set container as the layout for the group
        bars_group.setLayout(bars_container_layout)
        layout.addWidget(bars_group)
        
        # Create new revenue chart figure - now positioned below the bars
        revenue_group = QGroupBox()
        revenue_layout = QVBoxLayout()
        
        # Create figure with adjusted size and margins for revenue chart
        self.revenue_figure = plt.figure(figsize=(6, 3))
        self.revenue_figure.patch.set_facecolor('#141414')  # Dark background for figure
        self.revenue_ax = self.revenue_figure.add_subplot(111)
        self.revenue_ax.set_facecolor('#1E1E1E')  # Dark background for plot area
        # Adjust subplot parameters to give specified padding
        self.revenue_figure.subplots_adjust(left=0.15, right=0.98, bottom=0.18, top=0.95)
        self.revenue_canvas = FigureCanvas(self.revenue_figure)
        
        # Initialize revenue data
        self.gross_revenue_data = [0.0] * 8761  # Initialize with 0s (hours 0-8760)
        
        # Set up the plot
        self.revenue_ax.set_xlabel('Time Step (hour)', color='white')
        self.revenue_ax.set_ylabel('Revenue ($)', color='white')
        self.revenue_ax.tick_params(colors='white')  # Make tick labels white
        self.revenue_ax.grid(True, color='#555555')  # Lighter gray grid
        
        # Create empty line for gross revenue
        self.gross_revenue_line, = self.revenue_ax.plot([], [], '-', color='#FFC107', linewidth=2, label='Gross Revenue', alpha=0.9,
                                                      path_effects=[path_effects.SimpleLineShadow(shadow_color='#FFC107', alpha=0.2, offset=(0,0), linewidth=7),
                                                                  path_effects.Normal()])
        
        # Update legend with dark mode styling
        revenue_legend = self.revenue_ax.legend(framealpha=0.8)
        revenue_legend.get_frame().set_facecolor('#2D2D2D')
        for text in revenue_legend.get_texts():
            text.set_color('white')
            text.set_fontsize(9)  # Reduce font size for legend text
        
        # Set fixed horizontal scale for all 8760 hours
        self.revenue_ax.set_xlim(0, 8760)
        self.revenue_ax.set_ylim(0, 100)  # Initial y scale, will auto-adjust
        
        # Add matplotlib canvas to layout
        revenue_layout.addWidget(self.revenue_canvas)
        
        revenue_group.setLayout(revenue_layout)
        layout.addWidget(revenue_group)
        
        # Hidden labels for values (not displayed but used to store data)
        self.power_produced_label = QLabel("0 kW")
        self.grid_import_label = QLabel("0 kW")
        self.grid_export_label = QLabel("0 kW")
        self.power_consumed_label = QLabel("0 kW")
        self.power_balance_label = QLabel("0 kW")
        self.unused_capacity_label = QLabel("0 kW")
    
    def update_analytics(self, power_produced, power_consumed, current_time,
                         total_capacity=0, is_scrubbing=False, grid_import=0, grid_export=0,
                         total_imported=0, total_exported=0, system_stable=True, battery_power=0, 
                         total_battery_charge=0, gross_revenue_data=None):
        # Protect against re-entrance
        if self.is_drawing:
            return
            
        # Calculate surplus/deficit (after accounting for grid export and battery activity)
        # When battery_power is negative (charging), count it as additional consumption
        # When battery_power is positive (discharging), count it as additional production
        battery_charging = min(0, battery_power)  # Will be negative or zero
        battery_discharging = max(0, battery_power)  # Will be positive or zero
        
        # Note: power_produced already includes battery discharge from main_window.py
        # So we don't need to adjust it, just for charging
        adjusted_consumption = power_consumed - battery_charging  # Subtract negative value = add to consumption
        
        # Final surplus/deficit calculation - don't subtract battery_discharging since it's already included
        power_surplus = (power_produced + grid_import - grid_export) - adjusted_consumption
        
        # Make sure unused capacity calculation ignores battery completely
        # Extract the generator-only production (without battery) and use that for unused capacity
        base_generation = power_produced - battery_discharging
        unused_capacity = total_capacity - base_generation
        
        # Always update time display, even in scrub mode
        self.time_value_label.setText(f"{current_time} hr")
        
        # If in scrub mode, don't update any other UI elements
        if is_scrubbing:
            return
            
        # Calculate maximum value for scaling the bars
        max_power = max(power_produced, abs(battery_power), grid_import, grid_export, adjusted_consumption, abs(power_surplus), unused_capacity, 1000)
        
        # Update generation bar (excluding battery)
        self.generation_bar.setMaximum(int(max_power))
        self.generation_bar.setValue(int(power_produced))
        self.generation_bar.setFormat(f"{power_produced:.0f} kW")
        
        # Update battery bar - can be positive (discharging) or negative (charging)
        self.battery_bar.setMaximum(int(max_power))
        self.battery_bar.setMinimum(int(-max_power))
        self.battery_bar.setValue(int(battery_power))
        battery_text = f"+{battery_power:.0f} kW" if battery_power >= 0 else f"{battery_power:.0f} kW"
        self.battery_bar.setFormat(battery_text)
        
        # Update grid import bar
        self.grid_import_bar.setMaximum(int(max_power))
        self.grid_import_bar.setValue(int(grid_import))
        self.grid_import_bar.setFormat(f"{grid_import:.0f} kW")
        
        # Update grid export bar
        self.grid_export_bar.setMaximum(int(max_power))
        self.grid_export_bar.setValue(int(grid_export))
        self.grid_export_bar.setFormat(f"{grid_export:.0f} kW")
        
        # Update load bar
        self.load_bar.setMaximum(int(max_power))
        self.load_bar.setValue(int(adjusted_consumption))
        self.load_bar.setFormat(f"{adjusted_consumption:.0f} kW")
        
        # Update surplus/deficit bar
        self.surplus_bar.setMaximum(int(max_power))
        self.surplus_bar.setMinimum(int(-max_power))
        self.surplus_bar.setValue(int(power_surplus))
        surplus_text = f"+{power_surplus:.0f} kW" if power_surplus >= 0 else f"{power_surplus:.0f} kW"
        self.surplus_bar.setFormat(surplus_text)
        
        # Update unused capacity bar
        self.unused_capacity_bar.setMaximum(int(max_power))
        self.unused_capacity_bar.setValue(int(unused_capacity))
        self.unused_capacity_bar.setFormat(f"{unused_capacity:.0f} kW")
        
        # Update cumulative energy values - convert to MWh by dividing by 1000
        total_imported_mwh = total_imported / 1000.0
        total_exported_mwh = total_exported / 1000.0
        net_energy_mwh = (total_imported - total_exported) / 1000.0
        
        # Update the energy labels with MWh units
        self.total_imported_label.setText(f"{total_imported_mwh:,.2f} MWh")
        self.total_exported_label.setText(f"{total_exported_mwh:,.2f} MWh")
        
        # Use +/- formatting for net grid energy
        if net_energy_mwh >= 0:
            self.net_energy_label.setText(f"+{net_energy_mwh:,.2f} MWh")
        else:
            self.net_energy_label.setText(f"{net_energy_mwh:,.2f} MWh")  # Already has minus sign
        
        # Update stability label
        if system_stable:
            self.stable_label.setText("Yes")
            self.stable_label.setStyleSheet("font-weight: bold; color: green;")
        else:
            self.stable_label.setText("No")
            self.stable_label.setStyleSheet("font-weight: bold; color: red;")
        
        # Update total battery charge (already in MWh)
        self.total_battery_charge_label.setText(f"{total_battery_charge:,.2f} MWh")
        
        # Update hidden labels
        self.power_produced_label.setText(f"{power_produced:.2f} kW")
        self.grid_import_label.setText(f"{grid_import:.2f} kW")
        self.grid_export_label.setText(f"{grid_export:.2f} kW")
        self.power_consumed_label.setText(f"{power_consumed:.2f} kW")
        self.power_balance_label.setText(f"{power_surplus:.2f} kW")
        self.unused_capacity_label.setText(f"{unused_capacity:.2f} kW")
        
        # Handle time series data based on whether we're moving forward or backward
        if not self.time_data or current_time > self.time_data[-1]:
            # Moving forward - normal operation, append data
            # Keep last 100 points
            if len(self.time_data) > 100:
                self.time_data.pop(0)
                self.generation_data.pop(0)
                self.battery_data.pop(0)
                self.grid_import_data.pop(0)
                self.grid_export_data.pop(0)
                self.load_data.pop(0)
                self.surplus_data.pop(0)
                self.unused_capacity_data.pop(0)
            
            self.time_data.append(current_time)
            self.generation_data.append(power_produced)
            self.battery_data.append(battery_power)
            self.grid_import_data.append(grid_import)
            self.grid_export_data.append(grid_export)
            self.load_data.append(adjusted_consumption)
            self.surplus_data.append(power_surplus)
            self.unused_capacity_data.append(unused_capacity)
        else:
            # Moving backward or staying at current time
            if current_time in self.time_data:
                # If we've seen this time before, find and update its values
                idx = self.time_data.index(current_time)
                self.generation_data[idx] = power_produced
                self.battery_data[idx] = battery_power
                self.grid_import_data[idx] = grid_import
                self.grid_export_data[idx] = grid_export
                self.load_data[idx] = adjusted_consumption
                self.surplus_data[idx] = power_surplus
                self.unused_capacity_data[idx] = unused_capacity
            else:
                # Insert at appropriate position - find first time greater than current
                idx = 0
                while idx < len(self.time_data) and self.time_data[idx] < current_time:
                    idx += 1
                
                # Insert at this position
                self.time_data.insert(idx, current_time)
                self.generation_data.insert(idx, power_produced)
                self.battery_data.insert(idx, battery_power)
                self.grid_import_data.insert(idx, grid_import)
                self.grid_export_data.insert(idx, grid_export)
                self.load_data.insert(idx, adjusted_consumption)
                self.surplus_data.insert(idx, power_surplus)
                self.unused_capacity_data.insert(idx, unused_capacity)
                
                # Maintain max 100 points
                if len(self.time_data) > 100:
                    self.time_data.pop(0)
                    self.generation_data.pop(0)
                    self.battery_data.pop(0)
                    self.grid_import_data.pop(0)
                    self.grid_export_data.pop(0)
                    self.load_data.pop(0)
                    self.surplus_data.pop(0)
                    self.unused_capacity_data.pop(0)
        
        # Sort all data by time to ensure proper rendering
        if self.time_data:
            # Get indices that would sort the time data
            sorted_indices = sorted(range(len(self.time_data)), key=lambda i: self.time_data[i])
            
            # Apply sorting to all data lists
            self.time_data = [self.time_data[i] for i in sorted_indices]
            self.generation_data = [self.generation_data[i] for i in sorted_indices]
            self.battery_data = [self.battery_data[i] for i in sorted_indices]
            self.grid_import_data = [self.grid_import_data[i] for i in sorted_indices]
            self.grid_export_data = [self.grid_export_data[i] for i in sorted_indices]
            self.load_data = [self.load_data[i] for i in sorted_indices]
            self.surplus_data = [self.surplus_data[i] for i in sorted_indices]
            self.unused_capacity_data = [self.unused_capacity_data[i] for i in sorted_indices]
        
        # Update line data
        self.generation_line.set_data(self.time_data, self.generation_data)
        self.battery_line.set_data(self.time_data, self.battery_data)
        self.grid_line.set_data(self.time_data, self.grid_import_data)
        self.grid_export_line.set_data(self.time_data, self.grid_export_data)
        self.load_line.set_data(self.time_data, self.load_data)
        self.surplus_line.set_data(self.time_data, self.surplus_data)
        self.unused_capacity_line.set_data(self.time_data, self.unused_capacity_data)
        
        # Update view limits if needed
        if self.time_data:
            # Show last 168 hours (1 week) or less if not enough data
            window_size = 168
            self.ax.set_xlim(max(0, current_time - window_size), max(168, current_time + 1))
            max_val = max(
                max(self.generation_data) if self.generation_data else 0,
                max(self.grid_import_data) if self.grid_import_data else 0,
                max(self.grid_export_data) if self.grid_export_data else 0,
                max(self.load_data) if self.load_data else 0,
                max(self.unused_capacity_data) if self.unused_capacity_data else 0,
                1000
            )
            min_val = min(min(self.surplus_data) if self.surplus_data else 0, -1000)
            self.ax.set_ylim(min_val * 1.1, max_val * 1.1)
        
        # Update the revenue chart if gross_revenue_data is provided
        if gross_revenue_data is not None:
            # Update our stored copy of the data
            self.gross_revenue_data = gross_revenue_data
            
            # Create x-axis values, but only up to the current time step
            x_values = list(range(current_time + 1))
            
            # Calculate cumulative revenue (sum of all revenue up to each time point)
            # But only include values up to the current time step
            cumulative_revenue = []
            total = 0.0
            for i, revenue in enumerate(self.gross_revenue_data):
                if i > current_time:
                    break
                total += revenue
                cumulative_revenue.append(total)
            
            # Update line data with cumulative revenue instead of hourly revenue
            self.gross_revenue_line.set_data(x_values, cumulative_revenue)
            
            # Auto-adjust y scale based on cumulative values
            max_revenue = max(cumulative_revenue) if cumulative_revenue else 100
            if max_revenue > 0:
                self.revenue_ax.set_ylim(0, max_revenue * 1.1)  # 10% headroom
            
            # Draw the revenue canvas
            try:
                self.is_drawing = True
                self.revenue_canvas.draw()
            finally:
                self.is_drawing = False
        
        # Draw the canvas with protection against recursion
        try:
            self.is_drawing = True
            self.canvas.draw()
        finally:
            self.is_drawing = False
    
    def clear_chart_history(self):
        # Protect against re-entrance
        if self.is_drawing:
            return
            
        # Clear data lists
        self.time_data.clear()
        self.generation_data.clear()
        self.battery_data.clear()
        self.grid_import_data.clear()
        self.grid_export_data.clear()
        self.load_data.clear()
        self.surplus_data.clear()
        self.unused_capacity_data.clear()
        
        # Reset revenue data
        self.gross_revenue_data = [0.0] * 8761
        
        # Clear plot lines
        self.generation_line.set_data([], [])
        self.battery_line.set_data([], [])
        self.grid_line.set_data([], [])
        self.grid_export_line.set_data([], [])
        self.load_line.set_data([], [])
        self.surplus_line.set_data([], [])
        self.unused_capacity_line.set_data([], [])
        self.gross_revenue_line.set_data([], [])
        
        # Reset view limits (adjusted for 8760-hour scale)
        self.ax.set_xlim(0, 168)  # Show first week (168 hours)
        self.ax.set_ylim(-1000, 1000)
        self.revenue_ax.set_xlim(0, 8760)  # Show full year
        self.revenue_ax.set_ylim(0, 100)
        
        # Ensure dark mode styling is maintained for both charts
        self.ax.set_facecolor('#3D3D3D')
        self.figure.patch.set_facecolor('#2D2D2D')
        self.ax.grid(True, color='#555555')
        
        self.revenue_ax.set_facecolor('#3D3D3D')
        self.revenue_figure.patch.set_facecolor('#2D2D2D')
        self.revenue_ax.grid(True, color='#555555')
        
        # Apply dark mode styling to spine lines
        for spine in self.ax.spines.values():
            spine.set_color('#888888')
        
        for spine in self.revenue_ax.spines.values():
            spine.set_color('#888888')
        
        # Redraw canvas with protection
        try:
            self.is_drawing = True
            self.canvas.draw()
            self.revenue_canvas.draw()
        finally:
            self.is_drawing = False 