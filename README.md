# Dynamic Pricing Recommendation Engine

A sophisticated pricing engine that analyzes market data across multiple venues to generate intelligent price recommendations using market benchmarking, venue positioning, and brand premium analysis.

---

## Table of Contents

1. [How It Works - The Algorithm](#how-it-works---the-algorithm)
2. [Understanding the Metrics](#understanding-the-metrics)
3. [Reading the Output](#reading-the-output)
4. [Real-World Examples](#real-world-examples)
5. [Quick Start](#quick-start)
6. [Project Structure](#project-structure)

---

## How It Works - The Algorithm

The pricing engine uses a three-step approach to generate recommendations:

### Step 1: Market Benchmarking

The engine analyzes pricing data across all venues to establish market baselines:

1. **Brand-Level Medians**: For each bottle/brand, calculates the median price across all venues where it's sold
   - Example: Grey Goose appears at $350 (NYX), $375 (Mayflower) → Median = $350

2. **Type-Level Medians**: For each alcohol type (Vodka, Tequila, etc.), calculates the median price across all products of that type
   - Example: All Vodkas across all venues → Median Vodka price = $325

3. **Global Median**: The median price across ALL products and ALL venues
   - Example: Global median = $400

**Why This Matters**: These benchmarks represent "fair market value" - what similar products typically sell for in your market.

---

### Step 2: Venue Premium Index (VPI)

VPI measures how each venue prices relative to the market average.

**Formula:**
```
VPI = Venue's Median Price / Global Median Price
```

**Interpretation:**
- **VPI > 1.0**: Venue prices above market (premium positioning)
- **VPI = 1.0**: Venue prices at market average
- **VPI < 1.0**: Venue prices below market (value positioning)

**Example from Your Data:**
- **The Mayflower DC**: VPI = 1.062 (+6.2%) → Premium venue, charges 6.2% above market
- **NYX Rooftop Lounge**: VPI = 0.938 (-6.2%) → Value venue, charges 6.2% below market
- **Twelve After Twelve**: VPI = 0.812 (-18.8%) → Discount venue, charges 18.8% below market

**Why This Matters**: VPI tells you if a venue's overall pricing strategy matches market positioning. A premium venue should price higher; a value venue should price lower.

---

### Step 3: Brand Premium Score (BPS)

BPS measures how premium a brand is within its category.

**Formula:**
```
BPS = Brand Median Price / Type Median Price
```

**Interpretation:**
- **BPS > 1.5**: Premium brand (e.g., Don Julio 1942)
- **BPS = 1.0**: Average brand
- **BPS < 0.8**: Value brand

**Example:**
- **Don Julio 1942**: $900 median / $450 Tequila median = BPS 2.0x (premium)
- **Tito's Vodka**: $350 median / $325 Vodka median = BPS 1.08x (average)

**Why This Matters**: Helps identify which brands command premium pricing and ensures premium brands aren't under-priced.

---

### Step 4: Recommendation Calculation

For each product, the engine:

1. **Finds Market Price**: Uses brand median (if exists) or type median (fallback)
2. **Applies Venue Positioning**: Multiplies by VPI to account for venue's pricing strategy
3. **Applies Guardrails**: Limits change to ±15% (default) to prevent dramatic swings
4. **Rounds Price**: Rounds to nearest $25 (default) for clean pricing

**Formula:**
```
target_price = market_price_estimate × VPI
recommended_price = clamp(target_price, min_price, max_price)
rounded_price = round_to_nearest(recommended_price, $25)
```

Where:
- `min_price = current_price × 0.85` (max 15% decrease)
- `max_price = current_price × 1.15` (max 15% increase)

---

## Understanding the Metrics

### In the Recommendations CSV

Each row contains:

| Column | Description | Example | How to Read It |
|--------|-------------|---------|----------------|
| **venue** | Club/venue name | "NYX Rooftop Lounge" | Which club this recommendation is for |
| **bottle** | Product name | "Grey Goose" | The specific bottle |
| **type** | Alcohol category | "Vodka" | Product category |
| **current_price** | What you charge now | $350 | Your current pricing |
| **recommended_price** | What the engine suggests | $325 | New price recommendation |
| **delta_pct** | Percentage change | -7.1% | How much to change price |
| **delta_abs** | Dollar change | -$25 | Absolute dollar difference |
| **market_price_estimate** | Market benchmark | $350 | What market typically charges |
| **vpi** | Venue Premium Index | 0.938 | Your venue's pricing position |
| **reason** | Explanation | "Minor decrease to align..." | Why this recommendation |
| **min_price** | Minimum allowed | $297.50 | Guardrail: can't go below this |
| **max_price** | Maximum allowed | $402.50 | Guardrail: can't go above this |

---

### Key Metrics Explained

#### delta_pct (Price Change %)

**What it means**: How much to adjust the price

**How to interpret**:
- **Positive (e.g., +10%)**: Increase price - you're under-priced relative to market
- **Negative (e.g., -7%)**: Decrease price - you're over-priced relative to market
- **Near zero (±1%)**: Price is optimal - no change needed

**Real Example**:
```
Bottle: Don Julio Reposado at NYX
Current: $475
Recommended: $425
Delta: -10.5%
```
**Translation**: NYX is charging $475, but market median for Don Julio Reposado is $450. NYX's VPI is 0.938 (value venue), so target = $450 × 0.938 = $422.50 → rounds to $425. Recommendation: Lower by $50 (-10.5%).

---

#### market_price_estimate

**What it means**: The benchmark price for this product in your market

**How to interpret**:
- If your price is **above** market estimate → You may be over-priced
- If your price is **below** market estimate → You may be under-priced
- Compare to your VPI: Premium venues (VPI > 1.0) can charge above market

**Real Example**:
```
Grey Goose:
- Market estimate: $350 (median across all venues)
- NYX current: $350
- NYX VPI: 0.938 (value venue)
- Target: $350 × 0.938 = $328.50 → $325
```
**Translation**: Market says Grey Goose is worth $350. But NYX is a value venue, so it should price at $325 to match its positioning.

---

#### VPI (Venue Premium Index)

**What it means**: Your venue's overall pricing strategy relative to market

**How to interpret**:
- **1.062** = You price 6.2% above market (premium)
- **1.000** = You price at market average
- **0.938** = You price 6.2% below market (value)
- **0.812** = You price 18.8% below market (discount)

**Real Insights from Your Data**:
- **The Mayflower DC** (VPI 1.062): Premium positioning - can charge more
- **NYX** (VPI 0.938): Value positioning - should price lower
- **Twelve After Twelve** (VPI 0.812): Deep discount - significant pricing upside potential

**Action Item**: If your VPI is very low (< 0.85) but you want to be premium, raise prices. If your VPI is high (> 1.1) but you want to be value-focused, lower prices.

---

#### reason (Explanation)

**What it means**: Plain English explanation of why this recommendation was made

**Common reasons**:
- **"Price is optimal"**: No change needed - aligned with market
- **"below market median"**: You're charging less than competitors → can raise
- **"above market median"**: You're charging more than competitors → consider lowering
- **"venue typically prices X% higher/lower"**: Recommendation accounts for your venue's positioning

---

## Reading the Output

### Summary Statistics

After generating recommendations, you'll see:

```
Summary:
  Total recommendations: 174
  Recommendations to increase: 56
  Recommendations to decrease: 99
  No change needed: 19
```

**What this tells you**:
- **56 increases**: Products that are under-priced - revenue opportunity
- **99 decreases**: Products that are over-priced - may lose customers
- **19 optimal**: Products priced correctly - leave as-is

### Revenue Impact Analysis

Calculate potential revenue impact:

```
Current Total Revenue = Sum of all current_price
Recommended Total Revenue = Sum of all recommended_price
Revenue Delta = Recommended - Current
Revenue Delta % = (Delta / Current) × 100
```

**From Your Data**:
- **The Mayflower DC**: +$2,625 (+4.2%) → Raising prices could increase revenue
- **NYX**: -$1,185 (-5.4%) → Lowering prices might reduce revenue (but increase volume?)
- **Twelve After Twelve**: -$4,000 (-13.7%) → Significant price adjustment needed

**Important**: Revenue impact assumes **same demand**. In reality:
- **Price increases** may reduce quantity sold
- **Price decreases** may increase quantity sold
- Consider **price elasticity** in decision-making

---

## Real-World Examples

### Example 1: Premium Product at Value Venue

```
Venue: NYX Rooftop Lounge
Bottle: Don Julio 1942
Type: Tequila
Current Price: $850
Recommended Price: $850
Delta: 0.0%
Market Estimate: $900
VPI: 0.938
Reason: "Price is optimal. Current price aligns well with market (Tequila median: $900) and venue positioning (VPI: 0.94)."
```

**Analysis**:
- Don Julio 1942 market median is $900
- NYX's VPI is 0.938 (value venue)
- Target price: $900 × 0.938 = $844.20
- Current $850 is close enough → **No change needed**

**Takeaway**: Premium product is correctly priced for a value venue.

---

### Example 2: Over-Priced Product

```
Venue: NYX Rooftop Lounge
Bottle: Don Julio Reposado
Type: Tequila
Current Price: $475
Recommended Price: $425
Delta: -10.5%
Market Estimate: $450
VPI: 0.938
Reason: "Minor decrease to align with market positioning"
```

**Analysis**:
- Market median for Don Julio Reposado: $450
- NYX's VPI: 0.938 (value venue)
- Target: $450 × 0.938 = $422.50 → rounds to $425
- Current $475 is $50 too high → **Decrease by $50**

**Takeaway**: Product is over-priced for a value venue. Lowering could improve competitiveness.

---

### Example 3: Under-Priced Product at Premium Venue

```
Venue: The Mayflower DC
Bottle: Dom Perignon Rose
Type: Champagne
Current Price: $1,250
Recommended Price: $1,400
Delta: +12.0%
Market Estimate: $1,250
VPI: 1.062
Reason: "Minor increase to align with market positioning"
```

**Analysis**:
- Market median for Dom Perignon Rose: $1,250
- Mayflower's VPI: 1.062 (premium venue)
- Target: $1,250 × 1.062 = $1,327.50 → rounds to $1,325 (but max change is +15% = $1,437.50)
- Recommendation: $1,400 (within guardrails)
- Current $1,250 → **Increase by $150**

**Takeaway**: Premium venue can charge more. This is a revenue opportunity.

---

### Example 4: Optimal Pricing

```
Venue: NYX Rooftop Lounge
Bottle: Grey Goose
Type: Vodka
Current Price: $350
Recommended Price: $325
Delta: -7.1%
Market Estimate: $350
VPI: 0.938
Reason: "Minor decrease to align with market positioning"
```

**Analysis**:
- Market median for Grey Goose: $350
- NYX's VPI: 0.938 (value venue)
- Target: $350 × 0.938 = $328.50 → rounds to $325
- Current $350 → **Decrease to $325**

**Takeaway**: Value venue should price below market. Small adjustment aligns with positioning.

---

## Quick Start

### 1. Generate Recommendations

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python pricing_engine.py
```

This creates `backend/pricing_recommendations.csv` with all recommendations.

### 2. View Dashboard

```powershell
cd backend
.\venv\Scripts\Activate.ps1
streamlit run pricing_dashboard.py
```

Then open `http://localhost:8501` in your browser.

### 3. Test the Engine

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python test_engine.py
```

Shows summary statistics and examples.

---

## Project Structure

```
dynamic pricing/
├── backend/
│   ├── pricing_engine.py          # Core pricing algorithm
│   ├── pricing_engine_flexible.py # Supports unified/separate modes
│   ├── pricing_dashboard.py       # Streamlit interactive dashboard
│   ├── test_engine.py             # Test script with examples
│   ├── pricing_recommendations.csv # Generated recommendations
│   └── requirements.txt           # Python dependencies
├── Drink Pricing - *.csv          # Input data files
└── README.md                      # This file
```

---

## Understanding Your Results

### Key Questions to Ask

1. **What's my venue's VPI?**
   - Tells you if you're premium, value, or discount positioned

2. **Which products are most over/under-priced?**
   - Sort by `delta_pct` to find biggest opportunities

3. **What's the revenue impact?**
   - Sum `recommended_price` vs `current_price` to see total impact

4. **Are recommendations consistent with my strategy?**
   - If you want to be premium but VPI is low, you need bigger price increases

5. **Which categories need most adjustment?**
   - Group by `type` to see if Vodkas, Tequilas, etc. need rebalancing

### Decision Framework

**For Each Recommendation**:

1. **Check the reason**: Why is this change recommended?
2. **Check market estimate**: How does your price compare to market?
3. **Check VPI**: Does the recommendation align with your venue positioning?
4. **Check guardrails**: Are min/max prices reasonable?
5. **Consider demand**: Will this change affect volume sold?

**Remember**: These are **recommendations**, not mandates. Use business judgment:
- Premium products at premium venues → Can charge more
- Value venues → Should price competitively
- New products → May need market testing before following recommendations

---

## Next Steps: Phase 2 (Future)

To make this **truly dynamic**, add demand signals:
- Bottles sold per night
- Inventory levels
- Day of week / time of night
- Event types (DJ, holiday, concert)

Then implement:
- **Demand Prediction Model**: Predict quantity sold at given price
- **Revenue Optimization**: Choose price that maximizes `revenue = price × predicted_demand`

See `PRODUCT_STRATEGY.md` for the roadmap.

---

## Support & Documentation

- **Algorithm Details**: See `backend/README_PRICING_ENGINE.md`
- **Product Strategy**: See `PRODUCT_STRATEGY.md`
- **Decision Guide**: See `DECISION_GUIDE.md`
