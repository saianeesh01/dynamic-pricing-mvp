"""
Cost Manager: Handles product costs and profit margin constraints

This module manages:
- Product costs (COGS - Cost of Goods Sold)
- Minimum profit margins
- Profit calculations
- Cost validation
"""

import pandas as pd
import json
from pathlib import Path
from typing import Dict, Optional
from collections import defaultdict


class CostManager:
    """
    Manages product costs and profit margin requirements.
    
    Supports:
    - Product-specific costs
    - Type-based default costs (if product cost not specified)
    - Minimum profit margin percentages
    - Cost validation and fallback handling
    """
    
    def __init__(self, cost_config_path: Optional[str] = None):
        """
        Initialize CostManager.
        
        Args:
            cost_config_path: Path to JSON file with cost configuration.
                             If None, uses default cost estimation.
        """
        self.cost_config_path = Path(cost_config_path) if cost_config_path else None
        self.product_costs: Dict[str, float] = {}  # bottle_name -> cost
        self.type_costs: Dict[str, float] = {}     # type -> default cost
        self.min_profit_margin_pct: float = 0.30   # Default 30% minimum margin
        
        if self.cost_config_path and self.cost_config_path.exists():
            self.load_costs()
        else:
            # Initialize with default cost estimation (assumes 40% cost, 60% margin)
            self.use_default_costs = True
    
    def load_costs(self):
        """Load costs from JSON configuration file."""
        try:
            with open(self.cost_config_path, 'r') as f:
                config = json.load(f)
            
            # Load product-specific costs
            if 'product_costs' in config:
                self.product_costs = {
                    k.lower().strip(): float(v) 
                    for k, v in config['product_costs'].items()
                }
            
            # Load type-based default costs
            if 'type_costs' in config:
                self.type_costs = {
                    k: float(v) 
                    for k, v in config['type_costs'].items()
                }
            
            # Load minimum profit margin
            if 'min_profit_margin_pct' in config:
                self.min_profit_margin_pct = float(config['min_profit_margin_pct'])
            
            self.use_default_costs = False
            print(f"Loaded cost configuration from {self.cost_config_path}")
        except Exception as e:
            print(f"Warning: Could not load cost config: {e}. Using default cost estimation.")
            self.use_default_costs = True
    
    def get_cost(self, bottle: str, bottle_type: str, current_price: Optional[float] = None) -> float:
        """
        Get cost for a product.
        
        Args:
            bottle: Bottle/brand name
            bottle_type: Alcohol type
            current_price: Current selling price (used for default estimation)
        
        Returns:
            Cost of the product
        """
        bottle_norm = bottle.lower().strip()
        
        # Try product-specific cost first
        if bottle_norm in self.product_costs:
            return self.product_costs[bottle_norm]
        
        # Try type-based default cost
        if bottle_type in self.type_costs:
            return self.type_costs[bottle_type]
        
        # Fallback: estimate from current price (assume 40% cost, 60% margin)
        if current_price and self.use_default_costs:
            return current_price * 0.40
        
        # Ultimate fallback: use type-based median estimation
        # This is a rough estimate - should be replaced with actual cost data
        type_cost_defaults = {
            'Vodka': 150.0,
            'Tequila': 200.0,
            'Whiskey & Bourbon': 180.0,
            'Scotch': 250.0,
            'Champagne': 300.0,
            'Gin': 140.0,
            'Rum': 130.0,
            'Cognac': 350.0,
        }
        return type_cost_defaults.get(bottle_type, 175.0)
    
    def calculate_profit(self, price: float, cost: float) -> float:
        """Calculate profit (price - cost)."""
        return price - cost
    
    def calculate_profit_margin(self, price: float, cost: float) -> float:
        """
        Calculate profit margin percentage.
        
        Formula: ((price - cost) / price) * 100
        """
        if price <= 0:
            return 0.0
        return ((price - cost) / price) * 100
    
    def get_minimum_price(self, cost: float, min_margin_pct: Optional[float] = None) -> float:
        """
        Calculate minimum price to achieve profit margin.
        
        Formula: cost / (1 - min_margin_pct)
        
        Args:
            cost: Product cost
            min_margin_pct: Minimum profit margin (as decimal, e.g., 0.30 for 30%)
                          If None, uses self.min_profit_margin_pct
        """
        if min_margin_pct is None:
            min_margin_pct = self.min_profit_margin_pct
        
        if min_margin_pct >= 1.0:
            raise ValueError("Profit margin must be < 1.0 (use decimal, e.g., 0.30 for 30%)")
        
        return cost / (1 - min_margin_pct)
    
    def is_profitable(self, price: float, cost: float, min_margin_pct: Optional[float] = None) -> bool:
        """Check if price meets minimum profit margin requirement."""
        if min_margin_pct is None:
            min_margin_pct = self.min_profit_margin_pct
        
        margin = self.calculate_profit_margin(price, cost)
        return margin >= (min_margin_pct * 100)
    
    def save_costs(self, output_path: str):
        """Save current cost configuration to JSON file."""
        config = {
            'product_costs': self.product_costs,
            'type_costs': self.type_costs,
            'min_profit_margin_pct': self.min_profit_margin_pct
        }
        
        with open(output_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"Cost configuration saved to {output_path}")
    
    def estimate_costs_from_prices(self, df: pd.DataFrame, margin_pct: float = 0.60):
        """
        Estimate costs from existing prices (for initialization).
        
        This assumes current prices have a certain profit margin and estimates costs.
        Note: This is a rough estimate - actual costs should be provided when available.
        
        Args:
            df: DataFrame with columns: bottle, type, price
            margin_pct: Assumed profit margin (as decimal). Default 0.60 means 60% margin.
        """
        print(f"Estimating costs assuming {margin_pct*100:.0f}% profit margin...")
        
        # Estimate costs for each product
        for _, row in df.iterrows():
            bottle = row.get('bottle', '')
            bottle_type = row.get('type', '')
            price = float(row.get('price', 0))
            
            try:
                # Handle price as string (remove $, commas, etc.)
                if isinstance(price, str):
                    price = price.replace('$', '').replace(',', '').strip()
                price = float(price)
                
                if price > 0:
                    estimated_cost = price * (1 - margin_pct)
                    bottle_norm = bottle.lower().strip()
                    
                    # Store if not already set
                    if bottle_norm not in self.product_costs:
                        self.product_costs[bottle_norm] = estimated_cost
            except (ValueError, TypeError):
                continue  # Skip invalid prices
        
        # Calculate type medians for defaults
        for bottle_type in df['type'].unique():
            type_rows = df[df['type'] == bottle_type]['price']
            type_prices = []
            for price_val in type_rows:
                try:
                    if isinstance(price_val, str):
                        price_val = price_val.replace('$', '').replace(',', '').strip()
                    type_prices.append(float(price_val))
                except (ValueError, TypeError):
                    continue
            
            if len(type_prices) > 0:
                import numpy as np
                type_median_price = np.median(type_prices)
                self.type_costs[bottle_type] = type_median_price * (1 - margin_pct)
        
        print(f"Estimated costs for {len(self.product_costs)} products")
        print(f"Estimated costs for {len(self.type_costs)} types")

