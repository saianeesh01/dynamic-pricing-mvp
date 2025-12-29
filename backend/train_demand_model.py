"""
Train Phase 2 demand prediction model.

This script:
1. Generates or loads demand history data
2. Trains XGBoost model to predict bottles_sold
3. Saves model for use in pricing engine
"""

import pandas as pd
import os
from pathlib import Path
from demand_engine import DemandPredictionModel
from generate_demand_data import generate_demand_data


def main():
    data_path = Path(__file__).parent / 'data' / 'demand_history.csv'
    model_path = Path(__file__).parent / 'models' / 'demand_model.joblib'
    
    # Generate or load data
    if not data_path.exists():
        print("Demand history not found. Generating synthetic data...")
        df = generate_demand_data(n_samples=5000, output_path=str(data_path))
    else:
        print(f"Loading demand history from {data_path}")
        df = pd.read_csv(data_path)
    
    print(f"\nLoaded {len(df)} records")
    print(f"Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"Total bottles sold: {df['bottles_sold'].sum():,.0f}")
    
    # Train model
    print("\nTraining demand prediction model...")
    model = DemandPredictionModel()
    metrics = model.train(df, target_col='bottles_sold')
    
    print("\nTraining Results:")
    print(f"  Train MAE: {metrics['train_mae']:.2f} bottles")
    print(f"  Test MAE: {metrics['test_mae']:.2f} bottles")
    print(f"  Train RMSE: {metrics['train_rmse']:.2f} bottles")
    print(f"  Test RMSE: {metrics['test_rmse']:.2f} bottles")
    
    print("\nTop 10 Feature Importances:")
    sorted_features = sorted(
        metrics['feature_importance'].items(),
        key=lambda x: x[1],
        reverse=True
    )[:10]
    for feature, importance in sorted_features:
        print(f"  {feature}: {importance:.4f}")
    
    # Save model
    os.makedirs(model_path.parent, exist_ok=True)
    model.save(str(model_path))
    
    print(f"\n[SUCCESS] Model saved to {model_path}")
    print("\nNext steps:")
    print("  1. Use pricing_engine_v2.py for hybrid pricing")
    print("  2. Or integrate into existing pricing engine")


if __name__ == "__main__":
    main()


