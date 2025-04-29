class CapexManager:
    def __init__(self, main_window):
        self.main_window = main_window
        # Initialize previous_capex with a default of 0
        # This handles the case where main_window doesn't have previous_capex yet
        self.previous_capex = getattr(main_window, 'previous_capex', 0)
    
    def calculate_total_capex(self):
        """Calculate the total CAPEX of all components in the system"""
        total_capex = 0
        
        for component in self.main_window.components:
            # Only include components that have capex_per_kw and a capacity/power attribute
            if hasattr(component, 'capex_per_kw'):
                capacity = 0
                # Different components have capacity in different attributes
                if hasattr(component, 'capacity'):
                    capacity = component.capacity
                elif hasattr(component, 'power_capacity'):
                    capacity = component.power_capacity
                elif hasattr(component, 'demand'):
                    capacity = component.demand
                    
                # Add the component's CAPEX to the total
                if capacity > 0:
                    total_capex += component.capex_per_kw * capacity
        
        return total_capex
    
    def update_capex_display(self):
        """Update the CAPEX display with the current total"""
        if hasattr(self.main_window, 'capex_label'):
            total_capex = self.calculate_total_capex()
            
            # Check for million dollar milestones
            self.check_capex_milestone(total_capex)
            
            # Format the CAPEX value with commas for thousands
            formatted_capex = f"{total_capex:,.0f}"
            
            # Update the label text with HTML formatting to make $ and value gold
            self.main_window.capex_label.setText(f"CAPEX <span style='color: #FFCA28;'>${formatted_capex}</span>")
            self.main_window.capex_label.adjustSize()  # Resize to fit new content
            
            # Ensure it stays in the correct position
            if hasattr(self.main_window, 'view') and self.main_window.view:
                self.main_window.capex_label.move(10, self.main_window.view.height() - self.main_window.capex_label.height() - 65)
    
    def check_capex_milestone(self, current_capex):
        """Check if CAPEX has crossed a $1,000,000 milestone and create a particle if needed"""
        # Skip if we're not in a scene or not properly initialized
        if not hasattr(self.main_window, 'particle_system'):
            self.previous_capex = current_capex
            # Update main_window's previous_capex for compatibility
            self.main_window.previous_capex = current_capex
            return
        
        # Calculate how many $1,000,000 increments we've crossed
        previous_millions = int(self.previous_capex / 1000000)
        current_millions = int(current_capex / 1000000)
        
        if current_millions != previous_millions:
            # We've crossed at least one $1,000,000 milestone
            # Calculate the direction (positive or negative change)
            is_positive = current_capex > self.previous_capex
            
            # Get the position of the CAPEX label
            if hasattr(self.main_window, 'capex_label'):
                # Get the location of the capex label for particle origin
                label_x = self.main_window.capex_label.x() + 50
                label_y = self.main_window.capex_label.y()  # top
                
                # Calculate number of particles to create (one for each million crossed)
                num_particles = abs(current_millions - previous_millions)
                
                # Create a popup for each $1,000,000 increment
                for _ in range(num_particles):
                    if is_positive:
                        self.main_window.particle_system.create_capex_popup(label_x, label_y, 1000000, is_positive=True)
                    else:
                        self.main_window.particle_system.create_capex_popup(label_x, label_y, 1000000, is_positive=False)
        
        # Store current CAPEX for next check
        self.previous_capex = current_capex
        # Update main_window's previous_capex for compatibility
        self.main_window.previous_capex = current_capex 