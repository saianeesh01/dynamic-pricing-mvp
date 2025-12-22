# Dynamic Pricing Engine - Quick Start Guide

## ✅ What's Been Built

A complete **MVP Dynamic Pricing Recommendation Engine** that:
- Analyzes pricing across all 3 venues (NYX Rooftop Lounge, The Mayflower DC, Twelve After Twelve)
- Generates price recommendations with explanations
- Exports results to CSV
- Provides an interactive dashboard

## 🚀 Quick Start

### 1. Generate Recommendations (Command Line)

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python pricing_engine.py
```

This creates `backend/pricing_recommendations.csv` with recommendations for all 174 products.

### 2. View Interactive Dashboard

```powershell
cd backend
.\venv\Scripts\Activate.ps1
streamlit run pricing_dashboard.py
```

Then open http://localhost:8501 in your browser.

## 📊 Key Insights from Your Data

Based on the current dataset:

- **Global median price**: $400
- **Venue Premium Index (VPI)**:
  - The Mayflower DC: 1.062 (+6.2% above market)
  - NYX Rooftop Lounge: 0.938 (-6.2% below market)
  - Twelve After Twelve: 0.812 (-18.8% below market)

- **Recommendations**:
  - 56 products should increase in price
  - 99 products should decrease in price
  - 19 products are optimally priced

## 📁 Files Created

1. **`backend/pricing_engine.py`** - Core engine with all logic
2. **`backend/pricing_dashboard.py`** - Streamlit dashboard
3. **`backend/pricing_recommendations.csv`** - Generated recommendations
4. **`backend/README_PRICING_ENGINE.md`** - Full documentation

## 🔍 Example Recommendation

```
Venue: NYX Rooftop Lounge
Bottle: Grey Goose
Type: Vodka
Current Price: $350
Recommended Price: $325
Change: -7.1%
Reason: Minor decrease to align with market positioning
```

The engine recommends this because:
- NYX has a VPI of 0.938 (prices 6.2% below market)
- Market median for Grey Goose is $350
- Target = $350 × 0.938 = $328.30
- Rounded to $325 (nearest $25)
- Within ±15% guardrail

## 📈 Next Steps (Phase 2)

To make this **truly dynamic**, add demand signals:
- Bottles sold per night
- Inventory remaining
- Day of week / time
- Event types

Then implement:
- Demand prediction model (XGBoost)
- Price optimization to maximize revenue

See `backend/README_PRICING_ENGINE.md` for full details.
