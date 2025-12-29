# Phase 2: Demand-Based Dynamic Pricing

Phase 2 extends the MVP pricing engine with **demand prediction** and **revenue optimization** using machine learning.

## What's New in Phase 2

### Key Features

1. **Demand Prediction Model (XGBoost)**
   - Predicts bottles sold at different price points
   - Considers: price, day/time, events, inventory, venue, product type
   - Trained on historical sales data

2. **Price Optimization**
   - Finds optimal price to maximize revenue = price × predicted_demand
   - Grid search over price range
   - Respects guardrails and market constraints

3. **Hybrid Pricing Engine**
   - Combines Phase 1 market benchmarking with Phase 2 demand optimization
   - Uses demand model when available, falls back to market benchmarking
   - Best of both worlds: market intelligence + revenue optimization

---

## Quick Start

### 1. Generate Demand Data

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python generate_demand_data.py
```

This creates synthetic sales history in `backend/data/demand_history.csv` with:
- Price variations
- Weekend/weekday patterns
- Time-of-day patterns
- Event types (regular, DJ, holiday, concert)
- Inventory levels

### 2. Train Demand Model

```powershell
python train_demand_model.py
```

This trains an XGBoost model to predict bottles sold and saves it to `backend/models/demand_model.joblib`.

### 3. Test Phase 2

```powershell
python test_phase2.py
```

This runs tests for:
- Demand prediction
- Price optimization
- Hybrid engine integration

### 4. Use Hybrid Engine

```python
from pricing_engine_v2 import HybridPricingEngine
from demand_engine import DemandPredictionModel
from pathlib import Path

# Load demand model
model = DemandPredictionModel()
model.load('backend/models/demand_model.joblib')

# Create hybrid engine
engine = HybridPricingEngine(
    csv_dir=".",
    demand_model=model,
    use_demand_optimization=True
)
engine.load_data()
engine.compute_benchmarks()
engine.compute_vpi()

# Get optimized recommendation
rec = engine.recommend_price_v2(
    venue="NYX Rooftop Lounge",
    bottle="Grey Goose",
    bottle_type="Vodka",
    current_price=350,
    day_of_week=5,  # Saturday
    hour=22,  # 10 PM
    is_weekend=True,
    event_type="DJ"
)

print(f"Recommended: ${rec['recommended_price']:.2f}")
print(f"Predicted revenue improvement: ${rec.get('revenue_improvement', 0):.2f}")
```

---

## How It Works

### Demand Prediction Model

The model predicts `bottles_sold` given:

**Features:**
- `price`: Product price
- `venue`: Venue name (categorical)
- `type`: Alcohol type (categorical)
- `day_of_week`: 0-6 (Monday-Sunday)
- `hour`: 0-23
- `is_weekend`: 0 or 1
- `is_holiday`: 0 or 1
- `event_type`: regular, DJ, holiday, concert, etc. (categorical)
- `inventory_level`: 0-1 (remaining inventory / capacity)
- `month`: 1-12

**Target:**
- `bottles_sold`: Number of bottles sold (integer)

The model learns:
- **Price elasticity**: How demand changes with price
- **Temporal patterns**: Weekend/weekday, time-of-day effects
- **Event effects**: How different events affect demand
- **Inventory effects**: Scarcity signals

### Price Optimization

For each product, the optimizer:

1. **Defines price range**: ±30-50% from current price (with guardrails)
2. **Grid search**: Tests prices at regular intervals (e.g., $5 steps)
3. **Predicts demand**: For each price, predicts bottles sold
4. **Calculates revenue**: revenue = price × predicted_demand
5. **Finds maximum**: Selects price with highest predicted revenue

### Hybrid Approach

The hybrid engine combines both methods:

1. **Phase 1 (Market Benchmarking)**: Provides baseline recommendation
2. **Phase 2 (Demand Optimization)**: Finds revenue-optimal price
3. **Comparison**: Uses demand-optimized price if it improves revenue
4. **Fallback**: Uses market benchmarking if demand model unavailable or fails

**Output includes:**
- Recommended price
- Method used (demand_optimization vs market_benchmark)
- Predicted demand at current and optimal prices
- Predicted revenue improvement

---

## Example Output

```
Hybrid Recommendation for Grey Goose at NYX:
  Current price: $350.00
  Recommended price: $375.00
  Change: +7.1%
  Method: demand_optimization
  Reason: Demand-optimized: Revenue improvement of $125.50 (+8.2%) predicted

  Demand Model Predictions:
    Current: 12.3 bottles → $4,305.00 revenue
    Optimal: 13.1 bottles → $4,912.50 revenue
    Improvement: $607.50 (+14.1%)
```

---

## Files Created

1. **`backend/demand_engine.py`**
   - `DemandPredictionModel`: XGBoost model for demand prediction
   - `PriceOptimizer`: Finds optimal price for revenue maximization

2. **`backend/pricing_engine_v2.py`**
   - `HybridPricingEngine`: Combines Phase 1 + Phase 2

3. **`backend/generate_demand_data.py`**
   - Generates synthetic sales history for training

4. **`backend/train_demand_model.py`**
   - Trains and saves demand prediction model

5. **`backend/test_phase2.py`**
   - Tests Phase 2 functionality

---

## Next Steps

1. **Collect Real Data**: Replace synthetic data with actual sales history
2. **Fine-tune Model**: Adjust hyperparameters for better accuracy
3. **Add Features**: Weather, local events, competitor pricing, etc.
4. **A/B Testing**: Test optimized prices in production
5. **Real-time Updates**: Integrate with POS systems for live pricing

---

## Differences: Phase 1 vs Phase 2

| Feature | Phase 1 (MVP) | Phase 2 (Demand-Based) |
|---------|---------------|------------------------|
| **Method** | Market benchmarking | Demand prediction + optimization |
| **Input** | Cross-venue prices | Sales history + demand signals |
| **Output** | Market-aligned price | Revenue-maximizing price |
| **Accuracy** | Market positioning | Revenue prediction |
| **Use Case** | Competitive pricing | Revenue optimization |
| **When to Use** | New products, no sales data | Products with sales history |

---

## Integration with Phase 1

The hybrid engine seamlessly integrates both approaches:

- **New products**: Uses Phase 1 (market benchmarking)
- **Established products**: Uses Phase 2 (demand optimization)
- **Fallback**: Always falls back to Phase 1 if Phase 2 unavailable

This ensures the system works for all scenarios!


