"""
Phase 3: Professional Web Application
Modern Flask-based web app with integrated Phase 1 + Phase 2 pricing engine
"""

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import os
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np
import json

from pricing_engine import PricingEngine
from pricing_engine_v2 import HybridPricingEngine
from demand_engine import DemandPredictionModel, PriceOptimizer
from cost_manager import CostManager


def convert_numpy_types(obj):
    """Convert NumPy types to native Python types for JSON serialization"""
    # Handle NumPy arrays FIRST (before scalar checks)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    # Handle NumPy scalars
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    # Handle pandas types
    elif isinstance(obj, (pd.Timestamp, pd.Timedelta)):
        return str(obj)
    # Check for NaN values (only for scalar values, not arrays)
    elif not isinstance(obj, (dict, list, tuple)) and pd.isna(obj):
        return None
    # Handle collections
    elif isinstance(obj, dict):
        return {str(key): convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_numpy_types(item) for item in obj]
    # Handle other NumPy types (fallback)
    elif hasattr(obj, 'item'):  # NumPy scalar
        try:
            return obj.item()
        except (ValueError, AttributeError):
            return obj
    return obj

app = Flask(__name__)
CORS(app)

# Initialize engines
BASE_DIR = Path(__file__).parent
CSV_DIR = BASE_DIR.parent

# Load Cost Manager (Phase 4: Profit Optimization)
cost_config_path = BASE_DIR / 'data' / 'cost_config.json'
cost_manager = None
if cost_config_path.exists():
    try:
        cost_manager = CostManager(cost_config_path=str(cost_config_path))
        print("Cost Manager loaded - Profit-aware pricing active!")
    except Exception as e:
        print(f"Warning: Could not load Cost Manager: {e}")
        print("Pricing will continue without profit constraints.")
else:
    print("Cost config not found. Generating default cost estimates...")
    try:
        from generate_cost_config import generate_cost_config
        generate_cost_config(csv_dir=str(CSV_DIR), output_path=str(cost_config_path))
        cost_manager = CostManager(cost_config_path=str(cost_config_path))
        print("Cost Manager initialized with default estimates.")
    except Exception as e:
        print(f"Warning: Could not generate cost config: {e}")

# Phase 1 engine (always available)
phase1_engine = PricingEngine(csv_dir=str(CSV_DIR), cost_manager=cost_manager)
phase1_engine.load_data()
phase1_engine.compute_benchmarks()
phase1_engine.compute_vpi()

# Phase 2 engine (if model available)
phase2_engine = None
demand_model = None
phase2_available = False
model_path = BASE_DIR / 'models' / 'demand_model.joblib'

if model_path.exists():
    try:
        demand_model = DemandPredictionModel()
        demand_model.load(str(model_path))
        
        # Create PriceOptimizer with cost_manager for profit optimization
        price_optimizer = PriceOptimizer(demand_model, cost_manager=cost_manager)
        
        phase2_engine = HybridPricingEngine(
            csv_dir=str(CSV_DIR),
            demand_model=demand_model,
            use_demand_optimization=True,
            cost_manager=cost_manager
        )
        phase2_engine.load_data()
        phase2_engine.compute_benchmarks()
        phase2_engine.compute_vpi()
        phase2_available = True
        if cost_manager:
            print("Phase 2 + Phase 4 engine loaded - AI-powered demand & profit optimization active!")
        else:
            print("Phase 2 engine loaded successfully - AI-powered demand optimization active!")
    except Exception as e:
        print(f"Warning: Could not load Phase 2 engine: {e}")
        import traceback
        traceback.print_exc()
else:
    print("Phase 2 model not found - using Phase 1 (Market Benchmarking) only")

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/favicon.ico')
def favicon():
    """Serve favicon - return 204 No Content to suppress 404 errors"""
    return '', 204

@app.route('/api/venues')
def get_venues():
    """Get list of all venues"""
    venues = phase1_engine.df['venue'].unique().tolist()
    return jsonify(venues)

@app.route('/api/products')
def get_products():
    """Get products for a venue"""
    venue = request.args.get('venue')
    if not venue:
        return jsonify({'error': 'venue parameter required'}), 400
    
    products = phase1_engine.df[phase1_engine.df['venue'] == venue][
        ['bottle', 'type', 'price']
    ].to_dict('records')
    
    return jsonify(products)

@app.route('/api/status')
def get_status():
    """Get system status"""
    return jsonify({
        'phase2_available': phase2_available,
        'phase': 2 if phase2_available else 1
    })

