# Phase 4: Profit-Aware Pricing Optimization

This phase adds cost management and profit margin constraints to ensure all pricing recommendations are profitable.

## Overview

Phase 4 extends the pricing engine to:
- **Track product costs (COGS)** - Cost of Goods Sold for each product
- **Enforce minimum profit margins** - Ensure all prices meet minimum profitability requirements (default: 30%)
- **Optimize for profit** - When demand data is available, optimize for profit (revenue - cost) instead of just revenue
- **Prevent negative margins** - Automatically adjust prices to ensure profitability

## Key Components

### 1. CostManager (`backend/cost_manager.py`)

Manages product costs and profit calculations:

```python
from cost_manager import CostManager

# Load from config file
cost_manager = CostManager(cost_config_path='backend/data/cost_config.json')

# Get cost for a product
cost = cost_manager.get_cost(bottle="Grey Goose", bottle_type="Vodka", current_price=350)

# Calculate profit margin
margin = cost_manager.calculate_profit_margin(price=350, cost=140)  # Returns 60.0 (60%)

# Get minimum price for profitability
min_price = cost_manager.get_minimum_price(cost=140)  # Returns 200.0 (for 30% margin)
```

**Features:**
- Product-specific costs
- Type-based default costs (fallback)
- Minimum profit margin enforcement (default: 30%)
- Cost estimation from existing prices (for initialization)

### 2. Cost Configuration

Cost data is stored in `backend/data/cost_config.json`:

```json
{
  "product_costs": {
    "grey goose": 140.0,
    "don julio 1942": 360.0
  },
  "type_costs": {
    "Vodka": 120.0,
    "Tequila": 160.0
  },
  "min_profit_margin_pct": 0.30
}
```

### 3. Integration with Pricing Engine

The `PricingEngine` now accepts a `cost_manager` parameter:

```python
from pricing_engine import PricingEngine
from cost_manager import CostManager

cost_manager = CostManager(cost_config_path='backend/data/cost_config.json')
engine = PricingEngine(csv_dir=".", cost_manager=cost_manager)

# Recommendations now include profit metrics
recommendation = engine.recommend_price(
    venue="NYX Rooftop Lounge",
    bottle="Grey Goose",
    bottle_type="Vodka",
    current_price=350
)

print(recommendation['profit_margin_pct'])  # e.g., 60.0%
print(recommendation['cost'])  # e.g., 140.0
print(recommendation['profit'])  # e.g., 210.0
```

### 4. Profit-Optimized Demand Engine

When `CostManager` is provided to `PriceOptimizer`, it optimizes for **profit** instead of revenue:

```python
from demand_engine import PriceOptimizer, DemandPredictionModel
from cost_manager import CostManager

demand_model = DemandPredictionModel()
demand_model.load('models/demand_model.joblib')

cost_manager = CostManager(cost_config_path='backend/data/cost_config.json')
optimizer = PriceOptimizer(demand_model, cost_manager=cost_manager)

# Optimizes for profit = (price - cost) × predicted_demand
result = optimizer.optimize_price(
    venue="NYX Rooftop Lounge",
    bottle="Grey Goose",
    bottle_type="Vodka",
    current_price=350
)

print(result['optimal_profit'])  # Profit at optimal price
print(result['profit_improvement'])  # Profit improvement vs current
```

## How It Works

### Price Recommendation Process

1. **Calculate target price** using market benchmarking (Phase 1)
2. **Get product cost** from CostManager
3. **Calculate minimum profitable price**: `min_price = cost / (1 - margin_pct)`
4. **Apply profit constraint**: Ensure recommended price ≥ minimum profitable price
5. **Final check**: After rounding, verify profitability and adjust if needed

### Profit Margin Calculation

```
Profit Margin (%) = ((Price - Cost) / Price) × 100

Example:
- Price: $350
- Cost: $140
- Profit: $210
- Profit Margin: 60%
```

### Minimum Price Calculation

To achieve a minimum profit margin:

```
Minimum Price = Cost / (1 - Margin_Percentage)

Example (30% margin):
- Cost: $140
- Margin: 30% (0.30)
- Minimum Price: $140 / (1 - 0.30) = $200
```

## Usage

### Generate Cost Configuration

First, generate a cost configuration file from your existing pricing data:

```bash
cd backend
python generate_cost_config.py .. backend/data/cost_config.json
```

This estimates costs assuming a 60% profit margin (40% cost) on current prices.

**Important:** Update the cost values in `cost_config.json` with your actual COGS data for accurate profit calculations.

### Run with Profit Constraints

The pricing engine automatically uses the cost manager if available:

```python
from pricing_engine import PricingEngine
from cost_manager import CostManager

# Load cost manager
cost_manager = CostManager(cost_config_path='backend/data/cost_config.json')

# Initialize engine with cost manager
engine = PricingEngine(csv_dir=".", cost_manager=cost_manager)
engine.load_data()
engine.compute_benchmarks()
engine.compute_vpi()

# Generate recommendations (now with profit constraints)
recommendations = engine.generate_all_recommendations()
```

### Web Dashboard

The web dashboard (`web_app.py`) automatically loads the cost manager if the config file exists. Recommendations will show:

- **Cost**: Product cost (COGS)
- **Profit**: Profit per unit (Price - Cost)
- **Profit Margin**: Profit margin percentage
- **Min Profit Price**: Minimum price to achieve target margin

## API Response Format

Recommendations now include profit metrics:

```json
{
  "venue": "NYX Rooftop Lounge",
  "bottle": "Grey Goose",
  "type": "Vodka",
  "current_price": 350.0,
  "recommended_price": 350.0,
  "delta_pct": 0.0,
  "cost": 140.0,
  "profit": 210.0,
  "profit_margin_pct": 60.0,
  "current_profit": 210.0,
  "current_profit_margin_pct": 60.0,
  "profit_change": 0.0,
  "min_profit_price": 200.0,
  "reason": "Price is optimal. (Profit margin: 60.0%)"
}
```

## Benefits

1. **No Negative Margins**: All recommendations ensure minimum profitability
2. **Cost-Aware Optimization**: Demand optimization considers costs, not just revenue
3. **Flexible Cost Structure**: Supports product-specific and type-based costs
4. **Easy Configuration**: JSON-based cost configuration
5. **Backward Compatible**: Works without cost manager (uses Phase 1-3 only)

## Next Steps

1. **Update Cost Data**: Replace estimated costs with actual COGS from your inventory system
2. **Adjust Profit Margins**: Modify `min_profit_margin_pct` based on your business requirements
3. **Monitor Profitability**: Track profit metrics in recommendations and dashboard
4. **Optimize Further**: Use profit-optimized demand predictions for better pricing decisions

## Files

- `backend/cost_manager.py` - Cost management and profit calculations
- `backend/generate_cost_config.py` - Generate cost configuration from pricing data
- `backend/data/cost_config.json` - Cost configuration file
- `backend/pricing_engine.py` - Updated to support cost_manager
- `backend/demand_engine.py` - Updated PriceOptimizer for profit optimization
- `backend/pricing_engine_v2.py` - Updated HybridPricingEngine for cost_manager
- `backend/web_app.py` - Integrated CostManager in web application

