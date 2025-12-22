import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

def generate_mock_data(n_samples=2000):
    data = []
    
    # Base configuration: Friday (4) and Saturday (5) are peak nights
    peak_days = [4, 5] 
    peak_hours = [22, 23, 0, 1, 2] # 10 PM to 2 AM
    
    for _ in range(n_samples):
        # Features
        hour = random.randint(0, 23)
        day_of_week = random.randint(0, 6) # 0=Monday, 6=Sunday
        inventory_level = random.uniform(0, 1) # 0 to 100% capacity
        bartender_load = random.uniform(0.1, 1.0) # Simulated staff workload
        
        # Target Multiplier Calculation (Logic the ML should learn)
        multiplier = 1.0
        
        # Time-based surge
        if day_of_week in peak_days and hour in peak_hours:
            multiplier += 0.15
        elif hour in peak_hours:
            multiplier += 0.05
            
        # Inventory-based surge
        if inventory_level < 0.2:
            multiplier += 0.10
        elif inventory_level < 0.1:
            multiplier += 0.20
            
        # Workload-based surge (to slow down orders)
        if bartender_load > 0.8:
            multiplier += 0.05
            
        # Add some noise
        multiplier += random.uniform(-0.02, 0.02)
        
        # Guardrails (PRD: Max surge +20% / Max discount -15%, but we'll let ML learn the range)
        multiplier = max(0.85, min(1.20, multiplier))
        
        data.append({
            'hour': hour,
            'day_of_week': day_of_week,
            'inventory_level': inventory_level,
            'bartender_load': bartender_load,
            'target_multiplier': multiplier
        })
        
    df = pd.DataFrame(data)
    
    os.makedirs('data', exist_ok=True)
    df.to_csv('data/historical_pricing.csv', index=False)
    print(f"Generated {n_samples} samples in data/historical_pricing.csv")

if __name__ == "__main__":
    generate_mock_data()
