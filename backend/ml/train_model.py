import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error
import joblib
import os

def train_model():
    # Load data
    df = pd.read_csv('data/historical_pricing.csv')
    
    # Features and Target
    X = df[['hour', 'day_of_week', 'inventory_level', 'bartender_load']]
    y = df['target_multiplier']
    
    # Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Train
    # Using RandomForest for non-linear relationships (Peak hours + Day)
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    # Evaluate
    predictions = model.predict(X_test)
    mae = mean_absolute_error(y_test, predictions)
    print(f"Model trained. Mean Absolute Error: {mae:.4f}")
    
    # Save
    os.makedirs('models', exist_ok=True)
    joblib.dump(model, 'models/pricing_model.joblib')
    print("Model saved to models/pricing_model.joblib")

if __name__ == "__main__":
    train_model()
