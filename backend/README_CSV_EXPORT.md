# Understanding the CSV Export

The pricing recommendations CSV export includes comprehensive profit and revenue information.

## Columns Explained

### Basic Information
- **Venue**: Venue name
- **Bottle**: Product/bottle name
- **Type**: Alcohol type (Vodka, Tequila, etc.)

### Pricing Information
- **Current Price**: Current selling price
- **Recommended Price**: Engine's recommended price
- **Change %**: Percentage change from current to recommended

### Profit Information (Most Important!)
- **Cost**: Cost of Goods Sold (COGS) per bottle
- **Profit per Bottle**: Recommended Price - Cost
- **Profit Margin %**: ((Price - Cost) / Price) × 100
- **Status**: 
  - **PROFITABLE**: Profit margin ≥ 30% (meets minimum requirement)
  - **POSITIVE MARGIN**: Profit margin > 0% but < 30%
  - **NEGATIVE MARGIN**: Loss-making (Price < Cost) - **NEVER happens with Phase 4**

### Revenue & Method
- **Revenue Impact**: Predicted change in total revenue (can be negative if demand model predicts lower revenue)
- **Method**: Phase 1 (Market Benchmarking) or Phase 2 (AI Demand Optimization)

## How to Read the Data

### Example Row:
```
NYX Rooftop Lounge, Grey Goose, Vodka, 350, 402.5, +15%, 140.00, 262.50, 65.2%, 1003.94, Phase 2, PROFITABLE
```

**What this means:**
- Current price: $350
- Recommended price: $402.50 (+15% increase)
- Cost: $140 per bottle
- **Profit per bottle: $262.50** ($402.50 - $140)
- **Profit margin: 65.2%** (well above 30% minimum)
- **Status: PROFITABLE** ✓
- Revenue impact: +$1003.94 (demand model predicts revenue increase)

### Negative Revenue Impact Example:
```
NYX Rooftop Lounge, Bombay Sapphire, Gin, 300, 275, -8.3%, 120.00, 155.00, 56.4%, -576.53, Phase 2, PROFITABLE
```

**What this means:**
- Current price: $300
- Recommended price: $275 (-8.3% decrease)
- Cost: $120 per bottle
- **Profit per bottle: $155** ($275 - $120) ✓
- **Profit margin: 56.4%** (above 30% minimum) ✓
- **Status: PROFITABLE** ✓
- Revenue impact: -$576.53 (demand model predicts lower total revenue, BUT each sale is still profitable!)

**Key Point:** Negative revenue impact does NOT mean the product is unprofitable. It means the demand model predicts that lowering the price might reduce total revenue, but each individual sale is still profitable.

## Quick Filtering Guide

### Filter for Highly Profitable Products:
- **Profit Margin %** ≥ 50%
- **Status** = "PROFITABLE"

### Filter for Products Needing Attention:
- **Profit Margin %** < 30% (or "POSITIVE MARGIN" status)
- These may need price adjustments to meet minimum margin requirements

### Filter for Revenue Opportunities:
- **Revenue Impact** > 0 (positive revenue impact)
- These products have pricing opportunities that increase both profit AND revenue

## Important Notes

1. **All recommendations ensure profitability** - Phase 4 guarantees minimum 30% profit margin
2. **Cost data** comes from `backend/data/cost_config.json` (estimates based on 60% margin assumption)
3. **Update costs** with actual COGS data for more accurate profit calculations
4. **Revenue Impact** is a prediction based on the demand model - actual results may vary
5. **Profit is guaranteed**, revenue impact is a prediction

