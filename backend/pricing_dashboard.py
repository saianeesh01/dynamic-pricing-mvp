"""
Streamlit Dashboard for Dynamic Pricing Recommendations
Visualizes pricing recommendations, VPI, BPS, and market benchmarks.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import os
from pricing_engine import PricingEngine

# Page configuration
st.set_page_config(
    page_title="Dynamic Pricing Engine",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title
st.title("💰 Dynamic Pricing Recommendation Engine")
st.markdown("---")

# Initialize session state
if 'engine' not in st.session_state:
    csv_dir = os.path.join(os.path.dirname(__file__), "..")
    engine = PricingEngine(csv_dir=csv_dir)
    engine.load_data()
    engine.compute_benchmarks()
    engine.compute_vpi()
    st.session_state.engine = engine
    st.session_state.recommendations = None

engine = st.session_state.engine

# Sidebar
st.sidebar.header("⚙️ Settings")

max_change_pct = st.sidebar.slider(
    "Max Change %",
    min_value=0.05,
    max_value=0.30,
    value=0.15,
    step=0.05,
    help="Maximum allowed price change percentage"
)

rounding_base = st.sidebar.selectbox(
    "Rounding Base",
    options=[10, 25, 50, 100],
    index=1,
    help="Round prices to nearest $X"
)

if st.sidebar.button("🔄 Generate Recommendations", type="primary"):
    with st.spinner("Generating recommendations..."):
        df_recs = engine.generate_all_recommendations(
            max_change_pct=max_change_pct,
            rounding_base=rounding_base
        )
        st.session_state.recommendations = df_recs
        st.success("Recommendations generated!")

# Load recommendations if available
if st.session_state.recommendations is not None:
    df_recs = st.session_state.recommendations
else:
    # Generate default recommendations
    df_recs = engine.generate_all_recommendations(
        max_change_pct=max_change_pct,
        rounding_base=rounding_base
    )
    st.session_state.recommendations = df_recs

# Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Overview",
    "🏢 By Venue",
    "🍾 By Product",
    "📈 Market Analysis"
])

with tab1:
    st.header("📊 Pricing Recommendations Overview")
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    total_recs = len(df_recs)
    increases = len(df_recs[df_recs['delta_pct'] > 1])
    decreases = len(df_recs[df_recs['delta_pct'] < -1])
    unchanged = len(df_recs[abs(df_recs['delta_pct']) < 1])
    
    col1.metric("Total Recommendations", total_recs)
    col2.metric("Price Increases", increases, delta=f"+{increases}")
    col3.metric("Price Decreases", decreases, delta=f"-{decreases}")
    col4.metric("No Change", unchanged)
    
    # Revenue impact estimate
    current_revenue = df_recs['current_price'].sum()
    recommended_revenue = df_recs['recommended_price'].sum()
    revenue_delta = recommended_revenue - current_revenue
    revenue_delta_pct = (revenue_delta / current_revenue) * 100
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.metric(
            "Estimated Revenue Impact",
            f"${revenue_delta:,.0f}",
            delta=f"{revenue_delta_pct:+.1f}%",
            help="Estimated impact if all recommendations are applied (assuming same demand)"
        )
    
    with col2:
        avg_delta = df_recs['delta_pct'].mean()
        st.metric(
            "Average Price Change",
            f"{avg_delta:+.1f}%",
            help="Average percentage change across all recommendations"
        )
    
    # Distribution chart
    st.subheader("Price Change Distribution")
    fig = px.histogram(
        df_recs,
        x='delta_pct',
        nbins=30,
        labels={'delta_pct': 'Price Change %', 'count': 'Number of Products'},
        color_discrete_sequence=['#1f77b4']
    )
    fig.add_vline(x=0, line_dash="dash", line_color="red", annotation_text="No Change")
    st.plotly_chart(fig, use_container_width=True)
    
    # Top recommendations
    st.subheader("🔝 Top Recommendations")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Largest Increases**")
        top_increases = df_recs.nlargest(10, 'delta_pct')[
            ['venue', 'bottle', 'type', 'current_price', 'recommended_price', 'delta_pct', 'reason']
        ]
        st.dataframe(top_increases, use_container_width=True, hide_index=True)
    
    with col2:
        st.markdown("**Largest Decreases**")
        top_decreases = df_recs.nsmallest(10, 'delta_pct')[
            ['venue', 'bottle', 'type', 'current_price', 'recommended_price', 'delta_pct', 'reason']
        ]
        st.dataframe(top_decreases, use_container_width=True, hide_index=True)

with tab2:
    st.header("🏢 Recommendations by Venue")
    
    venue = st.selectbox("Select Venue", df_recs['venue'].unique())
    venue_recs = df_recs[df_recs['venue'] == venue].copy()
    
    # Venue metrics
    vpi = engine.venue_vpi.get(venue, 1.0)
    col1, col2, col3 = st.columns(3)
    col1.metric("Venue Premium Index (VPI)", f"{vpi:.3f}", delta=f"{(vpi-1)*100:+.1f}%")
    col2.metric("Total Products", len(venue_recs))
    col3.metric("Avg Price Change", f"{venue_recs['delta_pct'].mean():+.1f}%")
    
    # Price comparison chart
    st.subheader("Current vs Recommended Prices")
    
    # Sample for visualization (limit to 30 items for readability)
    viz_df = venue_recs.head(30).sort_values('current_price', ascending=False)
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name='Current Price',
        x=viz_df['bottle'],
        y=viz_df['current_price'],
        marker_color='lightblue'
    ))
    fig.add_trace(go.Bar(
        name='Recommended Price',
        x=viz_df['bottle'],
        y=viz_df['recommended_price'],
        marker_color='lightgreen'
    ))
    fig.update_layout(
        xaxis_title="Product",
        yaxis_title="Price ($)",
        barmode='group',
        height=500,
        xaxis_tickangle=-45
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Full table
    st.subheader("All Recommendations")
    st.dataframe(
        venue_recs[['bottle', 'type', 'current_price', 'recommended_price', 'delta_pct', 'reason']].sort_values('delta_pct', ascending=False),
        use_container_width=True,
        hide_index=True
    )

with tab3:
    st.header("🍾 Recommendations by Product Type")
    
    product_type = st.selectbox("Select Product Type", sorted(df_recs['type'].unique()))
    type_recs = df_recs[df_recs['type'] == product_type].copy()
    
    # Type metrics
    type_median = engine.type_medians.get(product_type, 0)
    col1, col2 = st.columns(2)
    col1.metric("Market Median Price", f"${type_median:.0f}")
    col2.metric("Products in Category", len(type_recs))
    
    # Price by venue comparison
    st.subheader(f"{product_type} Pricing Across Venues")
    
    pivot_df = type_recs.pivot_table(
        index='bottle',
        columns='venue',
        values=['current_price', 'recommended_price'],
        aggfunc='first'
    ).reset_index()
    
    st.dataframe(pivot_df, use_container_width=True)
    
    # Scatter plot: Current vs Recommended
    fig = px.scatter(
        type_recs,
        x='current_price',
        y='recommended_price',
        color='venue',
        hover_data=['bottle'],
        labels={'current_price': 'Current Price ($)', 'recommended_price': 'Recommended Price ($)'},
        title=f"{product_type} Price Recommendations"
    )
    # Add diagonal line
    max_price = max(type_recs['current_price'].max(), type_recs['recommended_price'].max())
    fig.add_trace(go.Scatter(
        x=[0, max_price],
        y=[0, max_price],
        mode='lines',
        line=dict(dash='dash', color='red'),
        name='No Change Line'
    ))
    st.plotly_chart(fig, use_container_width=True)

with tab4:
    st.header("📈 Market Analysis")
    
    # VPI comparison
    st.subheader("Venue Premium Index (VPI)")
    vpi_df = pd.DataFrame([
        {'Venue': venue, 'VPI': vpi, 'Premium %': (vpi - 1) * 100}
        for venue, vpi in engine.venue_vpi.items()
    ]).sort_values('VPI', ascending=False)
    
    fig = px.bar(
        vpi_df,
        x='Venue',
        y='VPI',
        color='VPI',
        color_continuous_scale='RdYlGn',
        labels={'VPI': 'Venue Premium Index'},
        text='VPI'
    )
    fig.add_hline(y=1.0, line_dash="dash", line_color="black", annotation_text="Market Average")
    fig.update_traces(texttemplate='%{text:.3f}', textposition='outside')
    st.plotly_chart(fig, use_container_width=True)
    
    st.dataframe(vpi_df, use_container_width=True, hide_index=True)
    
    # Price distribution by type
    st.subheader("Price Distribution by Alcohol Type")
    
    if engine.df is not None:
        fig = px.box(
            engine.df,
            x='type',
            y='price',
            color='venue',
            labels={'type': 'Alcohol Type', 'price': 'Price ($)'},
            title="Price Distribution Across Venues by Type"
        )
        fig.update_xaxes(tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
    
    # Market benchmarks
    st.subheader("Market Benchmarks")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Median Prices by Type**")
        type_medians_df = pd.DataFrame([
            {'Type': k, 'Median Price': v}
            for k, v in sorted(engine.type_medians.items(), key=lambda x: x[1], reverse=True)
        ])
        st.dataframe(type_medians_df, use_container_width=True, hide_index=True)
    
    with col2:
        st.markdown("**Top Premium Brands (by BPS)**")
        top_bps = sorted(
            [(k, v) for k, v in engine.brand_bps.items()],
            key=lambda x: x[1],
            reverse=True
        )[:20]
        bps_df = pd.DataFrame([
            {
                'Brand': k,
                'BPS': f"{v:.2f}x",
                'Market Median': f"${engine.brand_medians.get(k, 0):.0f}"
            }
            for k, v in top_bps
        ])
        st.dataframe(bps_df, use_container_width=True, hide_index=True)

# Download button
st.sidebar.markdown("---")
if st.sidebar.button("📥 Download Recommendations CSV"):
    csv = df_recs.to_csv(index=False)
    st.sidebar.download_button(
        label="Download",
        data=csv,
        file_name="pricing_recommendations.csv",
        mime="text/csv"
    )

# Footer
st.markdown("---")
st.markdown("""
### About This Engine

This MVP Dynamic Pricing Engine uses:
- **Market Benchmarking**: Cross-venue median prices for brands and types
- **Venue Premium Index (VPI)**: How each venue prices relative to market
- **Brand Premium Score (BPS)**: How premium a brand is within its category

**Next Steps (Phase 2)**: Add demand signals (sales, inventory, events) for true dynamic pricing.
""")

