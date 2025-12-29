"""
Test Phase 2: Demand-based pricing engine
"""

import os
from pathlib import Path
from demand_engine import DemandPredictionModel, PriceOptimizer
from pricing_engine_v2 import HybridPricingEngine
from train_demand_model import main as train_model


def test_demand_prediction():
    """Test demand prediction model"""
    print("=" * 80)
    print("TEST 1: Demand Prediction Model")
    print("=" * 80)
    
    model_path = Path(__file__).parent / 'models' / 'demand_model.joblib'
    
    if not model_path.exists():
        print("Model not found. Training...")
        train_model()
    
    model = DemandPredictionModel()
    model.load(str(model_path))
    
    # Test prediction
    predicted = model.predict(
        price=350,
        venue="NYX Rooftop Lounge",
        bottle="Grey Goose",
        bottle_type="Vodka",
        day_of_week=5,  # Saturday
        hour=22,  # 10 PM
        is_weekend=True,
        event_type="DJ",
        inventory_level=0.5
    )
    
    print(f"\nPrediction for Grey Goose at NYX:")
    print(f"  Price: $350")
    print(f"  Conditions: Saturday 10 PM, DJ event, 50% inventory")
    print(f"  Predicted bottles sold: {predicted:.1f}")
    print("[OK] Demand prediction working\n")


def test_price_optimization():
    """Test price optimization"""
    print("=" * 80)
    print("TEST 2: Price Optimization")
    print("=" * 80)
    
    model_path = Path(__file__).parent / 'models' / 'demand_model.joblib'
    model = DemandPredictionModel()
    model.load(str(model_path))
    
    optimizer = PriceOptimizer(model)
    
    result = optimizer.optimize_price(
        venue="NYX Rooftop Lounge",
        bottle="Grey Goose",
        bottle_type="Vodka",
        current_price=350,
        day_of_week=5,  # Saturday
        hour=22,  # 10 PM
        is_weekend=True,
        event_type="DJ"
    )
    
    print(f"\nPrice Optimization for Grey Goose at NYX (Saturday 10 PM, DJ event):")
    print(f"  Current price: ${result['current_price']:.2f}")
    print(f"  Current predicted demand: {result['current_demand']:.1f} bottles")
    print(f"  Current predicted revenue: ${result['current_revenue']:.2f}")
    print(f"\n  Optimal price: ${result['optimal_price']:.2f}")
    print(f"  Optimal predicted demand: {result['optimal_demand']:.1f} bottles")
    print(f"  Optimal predicted revenue: ${result['optimal_revenue']:.2f}")
    print(f"\n  Revenue improvement: ${result['revenue_improvement']:.2f} (+{result['revenue_improvement_pct']:.1f}%)")
    print(f"  Price change: ${result['price_change']:.2f} ({result['price_change_pct']:+.1f}%)")
    print("[OK] Price optimization working\n")


def test_hybrid_engine():
    """Test hybrid pricing engine"""
    print("=" * 80)
    print("TEST 3: Hybrid Pricing Engine (Phase 1 + Phase 2)")
    print("=" * 80)
    
    csv_dir = Path(__file__).parent.parent
    model_path = Path(__file__).parent / 'models' / 'demand_model.joblib'
    
    # Load demand model
    demand_model = DemandPredictionModel()
    if model_path.exists():
        demand_model.load(str(model_path))
        print("Demand model loaded")
    else:
        print("Demand model not found. Training...")
        train_model()
        demand_model.load(str(model_path))
    
    # Create hybrid engine
    engine = HybridPricingEngine(
        csv_dir=str(csv_dir),
        demand_model=demand_model,
        use_demand_optimization=True
    )
    engine.load_data()
    engine.compute_benchmarks()
    engine.compute_vpi()
    
    # Get recommendation
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
    
    print(f"\nHybrid Recommendation for Grey Goose at NYX:")
    print(f"  Current price: ${rec['current_price']:.2f}")
    print(f"  Recommended price: ${rec['recommended_price']:.2f}")
    print(f"  Change: {rec['delta_pct']:+.1f}%")
    print(f"  Method: {rec.get('method', 'unknown')}")
    print(f"  Reason: {rec['reason']}")
    
    if 'predicted_revenue_optimal' in rec and rec['predicted_revenue_optimal']:
        print(f"\n  Demand Model Predictions:")
        print(f"    Current: {rec.get('predicted_demand_current', 0):.1f} bottles -> ${rec.get('predicted_revenue_current', 0):.2f} revenue")
        print(f"    Optimal: {rec.get('predicted_demand_optimal', 0):.1f} bottles -> ${rec.get('predicted_revenue_optimal', 0):.2f} revenue")
        print(f"    Improvement: ${rec.get('revenue_improvement', 0):.2f} (+{rec.get('revenue_improvement_pct', 0):.1f}%)")
    
    print("[OK] Hybrid engine working\n")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("PHASE 2 TESTING: Demand-Based Dynamic Pricing")
    print("=" * 80 + "\n")
    
    try:
        test_demand_prediction()
        test_price_optimization()
        test_hybrid_engine()
        
        print("=" * 80)
        print("[SUCCESS] All Phase 2 tests passed!")
        print("=" * 80)
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()


