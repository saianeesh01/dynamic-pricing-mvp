"""
Phase 2: Demand-Based Dynamic Pricing Engine

This engine predicts demand (bottles sold) at different price points and optimizes
pricing to maximize revenue = price × predicted_demand.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error
import joblib
import os
from pathlib import Path


class DemandPredictionModel:
    """
    XGBoost model to predict bottles sold given price and contextual features.
    """
    
    def __init__(self):
        self.model = None
        self.feature_names = None
        self.is_trained = False
        
    def train(
        self,
        df: pd.DataFrame,
        target_col: str = 'bottles_sold',
        test_size: float = 0.2,
        random_state: int = 42
    ) -> Dict:
        """
        Train XGBoost model to predict demand.
        
        Expected features in df:
        - price: Current price
        - venue: Venue name (categorical)
        - bottle: Bottle/brand name (categorical)
        - type: Alcohol type (categorical)
        - day_of_week: 0-6 (Monday-Sunday)
        - hour: 0-23 (hour of day)
        - is_weekend: 0 or 1
        - is_holiday: 0 or 1
        - event_type: Event type (DJ, regular, holiday, etc.)
        - inventory_level: 0-1 (inventory remaining / capacity)
        - month: 1-12
        - bottles_sold: Target variable (quantity sold)
        
        Returns:
            Dictionary with training metrics
        """
        # Prepare features
        feature_cols = [
            'price', 'day_of_week', 'hour', 'is_weekend', 'is_holiday',
            'inventory_level', 'month'
        ]
        
        # One-hot encode categorical features
        categorical_cols = ['venue', 'type', 'event_type']
        df_encoded = df.copy()
        
        for col in categorical_cols:
            if col in df.columns:
                dummies = pd.get_dummies(df[col], prefix=col, drop_first=False)
                # Clean column names (replace spaces, special chars) to match prediction
                dummies.columns = [c.replace(' ', '_').replace('&', '').replace("'", '').replace('-', '_').replace('+', '_') for c in dummies.columns]
                df_encoded = pd.concat([df_encoded, dummies], axis=1)
                feature_cols.extend(dummies.columns.tolist())
        
        # Filter to available features
        available_features = [f for f in feature_cols if f in df_encoded.columns]
        
        X = df_encoded[available_features]
        y = df_encoded[target_col]
        
        self.feature_names = available_features
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )
        
        # Train XGBoost model
        self.model = xgb.XGBRegressor(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=random_state,
            n_jobs=-1
        )
        
        self.model.fit(X_train, y_train)
        
        # Evaluate
        y_pred_train = self.model.predict(X_train)
        y_pred_test = self.model.predict(X_test)
        
        train_mae = mean_absolute_error(y_train, y_pred_train)
        test_mae = mean_absolute_error(y_test, y_pred_test)
        train_rmse = np.sqrt(mean_squared_error(y_train, y_pred_train))
        test_rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
        
        self.is_trained = True
        
        metrics = {
            'train_mae': train_mae,
            'test_mae': test_mae,
            'train_rmse': train_rmse,
            'test_rmse': test_rmse,
            'feature_importance': dict(zip(
                self.feature_names,
                self.model.feature_importances_
            ))
        }
        
        return metrics
    
    def predict(
        self,
        price: float,
        venue: str,
        bottle: str,
        bottle_type: str,
        day_of_week: int = None,
        hour: int = None,
        is_weekend: bool = None,
        is_holiday: bool = False,
        event_type: str = 'regular',
        inventory_level: float = 1.0,
        month: int = None
    ) -> float:
        """
        Predict bottles sold at given price and conditions.
        
        Returns:
            Predicted number of bottles sold (non-negative)
        """
        if not self.is_trained:
            raise ValueError("Model not trained. Call train() first.")
        
        # Set defaults
        if day_of_week is None:
            day_of_week = datetime.now().weekday()
        if hour is None:
            hour = datetime.now().hour
        if is_weekend is None:
            is_weekend = day_of_week >= 4  # Fri, Sat, Sun
        if month is None:
            month = datetime.now().month
        
        # Create feature vector
        features = pd.DataFrame({
            'price': [price],
            'day_of_week': [day_of_week],
            'hour': [hour],
            'is_weekend': [1 if is_weekend else 0],
            'is_holiday': [1 if is_holiday else 0],
            'inventory_level': [inventory_level],
            'month': [month]
        })
        
        # Add one-hot encoded categorical features
        # First, create all categorical feature columns and set to 0
        for feature_name in self.feature_names:
            if feature_name.startswith('venue_') or feature_name.startswith('type_') or feature_name.startswith('event_type_'):
                if feature_name not in features.columns:
                    features[feature_name] = [0]
        
        # Then set the appropriate ones to 1
        # Clean the input values to match how get_dummies processes them
        venue_clean = venue.replace(' ', '_').replace('&', '').replace("'", '').replace('-', '_')
        type_clean = bottle_type.replace(' ', '_').replace('&', '').replace("'", '').replace('-', '_')
        event_clean = event_type.replace(' ', '_').replace('&', '').replace("'", '').replace('-', '_')
        
        for feature_name in self.feature_names:
            if feature_name.startswith('venue_'):
                # Match venue name (handle spaces and special chars)
                if feature_name == f'venue_{venue_clean}':
                    features[feature_name] = [1]
            elif feature_name.startswith('type_'):
                if feature_name == f'type_{type_clean}':
                    features[feature_name] = [1]
            elif feature_name.startswith('event_type_'):
                if feature_name == f'event_type_{event_clean}':
                    features[feature_name] = [1]
        
        # Ensure all features are present
        for feature_name in self.feature_names:
            if feature_name not in features.columns:
                features[feature_name] = [0]
        
        # Reorder columns to match training
        features = features[self.feature_names]
        
        # Predict
        prediction = self.model.predict(features)[0]
        
        # Ensure non-negative and convert to native Python float
        return float(max(0.0, float(prediction)))
    
    def save(self, filepath: str):
        """Save model to file."""
        if not self.is_trained:
            raise ValueError("Model not trained. Cannot save.")
        
        model_data = {
            'model': self.model,
            'feature_names': self.feature_names
        }
        joblib.dump(model_data, filepath)
        print(f"Model saved to {filepath}")
    
    def load(self, filepath: str):
        """Load model from file."""
        model_data = joblib.load(filepath)
        self.model = model_data['model']
        self.feature_names = model_data['feature_names']
        self.is_trained = True
        print(f"Model loaded from {filepath}")


class PriceOptimizer:
    """
    Optimizes price to maximize revenue or profit.
    
    If cost_manager is provided, optimizes profit = (price - cost) × predicted_demand(price).
    Otherwise, optimizes revenue = price × predicted_demand(price).
    """
    
    def __init__(self, demand_model: DemandPredictionModel, cost_manager=None):
        self.demand_model = demand_model
        self.cost_manager = cost_manager
    
    def optimize_price(
        self,
        venue: str,
        bottle: str,
        bottle_type: str,
        current_price: float,
        min_price: float = None,
        max_price: float = None,
        price_step: float = 5.0,
        day_of_week: int = None,
        hour: int = None,
        is_weekend: bool = None,
        is_holiday: bool = False,
        event_type: str = 'regular',
        inventory_level: float = 1.0,
        month: int = None
    ) -> Dict:
        """
        Find optimal price that maximizes profit (if cost_manager available) or revenue.
        
        Returns:
            Dictionary with optimal price, predicted demand, revenue, profit, and alternatives
        """
        # Get cost if cost manager available
        cost = None
        if self.cost_manager:
            try:
                cost = self.cost_manager.get_cost(bottle, bottle_type, current_price)
            except Exception as e:
                print(f"Warning: Could not get cost for {bottle}: {e}")
        
        # Set price bounds
        if min_price is None:
            min_price = current_price * 0.7  # 30% discount max
        if max_price is None:
            max_price = current_price * 1.5  # 50% increase max
        
        # Adjust min_price to ensure profitability if cost_manager available
        if self.cost_manager and cost is not None:
            min_profit_price = self.cost_manager.get_minimum_price(cost)
            min_price = max(min_price, min_profit_price)
        
        # Grid search over price range
        price_range = np.arange(min_price, max_price + price_step, price_step)
        results = []
        
        for price in price_range:
            predicted_demand = self.demand_model.predict(
                price=price,
                venue=venue,
                bottle=bottle,
                bottle_type=bottle_type,
                day_of_week=day_of_week,
                hour=hour,
                is_weekend=is_weekend,
                is_holiday=is_holiday,
                event_type=event_type,
                inventory_level=inventory_level,
                month=month
            )
            
            revenue = price * predicted_demand
            
            # Calculate profit if cost available
            if cost is not None:
                profit = (price - cost) * predicted_demand
                profit_margin = self.cost_manager.calculate_profit_margin(price, cost)
                # Only consider profitable prices
                if profit_margin >= self.cost_manager.min_profit_margin_pct * 100:
                    results.append({
                        'price': price,
                        'predicted_demand': predicted_demand,
                        'revenue': revenue,
                        'profit': profit,
                        'profit_margin_pct': profit_margin,
                        'cost': cost
                    })
            else:
                results.append({
                    'price': price,
                    'predicted_demand': predicted_demand,
                    'revenue': revenue
                })
        
        if not results:
            # No profitable prices found, return current price info
            if cost is not None:
                return {
                    'optimal_price': current_price,
                    'optimal_demand': 0,
                    'optimal_revenue': 0,
                    'optimal_profit': 0,
                    'current_price': current_price,
                    'current_demand': 0,
                    'current_revenue': 0,
                    'current_profit': 0,
                    'error': 'No profitable prices found. Current price may be below cost.',
                    'cost': float(cost),
                    'min_profit_price': float(self.cost_manager.get_minimum_price(cost))
                }
            else:
                return {
                    'optimal_price': current_price,
                    'optimal_demand': 0,
                    'optimal_revenue': 0,
                    'current_price': current_price,
                    'current_demand': 0,
                    'current_revenue': 0,
                    'error': 'No valid prices found'
                }
        
        results_df = pd.DataFrame(results)
        
        # Find optimal price - maximize profit if cost available, otherwise revenue
        if cost is not None and 'profit' in results_df.columns:
            optimal_idx = results_df['profit'].idxmax()
            optimize_for = 'profit'
        else:
            optimal_idx = results_df['revenue'].idxmax()
            optimize_for = 'revenue'
        
        optimal = results_df.iloc[optimal_idx]
        
        # Get current revenue for comparison
        current_demand = self.demand_model.predict(
            price=current_price,
            venue=venue,
            bottle=bottle,
            bottle_type=bottle_type,
            day_of_week=day_of_week,
            hour=hour,
            is_weekend=is_weekend,
            is_holiday=is_holiday,
            event_type=event_type,
            inventory_level=inventory_level,
            month=month
        )
        current_revenue = current_price * current_demand
        current_profit = (current_price - cost) * current_demand if cost is not None else None
        
        # Convert all values to native Python types
        optimal_price = float(optimal['price'])
        optimal_demand = float(optimal['predicted_demand'])
        optimal_revenue = float(optimal['revenue'])
        optimal_profit = float(optimal.get('profit', optimal_revenue))
        optimal_profit_margin = float(optimal.get('profit_margin_pct', 0))
        current_demand_float = float(current_demand)
        current_revenue_float = float(current_revenue)
        current_profit_float = float(current_profit) if current_profit is not None else None
        
        # Convert price_range records - ensure all values are native Python types
        price_range_records = []
        for rec in results_df.to_dict('records'):
            clean_rec = {}
            for k, v in rec.items():
                # Only convert scalar numeric types, not arrays
                if isinstance(v, (int, float, np.integer, np.floating)):
                    clean_rec[k] = float(v)
                elif isinstance(v, np.ndarray):
                    # Should not happen, but handle it
                    clean_rec[k] = float(v.item()) if v.size == 1 else v.tolist()
                else:
                    clean_rec[k] = v
            price_range_records.append(clean_rec)
        
        result = {
            'optimal_price': optimal_price,
            'optimal_demand': optimal_demand,
            'optimal_revenue': optimal_revenue,
            'current_price': float(current_price),
            'current_demand': current_demand_float,
            'current_revenue': current_revenue_float,
            'revenue_improvement': float(optimal_revenue - current_revenue_float),
            'revenue_improvement_pct': float(((optimal_revenue - current_revenue_float) / current_revenue_float * 100) if current_revenue_float > 0 else 0),
            'price_change': float(optimal_price - current_price),
            'price_change_pct': float(((optimal_price - current_price) / current_price * 100)),
            'price_range': price_range_records,
            'optimize_for': optimize_for
        }
        
        # Add profit metrics if cost available
        if cost is not None:
            result.update({
                'cost': float(cost),
                'optimal_profit': optimal_profit,
                'optimal_profit_margin_pct': optimal_profit_margin,
                'current_profit': current_profit_float,
                'current_profit_margin_pct': float(self.cost_manager.calculate_profit_margin(current_price, cost)),
                'profit_improvement': float(optimal_profit - current_profit_float) if current_profit_float is not None else 0,
                'profit_improvement_pct': float(((optimal_profit - current_profit_float) / current_profit_float * 100) if current_profit_float and current_profit_float > 0 else 0),
                'min_profit_price': float(self.cost_manager.get_minimum_price(cost))
            })
        
        return result

