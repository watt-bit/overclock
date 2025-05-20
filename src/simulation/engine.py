from PyQt5.QtCore import QObject
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
        
        # Add array to track gross cost
        self.gross_cost_data = [0.0] * 8761  # Initialize with 8761 entries (0-8760 hours)
        
        # Create Historian data object to record simulation history
        self.historian = {
            'total_generation': [0.0] * 8761,  # Initialize with 8761 entries (0-8760 hours)
            'total_load': [0.0] * 8761,  # Add total_load tracking to historian
            'grid_import': [0.0] * 8761,  # Add grid_import tracking to historian
            'grid_export': [0.0] * 8761,   # Add grid_export tracking to historian
            'cumulative_revenue': [0.0] * 8761,  # Add cumulative revenue tracking to historian
            'cumulative_cost': [0.0] * 8761,  # Add cumulative cost tracking to historian
            'battery_charge': [0.0] * 8761,  # Add battery charge tracking to historian
            'system_instability': [0.0] * 8761,  # Add system instability tracking to historian
            'satisfied_load': [0.0] * 8761   # Add satisfied load tracking to historian
        }
        
        # The component-specific historian entries will be added dynamically
        # as components are encountered during simulation
        
    def reset_historian(self):
        """Reset all data arrays within the historian object."""
        for key in self.historian:
            # Assuming all historian data are lists of numbers initialized to 0.0
            if isinstance(self.historian[key], list):
                # Re-initialize the list with zeros
                self.historian[key] = [0.0] * len(self.historian[key])
        print("Historian data reset.")
        
    def remove_component_historian_keys(self, component):
        """
        Remove historian keys associated with a deleted component.
        
        Args:
            component: The component being deleted
        """
        # Get component type and unique ID
        component_id = str(id(component))[-6:]  # Use last 6 digits of the ID
        
        # Determine the keys to remove based on component type
        keys_to_remove = []
        
        from src.components.generator import GeneratorComponent
        from src.components.load import LoadComponent
        from src.components.solar_panel import SolarPanelComponent
        from src.components.wind_turbine import WindTurbineComponent
        from src.components.grid_import import GridImportComponent
        from src.components.grid_export import GridExportComponent
        from src.components.cloud_workload import CloudWorkloadComponent
        
        # Check generation data
        if isinstance(component, GeneratorComponent):
            keys_to_remove.append(f"Generator_{component_id}")
            keys_to_remove.append(f"Cost_Gen_{component_id}")
        elif isinstance(component, SolarPanelComponent):
            keys_to_remove.append(f"Solar_{component_id}")
        elif isinstance(component, WindTurbineComponent):
            keys_to_remove.append(f"Wind_{component_id}")
        
        # Check load data
        elif isinstance(component, LoadComponent):
            keys_to_remove.append(f"Load_{component_id}")
            keys_to_remove.append(f"Rev_Load_{component_id}")
        
        # Check grid components
        elif isinstance(component, GridImportComponent):
            keys_to_remove.append(f"Cost_Import_{component_id}")
        elif isinstance(component, GridExportComponent):
            keys_to_remove.append(f"Rev_Export_{component_id}")
        
        # Check cloud workload
        elif isinstance(component, CloudWorkloadComponent):
            keys_to_remove.append(f"Rev_Cloud_{component_id}")
        
        # Remove the identified keys from the historian
        for key in keys_to_remove:
            if key in self.historian:
                del self.historian[key]
                
        # If we're in historian view, update the chart to reflect the changes
        if hasattr(self.main_window, 'is_model_view') and not self.main_window.is_model_view:
            self.main_window.historian_manager.update_chart()
        
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
            
            # Initialize load_satisfaction_ratio with default value
            load_satisfaction_ratio = 1.0
            
            # Reset all grid component indicators to zero at the beginning of each step
            for item in self.main_window.scene.items():
                if isinstance(item, GridImportComponent):
                    item.last_import = 0
                elif isinstance(item, GridExportComponent):
                    item.last_export = 0
            
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
                elif isinstance(item, SolarPanelComponent) and (item.operating_mode == "Powerlandia 8760 - Midwest 1" or item.operating_mode == "Custom"):
                    total_capacity += item.capacity
                elif isinstance(item, WindTurbineComponent) and (item.operating_mode == "Powerlandia 8760 - Midwest 1" or item.operating_mode == "Custom"):
                    total_capacity += item.capacity
                elif isinstance(item, BatteryComponent):
                    total_battery_charge += item.current_charge / 1000.0
                    if item.operating_mode == "BTF Basic Unit (Auto)":
                        active_batteries.append(item)
            
            # Second pass: calculate local generation first (priority)
            remaining_load = total_load
            
            # Track individual component outputs in this time step
            component_outputs = {}
            
            # Start with Solar Panel and Wind Turbine generation - highest priority
            for item in self.main_window.scene.items():
                if isinstance(item, SolarPanelComponent) and (item.operating_mode == "Powerlandia 8760 - Midwest 1" or item.operating_mode == "Custom"):
                    output = item.calculate_output(remaining_load)
                    local_generation += output
                    remaining_load = max(0, remaining_load - output)
                    
                    # Track individual component output
                    component_outputs[item] = output
                    
                elif isinstance(item, WindTurbineComponent) and (item.operating_mode == "Powerlandia 8760 - Midwest 1" or item.operating_mode == "Custom"):
                    output = item.calculate_output(remaining_load)
                    local_generation += output
                    remaining_load = max(0, remaining_load - output)
                    
                    # Track individual component output
                    component_outputs[item] = output
            
            # Then get generation from all Static (Auto) generators
            for item in self.main_window.scene.items():
                if isinstance(item, GeneratorComponent) and item.operating_mode == "Static (Auto)":
                    output = item.calculate_output(remaining_load)
                    local_generation += output
                    remaining_load = max(0, remaining_load - output)
                    
                    # Track individual component output
                    component_outputs[item] = output
            
            # Next get generation from BTF Unit Commitment (Auto) generators
            # Get all BTF Unit Commitment generators and sort by cost_per_gj in ascending order (lowest cost first)
            unit_commitment_generators = [item for item in self.main_window.scene.items() 
                                         if isinstance(item, GeneratorComponent) and 
                                         item.operating_mode == "BTF Unit Commitment (Auto)"]
            
            # Sort generators by cost_per_gj (lowest cost first)
            unit_commitment_generators.sort(key=lambda x: x.cost_per_gj)
            
            # Process generators in order of increasing cost
            for item in unit_commitment_generators:
                # Only pass the remaining load to each generator
                # This ensures generators don't all try to satisfy the full load
                output = item.calculate_output(remaining_load)
                local_generation += output
                remaining_load = max(0, remaining_load - output)
                
                # Track individual component output
                component_outputs[item] = output
            
            # Last, get generation from BTF Droop (Auto) generators, sharing load equally
            droop_generators = [item for item in self.main_window.scene.items() 
                              if isinstance(item, GeneratorComponent) and 
                              item.operating_mode == "BTF Droop (Auto)"]
            
            if droop_generators:
                # First, update the maintenance status for all droop generators
                for gen in droop_generators:
                    if hasattr(gen, '_update_maintenance_status'):
                        gen._update_maintenance_status()
                
                # Filter out generators that are in maintenance
                available_droop_generators = [gen for gen in droop_generators 
                                            if not (hasattr(gen, 'is_in_maintenance') and gen.is_in_maintenance)]
                
                # Process generators in maintenance to set outputs to 0
                for gen in droop_generators:
                    if hasattr(gen, 'is_in_maintenance') and gen.is_in_maintenance:
                        gen.last_output = 0
                        component_outputs[gen] = 0
                
                if remaining_load > 0 and available_droop_generators:
                    # Calculate total capacity of available droop generators (excluding those in maintenance)
                    total_droop_capacity = sum(gen.capacity for gen in available_droop_generators)
                    
                    if total_droop_capacity > 0:
                        # Determine equal percentage for all available droop generators
                        # Cap at 100% - we don't want to exceed their capacity
                        droop_percentage = min(1.0, remaining_load / total_droop_capacity)
                        
                        # Apply the same percentage to all available droop generators
                        for gen in available_droop_generators:
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
                            
                            # Track individual component output
                            component_outputs[gen] = actual_output
                            
                            # Update operating hours for this droop generator if it's producing power
                            if actual_output > 0:
                                gen.total_operating_hours += 1
                else:
                    # No remaining load or no available generators, set all droop generators to 0 output
                    for gen in available_droop_generators:
                        # If ramp rate limiting is enabled, respect it when ramping down
                        if gen.ramp_rate_enabled and gen.last_output > 0:
                            max_change = gen.capacity * gen.ramp_rate_limit
                            gen.last_output = max(0, gen.last_output - max_change)
                        else:
                            gen.last_output = 0
                        
                        # Track individual component output (even if zero)
                        component_outputs[gen] = gen.last_output
            
            # Track individual load component demands
            component_demands = {}
            
            # Calculate demand for each load component
            for item in self.main_window.scene.items():
                if isinstance(item, LoadComponent):
                    demand = item.calculate_demand(current_time)
                    component_demands[item] = demand
            
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
            # Initialize component_imports dictionary
            component_imports = {}
            
            if remaining_load > 0:
                # Get all GridImportComponent instances and sort by cost_per_kwh in ascending order
                grid_import_components = [item for item in self.main_window.scene.items() 
                                          if isinstance(item, GridImportComponent)]
                
                # Sort by cost_per_kwh in ascending order (lowest cost first)
                grid_import_components.sort(key=lambda x: x.cost_per_kwh)
                
                for item in grid_import_components:
                    import_amount = item.calculate_output(remaining_load)
                    grid_import += import_amount
                    remaining_load = max(0, remaining_load - import_amount)
                    
                    # Store this component's import amount
                    component_imports[item] = import_amount
                
                # Only mark as unstable if remaining load exceeds the tolerance
                if remaining_load > self.stability_tolerance:
                    self.system_stable = False
            
            # Calculate load satisfaction ratio based on actual remaining load,
            # regardless of system stability status
            if remaining_load > self.stability_tolerance and total_load > 0:
                # Calculate what percentage of the total load was actually met
                met_load = total_load - remaining_load
                load_satisfaction_ratio = met_load / total_load
            else:
                # If remaining load is within tolerance or total_load is zero, all load is satisfied
                load_satisfaction_ratio = 1.0
            
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
                    if isinstance(item, GeneratorComponent) and item.auto_charging and not item.is_in_maintenance:
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
                            
                            # Update component imports for cost calculation
                            for item in grid_import_components:
                                component_share = item.capacity / max_import_capacity
                                component_imports[item] = component_imports.get(item, 0) + (additional_grid_import * component_share)
                            
                            battery.update()
            
            # Eighth Pass: if there's still surplus power, use grid export
            # Initialize component_exports dictionary regardless of surplus power
            component_exports = {}
            
            if surplus_power > 0:
                # Get all GridExportComponent instances and sort by bulk_ppa_price in descending order
                grid_export_components = [item for item in self.main_window.scene.items() 
                                          if isinstance(item, GridExportComponent)]
                
                # Sort by bulk_ppa_price in descending order (highest price first)
                grid_export_components.sort(key=lambda x: x.bulk_ppa_price, reverse=True)
                
                for item in grid_export_components:
                    export_amount = item.calculate_export(surplus_power)
                    grid_export += export_amount
                    surplus_power = max(0, surplus_power - export_amount)
                    
                    # Store this component's export amount
                    component_exports[item] = export_amount
                
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
                    current_hourly_cost = 0.0
                    
                    # Calculate the actual percentage of load satisfied
                    # If there's remaining_load > tolerance, then some load wasn't satisfied
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
                                                (item.operating_mode == "Multi-Cloud Spot" or
                                                 item.operating_mode == "Dedicated Capacity")]
                    
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
                        if isinstance(item, GridExportComponent) and (item.bulk_ppa_price > 0 or item.market_prices_mode != "None"):
                            # Get this component's specific export amount rather than the total grid_export
                            component_export = component_exports.get(item, 0)
                            
                            # Calculate the export revenue for this time step
                            export_energy = component_export * steps_moved  # kWh exported
                            
                            # Check if market prices are being used
                            market_price = 0.00
                            if item.market_prices_mode != "None":
                                # Get current market price based on the current time step
                                market_price = item.get_current_market_price(current_time)
                            
                            # Total price is the sum of bulk PPA price and market price (if any)
                            total_price = item.bulk_ppa_price + market_price
                            
                            # Calculate revenue using the total price
                            export_revenue = export_energy * total_price
                            
                            # Add to accumulated revenue for this export component
                            item.accumulated_revenue += export_revenue
                            # Add to current hour's gross revenue
                            current_hourly_revenue += export_revenue
                    
                    # Calculate cost of gas for generators
                    for item in self.main_window.scene.items():
                        if isinstance(item, GeneratorComponent) and item.last_output > 0:
                            # Calculate energy generated in kWh
                            energy_generated = item.last_output * steps_moved
                            
                            # Calculate gas consumption in GJ
                            gas_consumption = item.calculate_gas_consumption(energy_generated)
                            
                            # Calculate gas cost
                            gas_cost = item.calculate_gas_cost(gas_consumption)
                            
                            # Add to accumulated cost for this generator
                            item.accumulated_cost += gas_cost
                            
                            # Add to current hour's gross cost
                            current_hourly_cost += gas_cost
                    
                    # Calculate cost from imports
                    for item in self.main_window.scene.items():
                        if isinstance(item, GridImportComponent) and (item.cost_per_kwh > 0 or item.market_prices_mode != "None"):
                            # Get this component's specific import amount
                            component_import = component_imports.get(item, 0)
                            
                            # Calculate the import cost for this time step
                            import_energy = component_import * steps_moved  # kWh imported
                            
                            # Check if market prices are being used
                            market_price = 0.00
                            if item.market_prices_mode != "None":
                                # Get current market price based on the current time step
                                market_price = item.get_current_market_price(current_time)
                            
                            # Total price is the sum of bulk PPA price and market price (if any)
                            total_price = item.cost_per_kwh + market_price
                            
                            # Calculate cost using the total price
                            import_cost = import_energy * total_price
                            
                            # Add to accumulated cost for this import component
                            item.accumulated_cost += import_cost
                            # Add to current hour's gross cost
                            current_hourly_cost += import_cost
                    
                    # Store the hourly gross revenue and cost
                    for hour in range(self.last_time_step, current_time):
                        if 0 <= hour < len(self.gross_revenue_data):
                            # Distribute revenue evenly across all hours if we jumped multiple steps
                            hourly_revenue = current_hourly_revenue / steps_moved
                            hourly_cost = current_hourly_cost / steps_moved
                            
                            self.gross_revenue_data[hour] = hourly_revenue
                            self.gross_cost_data[hour] = hourly_cost
                            
                            # Update cumulative revenue in historian
                            if hour > 0:
                                self.historian['cumulative_revenue'][hour] = self.historian['cumulative_revenue'][hour-1] + hourly_revenue
                                self.historian['cumulative_cost'][hour] = self.historian['cumulative_cost'][hour-1] + hourly_cost
                            else:
                                self.historian['cumulative_revenue'][hour] = hourly_revenue
                                self.historian['cumulative_cost'][hour] = hourly_cost
                
                self.last_time_step = current_time
            
            # Calculate final values
            unused_capacity = total_capacity - local_generation
            
            # Recalculate total battery charge
            total_battery_charge = 0
            for item in self.main_window.scene.items():
                if isinstance(item, BatteryComponent):
                    total_battery_charge += item.current_charge / 1000.0 # Convert to MWh
            
            # Calculate total generation including battery discharge
            total_generation = local_generation + max(0, battery_power)
            
            # Include battery charging in total_load
            battery_charging = min(0, battery_power)  # Will be negative or zero
            adjusted_total_load = total_load - battery_charging  # Subtract negative value = add to consumption
            
            # Calculate power surplus/deficit
            power_surplus = (total_generation + grid_import - grid_export) - adjusted_total_load
            
            # Record total generation in Historian
            if 0 <= current_time < len(self.historian['total_generation']):
                self.historian['total_generation'][current_time] = total_generation
                self.historian['total_load'][current_time] = adjusted_total_load  # Record adjusted total load in historian
                self.historian['grid_import'][current_time] = grid_import  # Record grid import in historian
                self.historian['grid_export'][current_time] = grid_export  # Record grid export in historian
                self.historian['battery_charge'][current_time] = total_battery_charge * 1000  # Record total battery charge in kWh  
                self.historian['system_instability'][current_time] = abs(power_surplus)  # Record absolute value of power surplus/deficit
                # Record satisfied load based on calculated load_satisfaction_ratio
                self.historian['satisfied_load'][current_time] = total_load * load_satisfaction_ratio  # Record satisfied load in historian
                
                # Record individual component data in the historian
                # For generation components
                for component, output in component_outputs.items():
                    # Create a unique key for this component
                    if isinstance(component, GeneratorComponent):
                        component_type = "Generator"
                    elif isinstance(component, SolarPanelComponent):
                        component_type = "Solar"
                    elif isinstance(component, WindTurbineComponent):
                        component_type = "Wind"
                    else:
                        component_type = "Unknown"
                    
                    # Create a key like "Generator_1" or "Solar_Panel_3"
                    # Include the component ID which is unique
                    component_id = str(id(component))[-6:]  # Use last 6 digits of the ID
                    historian_key = f"{component_type}_{component_id}"
                    
                    # Initialize this component's data array if it doesn't exist
                    if historian_key not in self.historian:
                        self.historian[historian_key] = [0.0] * 8761
                    
                    # Record this component's output for the current time
                    self.historian[historian_key][current_time] = output
                
                # For load components
                for component, demand in component_demands.items():
                    # Create a unique key for this load component
                    component_id = str(id(component))[-6:]  # Use last 6 digits of the ID
                    historian_key = f"Load_{component_id}"
                    
                    # Initialize this component's data array if it doesn't exist
                    if historian_key not in self.historian:
                        self.historian[historian_key] = [0.0] * 8761
                    
                    # Record this component's demand for the current time
                    self.historian[historian_key][current_time] = demand
                
                # Record individual component revenue data in the historian
                # For load components with revenue
                for item in self.main_window.scene.items():
                    if isinstance(item, LoadComponent) and hasattr(item, 'accumulated_revenue'):
                        # Create a unique key for this load component's revenue
                        component_id = str(id(item))[-6:]  # Use last 6 digits of the ID
                        historian_key = f"Rev_Load_{component_id}"
                        
                        # Initialize this component's data array if it doesn't exist
                        if historian_key not in self.historian:
                            self.historian[historian_key] = [0.0] * 8761
                        
                        # Record this component's cumulative revenue for the current time
                        self.historian[historian_key][current_time] = item.accumulated_revenue
                
                # For grid export components with revenue
                for item in self.main_window.scene.items():
                    if isinstance(item, GridExportComponent) and hasattr(item, 'accumulated_revenue'):
                        # Create a unique key for this export component's revenue
                        component_id = str(id(item))[-6:]  # Use last 6 digits of the ID
                        historian_key = f"Rev_Export_{component_id}"
                        
                        # Initialize this component's data array if it doesn't exist
                        if historian_key not in self.historian:
                            self.historian[historian_key] = [0.0] * 8761
                        
                        # Record this component's cumulative revenue for the current time
                        self.historian[historian_key][current_time] = item.accumulated_revenue
                
                # For cloud workload components with revenue
                for item in self.main_window.scene.items():
                    if isinstance(item, CloudWorkloadComponent) and hasattr(item, 'accumulated_revenue'):
                        # Create a unique key for this cloud workload component's revenue
                        component_id = str(id(item))[-6:]  # Use last 6 digits of the ID
                        historian_key = f"Rev_Cloud_{component_id}"
                        
                        # Initialize this component's data array if it doesn't exist
                        if historian_key not in self.historian:
                            self.historian[historian_key] = [0.0] * 8761
                        
                        # Record this component's cumulative revenue for the current time
                        self.historian[historian_key][current_time] = item.accumulated_revenue
                
                # Record individual component cost data in the historian
                # For generator components with cost
                for item in self.main_window.scene.items():
                    if isinstance(item, GeneratorComponent) and hasattr(item, 'accumulated_cost'):
                        # Create a unique key for this generator component's cost
                        component_id = str(id(item))[-6:]  # Use last 6 digits of the ID
                        historian_key = f"Cost_Gen_{component_id}"
                        
                        # Initialize this component's data array if it doesn't exist
                        if historian_key not in self.historian:
                            self.historian[historian_key] = [0.0] * 8761
                        
                        # Record this component's cumulative cost for the current time
                        self.historian[historian_key][current_time] = item.accumulated_cost
                
                # For grid import components with cost
                for item in self.main_window.scene.items():
                    if isinstance(item, GridImportComponent) and hasattr(item, 'accumulated_cost'):
                        # Create a unique key for this import component's cost
                        component_id = str(id(item))[-6:]  # Use last 6 digits of the ID
                        historian_key = f"Cost_Import_{component_id}"
                        
                        # Initialize this component's data array if it doesn't exist
                        if historian_key not in self.historian:
                            self.historian[historian_key] = [0.0] * 8761
                        
                        # Record this component's cumulative cost for the current time
                        self.historian[historian_key][current_time] = item.accumulated_cost
            
            # Update analytics with all values (conditionally)
            if not skip_ui_updates:
                self.main_window.analytics_panel.update_analytics(
                    total_generation,
                    adjusted_total_load,  # Pass the adjusted load including battery charging
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
                    gross_revenue_data=self.gross_revenue_data,
                    gross_cost_data=self.gross_cost_data,
                    power_surplus=power_surplus  # Pass power surplus to analytics panel
                )
            
            # Update all load components to refresh their visual display with current demand percentage (conditionally)
            if not skip_ui_updates:
                for item in self.main_window.scene.items():
                    if isinstance(item, LoadComponent):
                        item.update()
                    elif isinstance(item, GeneratorComponent):
                        item.update()
                        # Trigger smoke emission from generators, but only when simulation is running
                        if self.simulation_running and hasattr(item, 'emit_smoke'):
                            item.emit_smoke()
                    elif isinstance(item, CloudWorkloadComponent):
                        item.update()
                    elif isinstance(item, GridExportComponent):
                        item.update()
                    elif isinstance(item, GridImportComponent):
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