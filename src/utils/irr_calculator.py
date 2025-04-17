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