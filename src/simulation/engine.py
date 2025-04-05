from PyQt5.QtCore import QObject, pyqtSignal
from src.components.generator import GeneratorComponent
from src.components.load import LoadComponent
from src.components.bus import BusComponent
from src.components.battery import BatteryComponent
from src.components.grid_import import GridImportComponent
from src.components.grid_export import GridExportComponent
from src.components.cloud_workload import CloudWorkloadComponent
from src.components.solar_panel import SolarPanelComponent
from src.components.wind_turbine import WindTurbineComponent

class SimulationEngine(QObject):
    """
    SimulationEngine handles all simulation calculations while maintaining
    exact compatibility with the existing UI and component system.
    """
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window  # Keep reference to access scene and components
        
        # Mirror all simulation state variables
        self.current_time_step = 0
        self.simulation_running = False
        self.updating_simulation = False
        self.is_scrubbing = False
        self.system_stable = True
        self.fractional_step = 0
        self.last_time_step = 0
        self.total_energy_imported = 0
        self.total_energy_exported = 0
        
        # Add a stability tolerance to ignore tiny imbalances from rounding errors
        self.stability_tolerance = 0.1  # kW - imbalances smaller than this will not trigger instability
        
        # Add array to track gross revenue
        self.gross_revenue_data = [0.0] * 8761  # Initialize with 8761 entries (0-8760 hours)
        
        # Create Historian data object to record simulation history
        self.historian = {
            'total_generation': [0.0] * 8761,  # Initialize with 8761 entries (0-8760 hours)
            'total_load': [0.0] * 8761  # Add total_load tracking to historian
        }
        
    def reset_historian(self):
        """Reset all data arrays within the historian object."""
        for key in self.historian:
            # Assuming all historian data are lists of numbers initialized to 0.0
            if isinstance(self.historian[key], list):
                # Re-initialize the list with zeros
                self.historian[key] = [0.0] * len(self.historian[key])
        print("Historian data reset.")
        
    def step_simulation(self, steps):
        # Check network connectivity before stepping
        if not self.simulation_running and not self.main_window.check_network_connectivity():
            return False
            
        # UPDATED -- Keep this at 1 step per update to preserve fidelity, do not modify based on speed factor, do not revert to old logic that multiplied steps by speed factor 
        steps = 1
        
        # Process the current time step first, then increment for the next step
        # (Don't increment when checking return value; just return success)
        
        # Make sure current_time_step is clamped to valid range
        if self.current_time_step < 0:
            self.current_time_step = 0
        elif self.current_time_step > self.main_window.time_slider.maximum():
            self.current_time_step = self.main_window.time_slider.maximum()
            
        # After processing current step, increment for next iteration
        self.current_time_step += steps
        
        # Keep step in bounds after increment too
        if self.current_time_step > self.main_window.time_slider.maximum():
            self.current_time_step = self.main_window.time_slider.maximum()
        
        return True
        
    def update_simulation(self, skip_ui_updates=False):
        # Guard against recursive calls
        if self.updating_simulation:
            return
            
        self.updating_simulation = True
        
        try:
            current_time = self.current_time_step
            
            # Skip updates during scrubbing
            if self.is_scrubbing:
                return
            
            # Validate bus states before simulation
            self.main_window.validate_bus_states()
            
            # Reset stability flag for this update
            self.system_stable = True
            
            # Initialize calculation variables exactly as before
            total_load = 0
            local_generation = 0
            battery_power = 0
            grid_import = 0
            grid_export = 0
            total_capacity = 0
            active_batteries = []
            total_battery_charge = 0
            
            # First pass: calculate total load, generator capacity, and find batteries
            for item in self.main_window.scene.items():
                if isinstance(item, LoadComponent):
                    total_load += item.calculate_demand(current_time)
                elif isinstance(item, GeneratorComponent):
                    total_capacity += item.capacity
                elif isinstance(item, SolarPanelComponent) and item.operating_mode == "Powerlandia 8760 - Midwest 1":
                    total_capacity += item.capacity
                elif isinstance(item, WindTurbineComponent) and item.operating_mode == "Powerlandia 8760 - Midwest 1":
                    total_capacity += item.capacity
                elif isinstance(item, BatteryComponent):
                    total_battery_charge += item.current_charge / 1000.0
                    if item.operating_mode == "BTF Basic Unit (Auto)":
                        active_batteries.append(item)
            
            # Second pass: calculate local generation first (priority)
            remaining_load = total_load
            
            # Start with Solar Panel and Wind Turbine generation - highest priority
            for item in self.main_window.scene.items():
                if (isinstance(item, SolarPanelComponent) or isinstance(item, WindTurbineComponent)) and item.operating_mode == "Powerlandia 8760 - Midwest 1":
                    output = item.calculate_output(remaining_load)
                    local_generation += output
                    remaining_load = max(0, remaining_load - output)
            
            # Then get generation from all Static (Auto) generators
            for item in self.main_window.scene.items():
                if isinstance(item, GeneratorComponent) and item.operating_mode == "Static (Auto)":
                    output = item.calculate_output(remaining_load)
                    local_generation += output
                    remaining_load = max(0, remaining_load - output)
            
            # Next get generation from BTF Unit Commitment (Auto) generators
            for item in self.main_window.scene.items():
                if isinstance(item, GeneratorComponent) and item.operating_mode == "BTF Unit Commitment (Auto)":
                    # Only pass the remaining load to each generator
                    # This ensures generators don't all try to satisfy the full load
                    output = item.calculate_output(remaining_load)
                    local_generation += output
                    remaining_load = max(0, remaining_load - output)
            
            # Last, get generation from BTF Droop (Auto) generators, sharing load equally
            droop_generators = [item for item in self.main_window.scene.items() 
                              if isinstance(item, GeneratorComponent) and 
                              item.operating_mode == "BTF Droop (Auto)"]
            
            if droop_generators:
                if remaining_load > 0:
                    # Calculate total capacity of all droop generators
                    total_droop_capacity = sum(gen.capacity for gen in droop_generators)
                    
                    if total_droop_capacity > 0:
                        # Determine equal percentage for all droop generators
                        # Cap at 100% - we don't want to exceed their capacity
                        droop_percentage = min(1.0, remaining_load / total_droop_capacity)
                        
                        # Apply the same percentage to all droop generators
                        for gen in droop_generators:
                            # Calculate target output based on equal percentage
                            target_output = gen.capacity * droop_percentage
                            
                            # Apply ramp rate limiting if needed
                            if gen.ramp_rate_enabled and gen.last_output > 0:
                                max_change = gen.capacity * gen.ramp_rate_limit
                                if target_output > gen.last_output:
                                    # Ramping up
                                    actual_output = min(target_output, gen.last_output + max_change)
                                else:
                                    # Ramping down
                                    actual_output = max(target_output, gen.last_output - max_change)
                            else:
                                actual_output = target_output
                            
                            # Update last_output for the generator
                            gen.last_output = actual_output
                            
                            # Add to local generation and reduce remaining load
                            local_generation += actual_output
                            remaining_load = max(0, remaining_load - actual_output)
                else:
                    # No remaining load, set all droop generators to 0 output
                    for gen in droop_generators:
                        # If ramp rate limiting is enabled, respect it when ramping down
                        if gen.ramp_rate_enabled and gen.last_output > 0:
                            max_change = gen.capacity * gen.ramp_rate_limit
                            gen.last_output = max(0, gen.last_output - max_change)
                        else:
                            gen.last_output = 0
            
            # Third pass: if there's still remaining load, use battery discharge (second priority)
            if remaining_load > 0 and active_batteries:
                time_step = 1.0  # Calculate time step in hours (assume 1 hour per time step)
                
                for battery in active_batteries:
                    if not battery.has_energy():
                        continue
                        
                    energy_needed = remaining_load * time_step
                    discharged = battery.discharge(energy_needed, time_step)
                    power_discharged = discharged / time_step
                    
                    battery_power += power_discharged
                    remaining_load = max(0, remaining_load - power_discharged)
                    battery.update()
                    
                    if remaining_load <= 0:
                        break
            
            # Fourth pass: if there's still remaining load, use grid import (third priority)
            if remaining_load > 0:
                for item in self.main_window.scene.items():
                    if isinstance(item, GridImportComponent):
                        import_amount = item.calculate_output(remaining_load)
                        grid_import += import_amount
                        remaining_load = max(0, remaining_load - import_amount)
                
                # Only mark as unstable if remaining load exceeds the tolerance
                if remaining_load > self.stability_tolerance:
                    self.system_stable = False
            
            # Fifth pass: check for surplus power to charge batteries -- this should include solar and renewables as they are added too
            surplus_power = (local_generation + grid_import) - total_load
            
            if surplus_power > 0 and active_batteries:
                time_step = 1.0
                remaining_surplus = surplus_power
                
                for battery in active_batteries:
                    if not battery.has_capacity():
                        continue
                        
                    energy_available = remaining_surplus * time_step
                    charged = battery.charge(energy_available, time_step)
                    power_charged = charged / time_step
                    
                    battery_power -= power_charged
                    remaining_surplus = max(0, remaining_surplus - power_charged)
                    battery.update()
                    
                    if remaining_surplus <= 0:
                        break
                    
                surplus_power = remaining_surplus
            
            # Sixth Pass: If batteries still have capacity, try to use local generation to charge them -- the batteries WILL spin up generators with auto-charging enabled to get power
            if active_batteries and any(battery.has_capacity() for battery in active_batteries):
                unused_gen_capacity = 0
                for item in self.main_window.scene.items():
                    if isinstance(item, GeneratorComponent) and item.auto_charging:
                        unused_gen_capacity += (item.capacity - item.last_output)
                
                if unused_gen_capacity > 0:
                    time_step = 1.0
                    remaining_capacity = unused_gen_capacity
                    
                    for battery in active_batteries:
                        if not battery.has_capacity():
                            continue
                            
                        energy_available = remaining_capacity * time_step
                        charged = battery.charge(energy_available, time_step)
                        power_charged = charged / time_step
                        
                        local_generation += power_charged
                        battery_power -= power_charged
                        remaining_capacity = max(0, remaining_capacity - power_charged)
                        
                        battery.update()
            
            # Seventh Pass: If batteries still have capacity and we have grid import, use it to charge batteries
            if active_batteries and any(battery.has_capacity() for battery in active_batteries):
                # Get grid import components that allow battery charging
                grid_import_components = [item for item in self.main_window.scene.items() 
                                         if isinstance(item, GridImportComponent) and item.auto_charge_batteries]
                
                have_grid_import = len(grid_import_components) > 0
                
                if have_grid_import:
                    max_import_capacity = 0
                    for item in grid_import_components:
                        max_import_capacity += item.capacity
                    
                    remaining_import_capacity = max(0, max_import_capacity - grid_import)
                    
                    if remaining_import_capacity > 0:
                        time_step = 1.0
                        
                        for battery in active_batteries:
                            if not battery.has_capacity():
                                continue
                                
                            energy_available = remaining_import_capacity * time_step
                            charged = battery.charge(energy_available, time_step)
                            power_charged = charged / time_step
                            
                            additional_grid_import = power_charged
                            grid_import += additional_grid_import
                            battery_power -= power_charged
                            remaining_import_capacity = max(0, remaining_import_capacity - power_charged)
                            
                            battery.update()
            
            # Eighth Pass: if there's still surplus power, use grid export
            if surplus_power > 0:
                for item in self.main_window.scene.items():
                    if isinstance(item, GridExportComponent):
                        export_amount = item.calculate_export(surplus_power)
                        grid_export += export_amount
                        surplus_power = max(0, surplus_power - export_amount)
                
                # Only mark as unstable if surplus power exceeds the tolerance
                if surplus_power > self.stability_tolerance:
                    self.system_stable = False
            
            # Update energy accounting if not in scrub mode 
            if not self.is_scrubbing and current_time != self.last_time_step:
                if current_time > self.last_time_step or current_time == 0:
                    steps_moved = 1 if current_time == 0 else current_time - self.last_time_step
                    self.total_energy_imported += grid_import * steps_moved
                    self.total_energy_exported += grid_export * steps_moved
                    
                    # Calculate revenue for each load component based on energy consumption
                    current_hourly_revenue = 0.0
                    
                    # Calculate the actual percentage of load satisfied
                    # If there's remaining_load > tolerance, then some load wasn't satisfied
                    load_satisfaction_ratio = 1.0
                    if not self.system_stable and remaining_load > self.stability_tolerance:
                        # Calculate what percentage of the total load was actually met
                        met_load = total_load - remaining_load
                        load_satisfaction_ratio = met_load / total_load if total_load > 0 else 0.0
                    
                    # Calculate revenue from loads
                    load_components = []
                    for item in self.main_window.scene.items():
                        if isinstance(item, LoadComponent):
                            # Get energy consumption in kWh for this time step
                            energy_demanded = item.calculate_demand(current_time) * steps_moved
                            
                            # Apply the load satisfaction ratio to determine actual energy consumed
                            energy_consumed = energy_demanded * load_satisfaction_ratio
                            
                            # Calculate revenue based on price per kWh
                            revenue = energy_consumed * item.price_per_kwh
                            # Add to accumulated revenue
                            item.accumulated_revenue += revenue
                            # Add to current hour's gross revenue
                            current_hourly_revenue += revenue
                            
                            # Store for cloud workload calculations
                            if item.profile_type == "Data Center":
                                load_components.append((item, energy_consumed))
                    
                    # Calculate revenue from cloud workloads
                    cloud_workload_components = [item for item in self.main_window.scene.items() 
                                                if isinstance(item, CloudWorkloadComponent) and 
                                                item.operating_mode == "Multi-Cloud Spot"]
                    
                    for cloud_workload in cloud_workload_components:
                        cloud_revenue = 0.0
                        
                        # Calculate revenue for each relevant load
                        for load_component, energy_consumed in load_components:
                            # Calculate revenue based on load type and energy consumed
                            load_revenue = cloud_workload.calculate_cloud_revenue(load_component, energy_consumed)
                            cloud_revenue += load_revenue
                        
                        # Add to accumulated revenue for this cloud workload
                        cloud_workload.accumulated_revenue += cloud_revenue
                        # Add to current hour's gross revenue
                        current_hourly_revenue += cloud_revenue
                    
                    # Calculate revenue from exports
                    for item in self.main_window.scene.items():
                        if isinstance(item, GridExportComponent) and item.bulk_ppa_price > 0:
                            # Calculate the export revenue for this time step
                            export_energy = item.calculate_export(grid_export) * steps_moved  # kWh exported
                            export_revenue = export_energy * item.bulk_ppa_price
                            
                            # Add to accumulated revenue for this export component
                            item.accumulated_revenue += export_revenue
                            # Add to current hour's gross revenue
                            current_hourly_revenue += export_revenue
                    
                    # Store the hourly gross revenue
                    for hour in range(self.last_time_step, current_time):
                        if 0 <= hour < len(self.gross_revenue_data):
                            # Distribute revenue evenly across all hours if we jumped multiple steps
                            self.gross_revenue_data[hour] = current_hourly_revenue / steps_moved
                
                self.last_time_step = current_time
            
            # Calculate final values
            unused_capacity = total_capacity - local_generation
            
            # Recalculate total battery charge
            total_battery_charge = 0
            for item in self.main_window.scene.items():
                if isinstance(item, BatteryComponent):
                    total_battery_charge += item.current_charge / 1000.0
            
            # Calculate total generation including battery discharge
            total_generation = local_generation + max(0, battery_power)
            
            # Record total generation in Historian
            if 0 <= current_time < len(self.historian['total_generation']):
                self.historian['total_generation'][current_time] = total_generation
                self.historian['total_load'][current_time] = total_load  # Record total load in historian
            
            # Update analytics with all values (conditionally)
            if not skip_ui_updates:
                self.main_window.analytics_panel.update_analytics(
                    total_generation,
                    total_load,
                    current_time,
                    total_capacity,
                    is_scrubbing=False,
                    grid_import=grid_import,
                    grid_export=grid_export,
                    total_imported=self.total_energy_imported,
                    total_exported=self.total_energy_exported,
                    system_stable=self.system_stable,
                    battery_power=battery_power,
                    total_battery_charge=total_battery_charge,
                    gross_revenue_data=self.gross_revenue_data
                )
            
            # Update all load components to refresh their visual display with current demand percentage (conditionally)
            if not skip_ui_updates:
                for item in self.main_window.scene.items():
                    if isinstance(item, LoadComponent):
                        item.update()
                    elif isinstance(item, GeneratorComponent):
                        item.update()
                    elif isinstance(item, CloudWorkloadComponent):
                        item.update()
            
            # Update historian chart if in historian view (conditionally)
            if not skip_ui_updates and hasattr(self.main_window, 'is_model_view') and not self.main_window.is_model_view:
                self.main_window.historian_manager.update_chart()
            
            # Move to next time step if auto-playing
            if self.simulation_running:
                next_time = current_time + 1
                if next_time > self.main_window.time_slider.maximum():
                    # Stop the simulation when we reach the end
                    self.simulation_running = False
                    # The main window will handle updating UI elements
                else:
                    self.main_window.time_slider.setValue(self.current_time_step)
        
        finally:
            self.updating_simulation = False 