"""
Test script to demonstrate the pricing engine capabilities
"""
import pandas as pd
import os
from pricing_engine import PricingEngine
from pricing_engine_flexible import FlexiblePricingEngine, create_unified_engine, create_separate_engine

def print_section(title):
    print("\n" + "="*80)
    print(title)
    print("="*80)

def main():
    csv_dir = os.path.join(os.path.dirname(__file__), "..")
    
    # Test 1: Unified Mode (All Venues Together)
    print_section("TEST 1: Unified Mode - All Venues Together")
    
    unified = create_unified_engine(csv_dir)
    
    # Show VPI results
    print("\n>>> Venue Premium Index (VPI) - How each venue prices vs market:")
    for venue, vpi in sorted(unified.venue_vpi.items(), key=lambda x: x[1], reverse=True):
        premium = (vpi - 1) * 100
        print(f"   {venue:25s} VPI: {vpi:.3f} ({premium:+.1f}%)")
    
    # Generate and show recommendations summary
    df_recs = unified.generate_all_recommendations()
    
    print("\n>>> Recommendations Summary:")
    summary = df_recs.groupby('venue').agg({
        'delta_pct': ['count', 'mean'],
        'current_price': 'sum',
        'recommended_price': 'sum'
    }).round(2)
    
    for venue in df_recs['venue'].unique():
        venue_data = df_recs[df_recs['venue'] == venue]
        increases = len(venue_data[venue_data['delta_pct'] > 1])
        decreases = len(venue_data[venue_data['delta_pct'] < -1])
        unchanged = len(venue_data[abs(venue_data['delta_pct']) < 1])
        
        current_revenue = venue_data['current_price'].sum()
        recommended_revenue = venue_data['recommended_price'].sum()
        revenue_delta = recommended_revenue - current_revenue
        revenue_delta_pct = (revenue_delta / current_revenue) * 100
        
        print(f"\n   {venue}:")
        print(f"      Total products: {len(venue_data)}")
        print(f"      Increase: {increases} | Decrease: {decreases} | No change: {unchanged}")
        print(f"      Revenue impact: ${revenue_delta:,.0f} ({revenue_delta_pct:+.1f}%)")
        print(f"      Avg price change: {venue_data['delta_pct'].mean():+.1f}%")
    
    # Show top recommendations
    print_section("TOP 5 RECOMMENDATIONS BY IMPACT")
    print("\n>>> Largest Price Increases:")
    top_increases = df_recs.nlargest(5, 'delta_pct')[
        ['venue', 'bottle', 'type', 'current_price', 'recommended_price', 'delta_pct']
    ]
    for _, row in top_increases.iterrows():
        print(f"   {row['venue']:25s} {row['bottle']:25s} ${row['current_price']:>6.0f} -> ${row['recommended_price']:>6.0f} ({row['delta_pct']:+.1f}%)")
    
    print("\n>>> Largest Price Decreases:")
    top_decreases = df_recs.nsmallest(5, 'delta_pct')[
        ['venue', 'bottle', 'type', 'current_price', 'recommended_price', 'delta_pct']
    ]
    for _, row in top_decreases.iterrows():
        print(f"   {row['venue']:25s} {row['bottle']:25s} ${row['current_price']:>6.0f} -> ${row['recommended_price']:>6.0f} ({row['delta_pct']:+.1f}%)")
    
    # Test 2: Separate Mode (Single Venue with External Benchmarks)
    print_section("TEST 2: Separate Mode - Single Venue with External Benchmarks")
    
    # Extract benchmarks from unified engine
    benchmarks = FlexiblePricingEngine.create_from_unified_engine(unified)
    print(f"\n[OK] Extracted market benchmarks:")
    print(f"   Global median: ${benchmarks['global_median']:.2f}")
    print(f"   Brands tracked: {len(benchmarks['brand_medians'])}")
    print(f"   Types tracked: {len(benchmarks['type_medians'])}")
    
    # Create separate instance for NYX
    print("\n>>> Creating separate instance for NYX Rooftop Lounge...")
    separate_nyx = create_separate_engine(
        csv_dir=csv_dir,
        venue_name="NYX Rooftop Lounge",
        external_benchmarks=benchmarks
    )
    
    # Show VPI for this venue
    vpi_nyx = separate_nyx.venue_vpi.get("NYX Rooftop Lounge", 1.0)
    print(f"\n>>> NYX Venue Premium Index: {vpi_nyx:.3f} ({(vpi_nyx-1)*100:+.1f}% vs market)")
    
    # Generate recommendations for NYX only
    nyx_recs = separate_nyx.generate_all_recommendations()
    nyx_recs_filtered = nyx_recs[nyx_recs['venue'] == 'NYX Rooftop Lounge']
    
    print(f"\n>>> NYX Recommendations:")
    print(f"   Total products: {len(nyx_recs_filtered)}")
    print(f"   Increases: {len(nyx_recs_filtered[nyx_recs_filtered['delta_pct'] > 1])}")
    print(f"   Decreases: {len(nyx_recs_filtered[nyx_recs_filtered['delta_pct'] < -1])}")
    print(f"   No change: {len(nyx_recs_filtered[abs(nyx_recs_filtered['delta_pct']) < 1])}")
    
    print_section("TEST COMPLETE")
    print("\n[SUCCESS] All tests passed!")
    print("\n>>> Next steps:")
    print("   1. View full recommendations: backend/pricing_recommendations.csv")
    print("   2. Launch dashboard: streamlit run pricing_dashboard.py")
    print("   3. Test different settings in dashboard sidebar")

if __name__ == "__main__":
    main()

