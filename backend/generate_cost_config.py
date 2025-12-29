"""
Generate cost configuration file from pricing data.

This script estimates costs based on existing prices (assumes current prices have profit margins).
In production, you should replace these estimates with actual COGS data.
"""

import pandas as pd
from pathlib import Path
import sys

# Add backend directory to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from cost_manager import CostManager


def generate_cost_config(csv_dir: str = ".", output_path: str = "backend/data/cost_config.json"):
    """
    Generate cost configuration file by estimating from existing prices.
    
    Args:
        csv_dir: Directory containing venue CSV files
        output_path: Path to save cost configuration JSON file
    """
    csv_dir_path = Path(csv_dir)
    output_path_obj = Path(output_path)
    
    # Load all pricing data
    csv_files = list(csv_dir_path.glob("Drink Pricing*.csv"))
    
    if not csv_files:
        print(f"No CSV files found in {csv_dir}")
        return
    
    all_data = []
    for csv_file in csv_files:
        df = pd.read_csv(csv_file)
        
        # Standardize column names
        if 'Name' in df.columns:
            df = df.rename(columns={'Name': 'bottle', 'Type of Liquor': 'type', 'Price': 'price'})
        
        # Clean price column - remove $ and convert to float
        if 'price' in df.columns:
            df['price'] = df['price'].astype(str).str.replace('$', '').str.replace(',', '').str.strip()
            df['price'] = pd.to_numeric(df['price'], errors='coerce')
            df = df.dropna(subset=['price'])  # Remove rows with invalid prices
        
        # Extract venue name from filename
        venue_name = csv_file.stem.replace('Drink Pricing - ', '')
        df['venue'] = venue_name
        
        all_data.append(df)
    
    combined_df = pd.concat(all_data, ignore_index=True)
    
    # Create CostManager and estimate costs
    cost_manager = CostManager()
    
    # Assume current prices have 60% profit margin (40% cost)
    # Adjust this assumption based on your actual margins
    cost_manager.estimate_costs_from_prices(combined_df, margin_pct=0.60)
    
    # Set minimum profit margin (30% = 0.30)
    cost_manager.min_profit_margin_pct = 0.30
    
    # Save configuration
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
    cost_manager.save_costs(str(output_path_obj))
    
    print(f"\nCost configuration generated at: {output_path}")
    print(f"\nSummary:")
    print(f"  Products with estimated costs: {len(cost_manager.product_costs)}")
    print(f"  Types with estimated costs: {len(cost_manager.type_costs)}")
    print(f"  Minimum profit margin: {cost_manager.min_profit_margin_pct*100:.0f}%")
    print(f"\nNote: These are estimates based on existing prices.")
    print(f"      Please update with actual COGS data when available.")


if __name__ == '__main__':
    import sys
    
    csv_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    output_path = sys.argv[2] if len(sys.argv) > 2 else "backend/data/cost_config.json"
    
    generate_cost_config(csv_dir, output_path)

