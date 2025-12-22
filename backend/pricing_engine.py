"""
Dynamic Pricing Recommendation Engine
MVP implementation using market benchmarking, VPI, and BPS.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import re
from typing import Dict, List, Tuple, Optional
from collections import defaultdict


class PricingEngine:
    """
    Dynamic Pricing Engine that generates price recommendations based on:
    1. Market Benchmark (cross-venue median prices)
    2. Venue Premium Index (VPI)
    3. Brand Premium Score (BPS)
    """
    
    def __init__(self, csv_dir: str = "."):
        """
        Initialize the pricing engine.
        
        Args:
            csv_dir: Directory containing venue CSV files
        """
        self.csv_dir = Path(csv_dir)
        self.df = None
        self.venue_vpi = {}  # Venue Premium Index per venue
        self.global_avg_price = None
        self.brand_medians = {}  # Median price per brand across all venues
        self.type_medians = {}  # Median price per alcohol type
        self.brand_bps = {}  # Brand Premium Score per brand within type
        
    def load_data(self) -> pd.DataFrame:
        """
        Load and consolidate all venue CSV files.
        Extracts venue name from filename.
        """
        csv_files = list(self.csv_dir.glob("Drink Pricing*.csv"))
        
        if not csv_files:
            raise ValueError(f"No CSV files found in {self.csv_dir}")
        
        all_data = []
        
        for csv_file in csv_files:
            # Extract venue name from filename
            venue_name = csv_file.stem.replace("Drink Pricing - ", "")
            
            try:
                df = pd.read_csv(csv_file)
                
                # Standardize column names
                df.columns = df.columns.str.strip()
                
                # Map to standard columns
                col_mapping = {
                    'Name': 'bottle',
                    'Type of Liquor': 'type',
                    'Price': 'price'
                }
                
                # Find best matching columns
                for old_col, new_col in col_mapping.items():
                    for col in df.columns:
                        if old_col.lower() in col.lower() or new_col.lower() in col.lower():
                            df = df.rename(columns={col: new_col})
                            break
                
                # Add venue column
                df['venue'] = venue_name
                
                # Clean price column - remove $ and commas, convert to float
                if 'price' in df.columns:
                    df['price'] = df['price'].astype(str).str.replace('$', '').str.replace(',', '').str.strip()
                    df['price'] = pd.to_numeric(df['price'], errors='coerce')
                    df = df.dropna(subset=['price'])  # Remove rows with invalid prices
                    
                # Clean bottle and type names
                if 'bottle' in df.columns:
                    df['bottle'] = df['bottle'].astype(str).str.strip()
                if 'type' in df.columns:
                    df['type'] = df['type'].astype(str).str.strip()
                    
                all_data.append(df[['venue', 'bottle', 'type', 'price']])
                
            except Exception as e:
                print(f"Error loading {csv_file}: {e}")
                continue
        
        if not all_data:
            raise ValueError("No valid data loaded from CSV files")
        
        self.df = pd.concat(all_data, ignore_index=True)
        
        # Normalize bottle names (handle variations)
        self.df['bottle_normalized'] = self.df['bottle'].str.lower().str.strip()
        
        print(f"Loaded {len(self.df)} records from {len(csv_files)} venues")
        return self.df
    
    def compute_benchmarks(self):
        """Compute market benchmarks: global averages, brand medians, type medians."""
        if self.df is None:
            raise ValueError("Data not loaded. Call load_data() first.")
        
        # Global average price
        self.global_avg_price = self.df['price'].median()
        
        # Brand medians (across all venues)
        self.brand_medians = self.df.groupby('bottle_normalized')['price'].median().to_dict()
        
        # Type medians (across all venues)
        self.type_medians = self.df.groupby('type')['price'].median().to_dict()
        
        # Brand Premium Score (BPS): brand median / type median
        self.brand_bps = {}
        for bottle, brand_median in self.brand_medians.items():
            # Find the type(s) for this brand
            brand_types = self.df[self.df['bottle_normalized'] == bottle]['type'].unique()
            if len(brand_types) > 0:
                # Use the most common type for this brand
                type_median = self.type_medians.get(brand_types[0], brand_median)
                if type_median > 0:
                    self.brand_bps[bottle] = brand_median / type_median
                else:
                    self.brand_bps[bottle] = 1.0
            else:
                self.brand_bps[bottle] = 1.0
        
        print(f"Computed benchmarks:")
        print(f"  Global median price: ${self.global_avg_price:.2f}")
        print(f"  Brands tracked: {len(self.brand_medians)}")
        print(f"  Types tracked: {len(self.type_medians)}")
    
    def compute_vpi(self):
        """
        Compute Venue Premium Index (VPI) for each venue.
        VPI = venue_median_price / global_median_price
        """
        if self.df is None:
            raise ValueError("Data not loaded. Call load_data() first.")
        
        if self.global_avg_price is None:
            self.compute_benchmarks()
        
        venue_medians = self.df.groupby('venue')['price'].median()
        
        for venue, venue_median in venue_medians.items():
            self.venue_vpi[venue] = venue_median / self.global_avg_price if self.global_avg_price > 0 else 1.0
        
        print(f"\nVenue Premium Index (VPI):")
        for venue, vpi in sorted(self.venue_vpi.items(), key=lambda x: x[1], reverse=True):
            print(f"  {venue}: {vpi:.3f} ({'+' if vpi > 1 else ''}{(vpi - 1) * 100:.1f}%)")
    
    def get_market_price_estimate(self, bottle: str, bottle_type: str) -> float:
        """
        Estimate market price for a bottle using:
        1. Brand median (if exists across venues)
        2. Type median (fallback)
        """
        bottle_norm = bottle.lower().strip()
        
        # Try brand median first
        if bottle_norm in self.brand_medians:
            return self.brand_medians[bottle_norm]
        
        # Fallback to type median
        if bottle_type in self.type_medians:
            return self.type_medians[bottle_type]
        
        # Ultimate fallback: global median
        return self.global_avg_price
    
    def recommend_price(
        self,
        venue: str,
        bottle: str,
        bottle_type: str,
        current_price: float,
        max_change_pct: float = 0.15,
        rounding_base: int = 25
    ) -> Dict:
        """
        Generate price recommendation for a bottle at a venue.
        
        Args:
            venue: Venue name
            bottle: Bottle/brand name
            bottle_type: Alcohol type
            current_price: Current price
            max_change_pct: Maximum allowed change (default 15%)
            rounding_base: Round to nearest N dollars (default 25)
        
        Returns:
            Dictionary with recommendation details
        """
        # Get market price estimate
        market_price = self.get_market_price_estimate(bottle, bottle_type)
        
        # Get venue VPI
        vpi = self.venue_vpi.get(venue, 1.0)
        
        # Target price = market_price * VPI
        target_price = market_price * vpi
        
        # Apply guardrails: max change
        max_price = current_price * (1 + max_change_pct)
        min_price = current_price * (1 - max_change_pct)
        
        # Clamp target price to guardrails
        recommended_price = max(min_price, min(max_price, target_price))
        
        # Round to nearest rounding_base
        recommended_price = round(recommended_price / rounding_base) * rounding_base
        
        # Re-apply guardrails after rounding to ensure they're still respected
        # (rounding can push price outside guardrails)
        recommended_price = max(min_price, min(max_price, recommended_price))
        
        # Ensure it's at least $25
        recommended_price = max(25, recommended_price)
        
        # Calculate delta
        delta_pct = ((recommended_price - current_price) / current_price) * 100
        
        # Generate explanation
        reason = self._generate_reason(
            venue, bottle, bottle_type, current_price, recommended_price,
            market_price, vpi
        )
        
        return {
            'venue': venue,
            'bottle': bottle,
            'type': bottle_type,
            'current_price': current_price,
            'recommended_price': recommended_price,
            'delta_pct': round(delta_pct, 1),
            'delta_abs': round(recommended_price - current_price, 2),
            'market_price_estimate': round(market_price, 2),
            'vpi': round(vpi, 3),
            'reason': reason,
            'min_price': round(min_price, 2),
            'max_price': round(max_price, 2)
        }
    
    def _generate_reason(
        self,
        venue: str,
        bottle: str,
        bottle_type: str,
        current_price: float,
        recommended_price: float,
        market_price: float,
        vpi: float
    ) -> str:
        """Generate human-readable explanation for recommendation."""
        delta_pct = ((recommended_price - current_price) / current_price) * 100
        
        reasons = []
        
        if abs(delta_pct) < 1:
            return f"Price is optimal. Current price aligns well with market ({bottle_type} median: ${market_price:.0f}) and venue positioning (VPI: {vpi:.2f})."
        
        # Compare to market
        if current_price < market_price * 0.9:
            reasons.append(f"below market median for {bottle_type} (${market_price:.0f})")
        elif current_price > market_price * 1.1:
            reasons.append(f"above market median for {bottle_type} (${market_price:.0f})")
        
        # Compare to venue positioning
        if vpi > 1.1:
            reasons.append(f"venue typically prices {vpi - 1:.0%} higher than market")
        elif vpi < 0.9:
            reasons.append(f"venue typically prices {abs(vpi - 1):.0%} lower than market")
        
        # Direction
        if delta_pct > 0:
            direction = "increase"
        else:
            direction = "decrease"
        
        if reasons:
            explanation = f"Recommend {direction} due to: {', '.join(reasons)}"
        else:
            explanation = f"Minor {direction} to align with market positioning"
        
        return explanation
    
    def generate_all_recommendations(
        self,
        max_change_pct: float = 0.15,
        rounding_base: int = 25
    ) -> pd.DataFrame:
        """
        Generate recommendations for all bottles across all venues.
        
        Returns:
            DataFrame with recommendations
        """
        if self.df is None:
            self.load_data()
        
        if not self.venue_vpi:
            self.compute_vpi()
        
        recommendations = []
        
        for _, row in self.df.iterrows():
            rec = self.recommend_price(
                venue=row['venue'],
                bottle=row['bottle'],
                bottle_type=row['type'],
                current_price=row['price'],
                max_change_pct=max_change_pct,
                rounding_base=rounding_base
            )
            recommendations.append(rec)
        
        return pd.DataFrame(recommendations)
    
    def export_recommendations(
        self,
        output_path: str = "pricing_recommendations.csv",
        max_change_pct: float = 0.15,
        rounding_base: int = 25
    ):
        """
        Generate and export recommendations to CSV.
        """
        print(f"\nGenerating recommendations for all venues...")
        df_recs = self.generate_all_recommendations(
            max_change_pct=max_change_pct,
            rounding_base=rounding_base
        )
        
        df_recs.to_csv(output_path, index=False)
        print(f"[SUCCESS] Recommendations exported to {output_path}")
        print(f"\nSummary:")
        print(f"  Total recommendations: {len(df_recs)}")
        print(f"  Recommendations to increase: {len(df_recs[df_recs['delta_pct'] > 1])}")
        print(f"  Recommendations to decrease: {len(df_recs[df_recs['delta_pct'] < -1])}")
        print(f"  No change needed: {len(df_recs[abs(df_recs['delta_pct']) < 1])}")
        
        return df_recs


if __name__ == "__main__":
    # Example usage
    # CSV files are in parent directory
    import os
    csv_dir = os.path.join(os.path.dirname(__file__), "..")
    engine = PricingEngine(csv_dir=csv_dir)
    engine.load_data()
    engine.compute_benchmarks()
    engine.compute_vpi()
    
    # Generate recommendations
    output_path = os.path.join(os.path.dirname(__file__), "pricing_recommendations.csv")
    df_recs = engine.export_recommendations(output_path)
    
    # Show sample recommendations
    print("\n" + "="*80)
    print("SAMPLE RECOMMENDATIONS")
    print("="*80)
    print(df_recs[['venue', 'bottle', 'type', 'current_price', 'recommended_price', 'delta_pct', 'reason']].head(20).to_string(index=False))
