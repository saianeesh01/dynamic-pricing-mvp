# Dynamic Pricing Recommendation Engine

MVP implementation of a dynamic pricing engine using market benchmarking, Venue Premium Index (VPI), and Brand Premium Score (BPS).

## Overview

This engine analyzes pricing data across multiple venues to generate price recommendations based on:

1. **Market Benchmarking**: Cross-venue median prices for brands and alcohol types
2. **Venue Premium Index (VPI)**: How each venue prices relative to the market average
3. **Brand Premium Score (BPS)**: How premium a brand is within its category
4. **Guardrails**: Maximum ±15% price changes with rounding rules

## Features

- ✅ Loads pricing data from multiple venue CSV files
- ✅ Computes market benchmarks (global median, brand medians, type medians)
- ✅ Calculates Venue Premium Index (VPI) for each venue
- ✅ Calculates Brand Premium Score (BPS) for each brand
- ✅ Generates price recommendations with explanations
- ✅ Exports recommendations to CSV
- ✅ Interactive Streamlit dashboard for visualization

## Data Format

CSV files should have the following columns:
- `Name` or `bottle`: Bottle/brand name
- `Type of Liquor` or `type`: Alcohol type (Vodka, Tequila, etc.)
- `Price`: Price in format `$300` or `$1,000`

File naming convention: `Drink Pricing - [Venue Name].csv`

## Usage

### Command Line

```bash
# Activate virtual environment
.\venv\Scripts\Activate.ps1  # Windows PowerShell
# or
source venv/bin/activate      # Linux/Mac

# Run the pricing engine
python pricing_engine.py
```

This will:
1. Load all CSV files from the parent directory
2. Compute benchmarks and VPI
3. Generate recommendations
4. Export to `pricing_recommendations.csv`

### Python API

```python
from pricing_engine import PricingEngine

# Initialize engine (CSV files should be in parent directory)
import os
csv_dir = os.path.join(os.path.dirname(__file__), "..")
engine = PricingEngine(csv_dir=csv_dir)

# Load data
engine.load_data()

# Compute benchmarks
engine.compute_benchmarks()
engine.compute_vpi()

# Generate recommendations for a specific bottle
recommendation = engine.recommend_price(
    venue="NYX Rooftop Lounge",
    bottle="Grey Goose",
    bottle_type="Vodka",
    current_price=350,
    max_change_pct=0.15,
    rounding_base=25
)

print(recommendation)

# Generate recommendations for all bottles
df_recs = engine.generate_all_recommendations()
df_recs.to_csv("recommendations.csv", index=False)
```

### Streamlit Dashboard

```bash
# Install dependencies first (if not already installed)
pip install streamlit plotly

# Run dashboard
streamlit run pricing_dashboard.py
```

The dashboard provides:
- 📊 Overview of all recommendations with summary metrics
- 🏢 Filter by venue with price comparisons
- 🍾 Filter by product type with cross-venue analysis
- 📈 Market analysis (VPI, BPS, price distributions)

## Output Format

The recommendations CSV includes:
- `venue`: Venue name
- `bottle`: Bottle/brand name
- `type`: Alcohol type
- `current_price`: Current price
- `recommended_price`: Recommended price
- `delta_pct`: Percentage change
- `delta_abs`: Absolute change
- `market_price_estimate`: Market benchmark price
- `vpi`: Venue Premium Index
- `reason`: Human-readable explanation
- `min_price`: Minimum allowed price (guardrail)
- `max_price`: Maximum allowed price (guardrail)

## Algorithm Details

### Market Price Estimate

For each bottle, the engine uses:
1. Brand median price across all venues (if brand exists in multiple venues)
2. Type median price (if brand not found)
3. Global median price (fallback)

### Target Price Calculation

```
target_price = market_price_estimate × VPI
recommended_price = clamp(target_price, min_price, max_price)
```

Where:
- `min_price = current_price × (1 - max_change_pct)`
- `max_price = current_price × (1 + max_change_pct)`
- Final price is rounded to nearest `rounding_base` (default $25)

### Venue Premium Index (VPI)

```
VPI = venue_median_price / global_median_price
```

- VPI > 1.0: Venue prices above market average
- VPI < 1.0: Venue prices below market average
- VPI = 1.0: Venue prices at market average

### Brand Premium Score (BPS)

```
BPS = brand_median_price / type_median_price
```

- BPS > 1.0: Premium brand within its category
- BPS < 1.0: Value brand within its category

## Phase 2: True Dynamic Pricing

To evolve to real dynamic pricing, add demand signals:
- Bottles sold per night
- Inventory remaining
- Day of week / time of night
- Event type (DJ, holiday, concert)
- Party size / table minimums

Then implement:
- **Demand Prediction Model**: XGBoost to predict quantity sold at given price
- **Price Optimization**: Choose price that maximizes `revenue = price × predicted_demand(price)`

## Example Output

```
venue                  bottle              type      current_price  recommended_price  delta_pct  reason
NYX Rooftop Lounge     Grey Goose          Vodka     350           325                -7.1%     Minor decrease to align with market positioning
The Mayflower DC       Don Julio 1942      Tequila   900           850                -5.6%     below market median for Tequila ($900) and venue typically prices 6% higher than market
Twelve After Twelve    Ace of Spades       Champagne 1000          1100               +10.0%    below market median for Champagne ($1100)
```

## License

MIT
