"""
Generate synthetic demand data for Phase 2 training.

This creates historical sales data with realistic patterns:
- Price elasticity (higher price = lower demand)
- Weekend/weekday patterns
- Time-of-day patterns
- Event-based surges
- Inventory effects
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os
from pathlib import Path


def generate_demand_data(
    n_samples: int = 5000,
    venues: List[str] = None,
    output_path: str = 'backend/data/demand_history.csv'
) -> pd.DataFrame:
    """
    Generate synthetic demand/sales history data.
    
    Creates realistic patterns:
    - Price elasticity: demand decreases as price increases
    - Weekend effect: 2-3x demand on Friday/Saturday
    - Peak hours: 10 PM - 2 AM highest demand
    - Events: DJ/holiday events increase demand
    - Inventory: Low inventory signals scarcity, increases demand slightly
    """
    
    if venues is None:
        venues = ["NYX Rooftop Lounge", "The Mayflower DC", "Twelve After Twelve"]
    
    # Load pricing data to get realistic product/price combinations
    csv_dir = Path(__file__).parent.parent
    pricing_data = []
    
    for venue in venues:
        csv_file = csv_dir / f"Drink Pricing - {venue}.csv"
        if csv_file.exists():
            df = pd.read_csv(csv_file)
            df.columns = df.columns.str.strip()
            
            # Map columns
            col_mapping = {'Name': 'bottle', 'Type of Liquor': 'type', 'Price': 'price'}
            for old_col, new_col in col_mapping.items():
                for col in df.columns:
                    if old_col.lower() in col.lower():
                        df = df.rename(columns={col: new_col})
            
            # Clean price
            if 'price' in df.columns:
                df['price'] = df['price'].astype(str).str.replace('$', '').str.replace(',', '').str.strip()
                df['price'] = pd.to_numeric(df['price'], errors='coerce')
                df = df.dropna(subset=['price'])
            
            df['venue'] = venue
            pricing_data.append(df[['venue', 'bottle', 'type', 'price']])
    
    if not pricing_data:
        raise ValueError("No pricing data found. Please ensure CSV files exist.")
    
    products_df = pd.concat(pricing_data, ignore_index=True)
    
    # Event types and their demand multipliers
    event_types = {
        'regular': 1.0,
        'DJ': 1.3,
        'holiday': 1.5,
        'concert': 1.4,
        'private_event': 0.8
    }
    
    data = []
    
    # Generate date range (last 6 months)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)
    
    # Sample products
    sample_size = min(n_samples, len(products_df))
    sampled_products = products_df.sample(n=sample_size, replace=True, random_state=42)
    
    for idx, product_row in sampled_products.iterrows():
        venue = product_row['venue']
        bottle = product_row['bottle']
        bottle_type = product_row['type']
        base_price = product_row['price']
        
        # Random date/time
        random_days = random.randint(0, 180)
        date = start_date + timedelta(days=random_days)
        day_of_week = date.weekday()  # 0=Monday, 6=Sunday
        # Generate hour: 18-23 (evening) or 0-2 (late night)
        if random.random() > 0.5:
            hour = random.randint(0, 2)  # Late night (0-2 AM)
        else:
            hour = random.randint(18, 23)  # Evening (6-11 PM)
        
        month = date.month
        is_weekend = day_of_week >= 4  # Friday, Saturday, Sunday
        
        # Random event type (weighted toward regular)
        event_type = random.choices(
            list(event_types.keys()),
            weights=[0.7, 0.15, 0.05, 0.08, 0.02]
        )[0]
        event_multiplier = event_types[event_type]
        is_holiday = (event_type == 'holiday')
        
        # Inventory level (0-1, where 1 = fully stocked)
        inventory_level = random.uniform(0.1, 1.0)
        
        # Price variation (some days prices change)
        price_variation = random.uniform(0.85, 1.15)  # ±15% variation
        price = base_price * price_variation
        
        # Base demand calculation (simulating price elasticity)
        # Higher price = lower demand (elasticity around -1.5 to -2.0)
        price_elasticity = -1.8
        base_demand = 10.0 * (base_price / 400.0) ** price_elasticity  # Normalize to $400
        
        # Apply multipliers
        demand = base_demand
        
        # Weekend multiplier
        if is_weekend:
            demand *= 2.5 if day_of_week in [4, 5] else 1.8  # Fri/Sat stronger
        
        # Peak hours (10 PM - 2 AM)
        if hour >= 22 or hour <= 2:
            demand *= 1.5
        elif hour >= 20:  # 8-10 PM
            demand *= 1.2
        
        # Event multiplier
        demand *= event_multiplier
        
        # Inventory effect (low inventory = slight demand increase due to scarcity)
        if inventory_level < 0.2:
            demand *= 1.1
        
        # Month effect (summer months higher)
        if month in [6, 7, 8, 12]:  # June, July, August, December
            demand *= 1.2
        
        # Add noise
        demand *= random.uniform(0.7, 1.3)
        
        # Round to integer (can't sell fractional bottles)
        bottles_sold = max(0, round(demand))
        
        data.append({
            'date': date.strftime('%Y-%m-%d'),
            'venue': venue,
            'bottle': bottle,
            'type': bottle_type,
            'price': round(price, 2),
            'bottles_sold': bottles_sold,
            'day_of_week': day_of_week,
            'hour': hour if hour < 24 else hour - 24,
            'is_weekend': 1 if is_weekend else 0,
            'is_holiday': 1 if is_holiday else 0,
            'event_type': event_type,
            'inventory_level': round(inventory_level, 2),
            'month': month,
            'revenue': round(price * bottles_sold, 2)
        })
    
    df = pd.DataFrame(data)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    
    print(f"Generated {len(df)} demand records")
    print(f"Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"Venues: {df['venue'].nunique()}")
    print(f"Products: {df['bottle'].nunique()}")
    print(f"Total bottles sold: {df['bottles_sold'].sum():,.0f}")
    print(f"Total revenue: ${df['revenue'].sum():,.2f}")
    print(f"\nSaved to: {output_path}")
    
    return df


if __name__ == "__main__":
    df = generate_demand_data(n_samples=5000)
    print("\nSample data:")
    print(df.head(10).to_string(index=False))

