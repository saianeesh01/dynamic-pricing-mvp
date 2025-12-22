"""
Flexible Pricing Engine - Supports both Unified and Separate Instance models
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from pricing_engine import PricingEngine


class FlexiblePricingEngine(PricingEngine):
    """
    Extended PricingEngine that supports:
    1. Unified model: All venues together (original)
    2. Separate model: Single venue with external benchmarks
    3. Hybrid model: Single venue with API-fetched benchmarks
    """
    
    def __init__(self, csv_dir: str = ".", mode: str = "unified", external_benchmarks: Optional[Dict] = None):
        """
        Initialize the flexible pricing engine.
        
        Args:
            csv_dir: Directory containing venue CSV files
            mode: "unified" (all venues) or "separate" (single venue)
            external_benchmarks: Optional dict with pre-computed benchmarks
                Format: {
                    'global_median': float,
                    'brand_medians': {brand: price},
                    'type_medians': {type: price}
                }
        """
        super().__init__(csv_dir)
        self.mode = mode  # "unified" or "separate"
        self.external_benchmarks = external_benchmarks
        self.venue_filter = None  # For separate mode, filter to single venue
        
    def load_data(self, venue_name: Optional[str] = None) -> pd.DataFrame:
        """
        Load data - supports both unified and separate modes.
        
        Args:
            venue_name: If provided (separate mode), only load this venue's data
        """
        if self.mode == "separate" and venue_name:
            self.venue_filter = venue_name
        
        # Load all data first
        df = super().load_data()
        
        # Filter to single venue if in separate mode
        if self.mode == "separate" and self.venue_filter:
            df = df[df['venue'] == self.venue_filter].copy()
            if len(df) == 0:
                raise ValueError(f"Venue '{venue_name}' not found in data")
            # IMPORTANT: Update self.df to the filtered data so subsequent operations use correct data
            self.df = df
            print(f"Separate mode: Loaded {len(df)} records for {venue_name} only")
        
        return df
    
    def compute_benchmarks(self):
        """
        Compute benchmarks - supports external benchmarks for separate mode.
        """
        if self.external_benchmarks:
            # Use external benchmarks (from API or shared service)
            self.global_avg_price = self.external_benchmarks.get('global_median')
            self.brand_medians = self.external_benchmarks.get('brand_medians', {})
            self.type_medians = self.external_benchmarks.get('type_medians', {})
            
            # Compute BPS from external benchmarks
            self.brand_bps = {}
            for bottle, brand_median in self.brand_medians.items():
                # Try to find type from our data
                if self.df is not None:
                    brand_data = self.df[self.df['bottle_normalized'] == bottle]
                    if len(brand_data) > 0:
                        bottle_type = brand_data['type'].iloc[0]
                        type_median = self.type_medians.get(bottle_type, brand_median)
                    else:
                        type_median = brand_median
                else:
                    type_median = brand_median
                
                if type_median > 0:
                    self.brand_bps[bottle] = brand_median / type_median
                else:
                    self.brand_bps[bottle] = 1.0
            
            print(f"Using external benchmarks:")
            print(f"  Global median price: ${self.global_avg_price:.2f}")
            print(f"  Brands tracked: {len(self.brand_medians)}")
            print(f"  Types tracked: {len(self.type_medians)}")
        else:
            # Use unified benchmarks (compute from all data)
            super().compute_benchmarks()
    
    def compute_vpi(self):
        """
        Compute VPI - works for both modes.
        In separate mode, VPI is computed against external global median.
        """
        if self.df is None:
            raise ValueError("Data not loaded. Call load_data() first.")
        
        if self.global_avg_price is None:
            self.compute_benchmarks()
        
        if self.mode == "separate" and self.venue_filter:
            # Single venue mode: compute VPI for just this venue
            venue_median = self.df['price'].median()
            self.venue_vpi[self.venue_filter] = venue_median / self.global_avg_price if self.global_avg_price > 0 else 1.0
            print(f"\nVenue Premium Index (VPI) for {self.venue_filter}: {self.venue_vpi[self.venue_filter]:.3f}")
        else:
            # Unified mode: compute VPI for all venues
            super().compute_vpi()
    
    def export_benchmarks(self) -> Dict:
        """
        Export current benchmarks for sharing with other instances.
        Useful for centralized benchmark service.
        
        Returns:
            Dictionary with benchmark data (no venue-specific info)
        """
        if self.global_avg_price is None:
            self.compute_benchmarks()
        
        return {
            'global_median': self.global_avg_price,
            'brand_medians': self.brand_medians,
            'type_medians': self.type_medians,
            'brand_bps': self.brand_bps
        }
    
    @staticmethod
    def create_from_unified_engine(unified_engine: PricingEngine) -> Dict:
        """
        Extract benchmarks from a unified engine to share with separate instances.
        
        Args:
            unified_engine: A PricingEngine instance with all venues loaded
            
        Returns:
            Benchmark dictionary ready for external_benchmarks parameter
        """
        if unified_engine.global_avg_price is None:
            unified_engine.compute_benchmarks()
        
        return {
            'global_median': unified_engine.global_avg_price,
            'brand_medians': unified_engine.brand_medians,
            'type_medians': unified_engine.type_medians
        }


# Example usage functions
def create_unified_engine(csv_dir: str = ".") -> PricingEngine:
    """Create engine in unified mode (all venues together)."""
    engine = PricingEngine(csv_dir=csv_dir)
    engine.load_data()
    engine.compute_benchmarks()
    engine.compute_vpi()
    return engine


def create_separate_engine(csv_dir: str = ".", venue_name: str = "NYX Rooftop Lounge", 
                          external_benchmarks: Optional[Dict] = None) -> FlexiblePricingEngine:
    """
    Create engine in separate mode (single venue with external benchmarks).
    
    Example:
        # Get benchmarks from unified engine
        unified = create_unified_engine()
        benchmarks = FlexiblePricingEngine.create_from_unified_engine(unified)
        
        # Create separate instance for one venue
        separate = create_separate_engine(
            venue_name="NYX Rooftop Lounge",
            external_benchmarks=benchmarks
        )
    """
    engine = FlexiblePricingEngine(
        csv_dir=csv_dir,
        mode="separate",
        external_benchmarks=external_benchmarks
    )
    engine.load_data(venue_name=venue_name)
    engine.compute_benchmarks()
    engine.compute_vpi()
    return engine


if __name__ == "__main__":
    import os
    
    # Example 1: Unified mode (current approach)
    print("=" * 80)
    print("EXAMPLE 1: Unified Mode (All Venues Together)")
    print("=" * 80)
    csv_dir = os.path.join(os.path.dirname(__file__), "..")
    unified = create_unified_engine(csv_dir)
    
    # Example 2: Separate mode with shared benchmarks
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Separate Mode (Single Venue with External Benchmarks)")
    print("=" * 80)
    
    # Extract benchmarks from unified engine
    benchmarks = FlexiblePricingEngine.create_from_unified_engine(unified)
    
    # Create separate instance for NYX
    separate_nyx = create_separate_engine(
        csv_dir=csv_dir,
        venue_name="NYX Rooftop Lounge",
        external_benchmarks=benchmarks
    )
    
    # Generate recommendations for NYX only
    nyx_recs = separate_nyx.generate_all_recommendations()
    print(f"\nGenerated {len(nyx_recs)} recommendations for NYX Rooftop Lounge")
    print("\nSample recommendations:")
    print(nyx_recs[['bottle', 'current_price', 'recommended_price', 'delta_pct', 'reason']].head(10).to_string(index=False))
