from pyxirr import xirr
import numpy as np
from datetime import datetime, timedelta

def calculate_irr(capex, hourly_revenue, hourly_cost, current_hour):
    """
    Calculate the internal rate of return (IRR) for the system based on CAPEX and hourly net revenue.
    
    Args:
        capex: Total capital expenditure (negative value)
        hourly_revenue: List of hourly revenue values
        hourly_cost: List of hourly cost values
        current_hour: Current hour in the simulation
        
    Returns:
        IRR as a decimal (e.g., 0.1482 for 14.82%) or None if IRR cannot be calculated
    """
    if current_hour <= 0:
        return None
        
    # Create cash flows: CAPEX at hour 0, followed by hourly net revenue
    cash_flows = [-capex]  # CAPEX is a negative cash flow at hour 0
    
    # Calculate net revenue (revenue - cost) for each hour
    for i in range(min(current_hour, len(hourly_revenue), len(hourly_cost))):
        net_revenue = hourly_revenue[i] - hourly_cost[i]
        cash_flows.append(net_revenue)
    
    # Create dates: starting from now, with hourly intervals
    start_date = datetime.now()
    dates = [start_date]
    
    for i in range(len(cash_flows) - 1):  # -1 because we already have the CAPEX at hour 0
        dates.append(start_date + timedelta(hours=i+1))
    
    # Check if we have enough data and non-zero cash flows beyond CAPEX
    if len(cash_flows) <= 1 or all(cf == 0 for cf in cash_flows[1:]):
        return None
    
    try:
        # Calculate the IRR using pyxirr
        irr = xirr(dates, cash_flows)
        return irr
    except Exception as e:
        print(f"Error calculating IRR: {e}")
        return None

def calculate_extended_irr(capex, hourly_revenue, hourly_cost, current_hour):
    """
    Calculate IRR for 12, 18, and 36 months using real data for the first year
    and synthetic data based on average hourly net revenue for extended periods.
    
    Args:
        capex: Total capital expenditure (negative value)
        hourly_revenue: List of hourly revenue values
        hourly_cost: List of hourly cost values
        current_hour: Current hour in the simulation
        
    Returns:
        Dictionary of IRR values for 12, 18, and 36 months
        e.g., {12: 0.1482, 18: 0.1763, 36: 0.2059}
    """
    # Calculate 12-month IRR using the original function
    irr_12_month = calculate_irr(capex, hourly_revenue, hourly_cost, current_hour)
    
    # Initialize results dictionary
    results = {12: irr_12_month, 18: None, 36: None}
    
    # Calculate average net revenue per hour based on available data
    total_net_revenue = 0
    count = min(current_hour, len(hourly_revenue), len(hourly_cost))
    
    if count > 0:
        for i in range(count):
            net_revenue = hourly_revenue[i] - hourly_cost[i]
            total_net_revenue += net_revenue
        
        avg_hourly_net_revenue = total_net_revenue / count
        
        # Calculate extended IRRs for 18 and 36 months
        for months in [18, 36]:
            # Calculate total hours for this period
            total_hours = months * 730  # Approximately 730 hours per month
            
            # Create cash flows: CAPEX at hour 0, followed by real data, then synthetic data
            cash_flows = [-capex]
            
            # Add actual data for available period
            for i in range(count):
                net_revenue = hourly_revenue[i] - hourly_cost[i]
                cash_flows.append(net_revenue)
            
            # Add synthetic data based on average for remaining period
            synthetic_hours = total_hours - count
            for _ in range(synthetic_hours):
                cash_flows.append(avg_hourly_net_revenue)
            
            # Create dates
            start_date = datetime.now()
            dates = [start_date]
            
            for i in range(len(cash_flows) - 1):
                dates.append(start_date + timedelta(hours=i+1))
            
            try:
                # Calculate IRR for extended period
                irr = xirr(dates, cash_flows)
                results[months] = irr
            except Exception as e:
                print(f"Error calculating {months}-month IRR: {e}")
                results[months] = None
    
    return results 