"""
Phase 2: Hybrid Pricing Engine

Combines Phase 1 market benchmarking with Phase 2 demand-based optimization.
Uses demand prediction to optimize pricing for revenue maximization.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
from datetime import datetime
import os
from pathlib import Path

from pricing_engine import PricingEngine
from demand_engine import DemandPredictionModel, PriceOptimizer
from demand_engine import DemandPredictionModel, PriceOptimizer


class HybridPricingEngine(PricingEngine):
    """
    Phase 2 pricing engine that combines:
    1. Market benchmarking (Phase 1)
    2. Demand prediction and optimization (Phase 2)
    
    When demand data is available, optimizes for revenue.
    Falls back to market benchmarking when demand data is unavailable.
    """
    
    def __init__(
        self,
        csv_dir: str = ".",
        demand_model: Optional[DemandPredictionModel] = None,
        use_demand_optimization: bool = True
    ):
        """
        Initialize hybrid pricing engine.
        
        Args:
            csv_dir: Directory containing venue CSV files
            demand_model: Trained demand prediction model (optional)
            use_demand_optimization: Whether to use demand-based optimization when available
        """
        super().__init__(csv_dir)
        self.demand_model = demand_model
        self.price_optimizer = PriceOptimizer(demand_model) if demand_model else None
        self.use_demand_optimization = use_demand_optimization
    
    def recommend_price_v2(
        self,
        venue: str,
        bottle: str,
        bottle_type: str,
        current_price: float,
        max_change_pct: float = 0.15,
        rounding_base: int = 25,
        # Demand signal parameters
        day_of_week: int = None,
        hour: int = None,
        is_weekend: bool = None,
        is_holiday: bool = False,
        event_type: str = 'regular',
        inventory_level: float = 1.0,
        month: int = None
    ) -> Dict:
        """
        Generate price recommendation using hybrid approach.
        
        If demand model is available and use_demand_optimization is True:
        - Uses demand prediction to optimize for revenue
        - Applies market benchmarking as constraints/fallback
        
        Otherwise:
        - Falls back to Phase 1 market benchmarking
        """
        # Get Phase 1 recommendation as baseline
        baseline_rec = self.recommend_price(
            venue=venue,
            bottle=bottle,
            bottle_type=bottle_type,
            current_price=current_price,
            max_change_pct=max_change_pct,
            rounding_base=rounding_base
        )
        
        # If demand optimization is available, use it
        if self.use_demand_optimization and self.price_optimizer:
            try:
                # Get optimal price from demand model
                optimization = self.price_optimizer.optimize_price(
                    venue=venue,
                    bottle=bottle,
                    bottle_type=bottle_type,
                    current_price=current_price,
                    min_price=baseline_rec['min_price'],
                    max_price=baseline_rec['max_price'],
                    price_step=rounding_base,
                    day_of_week=day_of_week,
                    hour=hour,
                    is_weekend=is_weekend,
                    is_holiday=is_holiday,
                    event_type=event_type,
                    inventory_level=inventory_level,
                    month=month
                )
                
                # Use demand-optimized price if it's better
                if optimization['revenue_improvement'] > 0:
                    recommended_price = optimization['optimal_price']
                    reason = f"Demand-optimized: Revenue improvement of ${optimization['revenue_improvement']:.2f} (+{optimization['revenue_improvement_pct']:.1f}%) predicted"
                    method = "demand_optimization"
                else:
                    # Demand model suggests current price is better
                    recommended_price = baseline_rec['recommended_price']
                    reason = baseline_rec['reason'] + " (demand model confirms market-based recommendation)"
                    method = "market_benchmark"
                
                # Round and apply guardrails
                recommended_price = round(recommended_price / rounding_base) * rounding_base
                recommended_price = max(baseline_rec['min_price'], min(baseline_rec['max_price'], recommended_price))
                
                # Calculate delta
                delta_pct = ((recommended_price - current_price) / current_price) * 100
                
                result = {
                    **baseline_rec,
                    'recommended_price': recommended_price,
                    'delta_pct': round(delta_pct, 1),
                    'delta_abs': round(recommended_price - current_price, 2),
                    'reason': reason,
                    'method': method,
                    'predicted_demand_current': optimization.get('current_demand', None),
                    'predicted_demand_optimal': optimization.get('optimal_demand', None),
                    'predicted_revenue_current': optimization.get('current_revenue', None),
                    'predicted_revenue_optimal': optimization.get('optimal_revenue', None),
                    'revenue_improvement': optimization.get('revenue_improvement', None),
                    'revenue_improvement_pct': optimization.get('revenue_improvement_pct', None)
                }
                
                return result
                
            except Exception as e:
                # Fall back to market benchmarking if demand optimization fails
                print(f"Warning: Demand optimization failed: {e}. Falling back to market benchmarking.")
                baseline_rec['method'] = 'market_benchmark_fallback'
                return baseline_rec
        else:
            # No demand model, use Phase 1 approach
            baseline_rec['method'] = 'market_benchmark'
            return baseline_rec
    
    def generate_all_recommendations_v2(
        self,
        max_change_pct: float = 0.15,
        rounding_base: int = 25,
        use_current_time: bool = True,
        **demand_kwargs
    ) -> pd.DataFrame:
        """
        Generate recommendations using hybrid approach for all products.
        
        Args:
            max_change_pct: Maximum price change percentage
            rounding_base: Rounding base for prices
            use_current_time: Use current date/time for demand predictions
            **demand_kwargs: Additional demand signal parameters
        """
        if self.df is None:
            self.load_data()
        
        if not self.venue_vpi:
            self.compute_vpi()
        
        # Set time defaults if using current time
        if use_current_time:
            now = datetime.now()
            if 'day_of_week' not in demand_kwargs:
                demand_kwargs['day_of_week'] = now.weekday()
            if 'hour' not in demand_kwargs:
                demand_kwargs['hour'] = now.hour
            if 'is_weekend' not in demand_kwargs:
                demand_kwargs['is_weekend'] = now.weekday() >= 4
            if 'month' not in demand_kwargs:
                demand_kwargs['month'] = now.month
        
        recommendations = []
        
        for _, row in self.df.iterrows():
            rec = self.recommend_price_v2(
                venue=row['venue'],
                bottle=row['bottle'],
                bottle_type=row['type'],
                current_price=row['price'],
                max_change_pct=max_change_pct,
                rounding_base=rounding_base,
                **demand_kwargs
            )
            recommendations.append(rec)
        
        return pd.DataFrame(recommendations)