@app.route('/api/market-analysis')
def get_market_analysis():
    """Get market analysis data"""
    vpi_data = [
        {'venue': str(venue), 'vpi': float(vpi), 'premium_pct': float((vpi - 1) * 100)}
        for venue, vpi in phase1_engine.venue_vpi.items()
    ]
    
    type_medians = [
        {'type': str(k), 'median_price': float(v)}
        for k, v in sorted(phase1_engine.type_medians.items(), key=lambda x: x[1], reverse=True)
    ]
    
    try:
        result = {
            'vpi': vpi_data,
            'type_medians': type_medians,
            'global_median': float(phase1_engine.global_avg_price),
            'phase2_available': phase2_available
        }
        
        # Convert NumPy types
        result_clean = convert_numpy_types(result)
        return jsonify(result_clean)
    except Exception as e:
        print(f"Error in market-analysis: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/recommendations', methods=['POST'])
def get_recommendations():
    """Get price recommendations"""
    data = request.json
    venue = data.get('venue')
    bottle = data.get('bottle')
    bottle_type = data.get('type')
    current_price = float(data.get('price', 0))
    
    # Demand signals (optional)
    day_of_week = data.get('day_of_week')
    hour = data.get('hour')
    is_weekend = data.get('is_weekend')
    event_type = data.get('event_type', 'regular')
    inventory_level = data.get('inventory_level', 1.0)
    
    if not all([venue, bottle, bottle_type, current_price]):
        return jsonify({'error': 'Missing required parameters'}), 400
    
    # Try Phase 2 first, fall back to Phase 1
    if phase2_engine:
        try:
            rec = phase2_engine.recommend_price_v2(
                venue=venue,
                bottle=bottle,
                bottle_type=bottle_type,
                current_price=current_price,
                day_of_week=day_of_week,
                hour=hour,
                is_weekend=is_weekend,
                event_type=event_type,
                inventory_level=inventory_level
            )
            rec['phase'] = 2
            # Convert NumPy types to native Python types
            rec_clean = convert_numpy_types(rec)
            return jsonify(rec_clean)
        except Exception as e:
            print(f"Phase 2 recommendation failed: {e}")
            import traceback
            traceback.print_exc()
    
    # Fall back to Phase 1
    rec = phase1_engine.recommend_price(
        venue=venue,
        bottle=bottle,
        bottle_type=bottle_type,
        current_price=current_price
    )
    rec['phase'] = 1
    # Convert NumPy types to native Python types
    rec_clean = convert_numpy_types(rec)
    return jsonify(rec_clean)

@app.route('/api/bulk-recommendations', methods=['POST'])
def get_bulk_recommendations():
    """Get recommendations for all products"""
    try:
        data = request.json or {}
        venue = data.get('venue') or None
        
        # Demand signals
        day_of_week = data.get('day_of_week')
        hour = data.get('hour')
        is_weekend = data.get('is_weekend')
        event_type = data.get('event_type', 'regular')
        inventory_level = data.get('inventory_level', 1.0)
        
        # Filter by venue if specified
        if venue:
            df = phase1_engine.df[phase1_engine.df['venue'] == venue].copy()
        else:
            df = phase1_engine.df.copy()
        
        if len(df) == 0:
            return jsonify([])
        
        recommendations = []
        
        for idx, row in df.iterrows():
            try:
                venue_name = str(row['venue'])
                bottle_name = str(row['bottle'])
                bottle_type = str(row['type'])
                current_price = float(row['price'])
                
                if phase2_engine and phase2_available:
                    try:
                        rec = phase2_engine.recommend_price_v2(
                            venue=venue_name,
                            bottle=bottle_name,
                            bottle_type=bottle_type,
                            current_price=current_price,
                            day_of_week=day_of_week,
                            hour=hour,
                            is_weekend=is_weekend,
                            event_type=event_type,
                            inventory_level=inventory_level
                        )
                        rec['phase'] = 2
                    except Exception as e:
                        # Fall back to Phase 1
                        rec = phase1_engine.recommend_price(
                            venue=venue_name,
                            bottle=bottle_name,
                            bottle_type=bottle_type,
                            current_price=current_price
                        )
                        rec['phase'] = 1
                else:
                    # Use Phase 1 only
                    rec = phase1_engine.recommend_price(
                        venue=venue_name,
                        bottle=bottle_name,
                        bottle_type=bottle_type,
                        current_price=current_price
                    )
                    rec['phase'] = 1
                
                # Convert NumPy types to native Python types
                rec_clean = convert_numpy_types(rec)
                recommendations.append(rec_clean)
            except Exception as e:
                print(f"Error processing row {idx}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        return jsonify(recommendations)
    except Exception as e:
        print(f"Error in bulk-recommendations: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/demand-prediction', methods=['POST'])
def predict_demand():
    """Predict demand at different price points"""
    try:
        if not demand_model:
            return jsonify({'error': 'Demand model not available'}), 503
        
        data = request.json or {}
        venue = data.get('venue')
        bottle = data.get('bottle')
        bottle_type = data.get('type')
        
        if not all([venue, bottle, bottle_type]):
            return jsonify({'error': 'Missing required parameters: venue, bottle, type'}), 400
        
        # Demand signals
        day_of_week = data.get('day_of_week', datetime.now().weekday())
        hour = data.get('hour', datetime.now().hour)
        is_weekend = data.get('is_weekend', datetime.now().weekday() >= 4)
        event_type = data.get('event_type', 'regular')
        inventory_level = data.get('inventory_level', 1.0)
        
        # Test price range
        current_price = float(data.get('price', 300))
        price_range = [current_price * (0.7 + i * 0.05) for i in range(13)]  # 70% to 130%
        
        predictions = []
        for price in price_range:
            try:
                demand = demand_model.predict(
                    price=float(price),
                    venue=str(venue),
                    bottle=str(bottle),
                    bottle_type=str(bottle_type),
                    day_of_week=int(day_of_week) if day_of_week is not None else None,
                    hour=int(hour) if hour is not None else None,
                    is_weekend=bool(is_weekend) if is_weekend is not None else None,
                    event_type=str(event_type),
                    inventory_level=float(inventory_level)
                )
                # Ensure all values are native Python types
                pred = {
                    'price': float(round(price, 2)),
                    'predicted_demand': float(round(float(demand), 1)),
                    'revenue': float(round(float(price) * float(demand), 2))
                }
                predictions.append(pred)
            except Exception as e:
                print(f"Error predicting at price ${price}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        if not predictions:
            return jsonify({'error': 'No predictions generated'}), 500
        
        # Convert NumPy types to native Python types (double-check)
        predictions_clean = convert_numpy_types(predictions)
        return jsonify(predictions_clean)
    except Exception as e:
        print(f"Error in demand-prediction: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')

