"""Quick test to verify bug fixes"""
import os
from pricing_engine_flexible import FlexiblePricingEngine
from pricing_engine import PricingEngine

# Test Bug 1 fix: self.df should be updated in separate mode
print("Testing Bug 1 fix: self.df update in separate mode")
csv_dir = os.path.join(os.path.dirname(__file__), "..")
engine = FlexiblePricingEngine(csv_dir=csv_dir, mode="separate")
engine.load_data(venue_name="NYX Rooftop Lounge")
print(f"  Venues in self.df: {engine.df['venue'].unique()}")
print(f"  Number of records: {len(engine.df)}")
assert len(engine.df['venue'].unique()) == 1, "Bug 1 not fixed: self.df should contain only one venue"
assert engine.df['venue'].iloc[0] == "NYX Rooftop Lounge", "Bug 1 not fixed: wrong venue in self.df"
print("  [OK] Bug 1 fixed: self.df correctly filtered\n")

# Test Bug 3 fix: guardrails after rounding
print("Testing Bug 3 fix: guardrails respected after rounding")
engine2 = PricingEngine(csv_dir=csv_dir)
engine2.load_data()
engine2.compute_benchmarks()
engine2.compute_vpi()

# Test case: rounding that would push outside guardrails
# current_price = $100, max_change = 15%, so max_price = $115
# If target rounds to $125, it should be clamped back to $115
result = engine2.recommend_price(
    venue="NYX Rooftop Lounge",
    bottle="Test",
    bottle_type="Vodka",
    current_price=100.0,
    max_change_pct=0.15,
    rounding_base=25
)
max_price = 100.0 * 1.15  # 115
min_price = 100.0 * 0.85  # 85
assert result['recommended_price'] <= max_price, f"Bug 3 not fixed: {result['recommended_price']} > {max_price}"
assert result['recommended_price'] >= min_price, f"Bug 3 not fixed: {result['recommended_price']} < {min_price}"
print(f"  Current: $100, Recommended: ${result['recommended_price']}, Guardrails: [${min_price}, ${max_price}]")
print(f"  [OK] Bug 3 fixed: guardrails respected after rounding\n")

print("All bug fixes verified!")


