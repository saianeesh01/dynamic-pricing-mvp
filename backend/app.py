from flask import Flask, jsonify, request
from flask_cors import CORS
from models import db, Product, PricingRule
import os
import joblib
import pandas as pd
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Configuration
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'pricing.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Load ML Model
MODEL_PATH = os.path.join(BASE_DIR, 'models', 'pricing_model.joblib')
model = None
try:
    if os.path.exists(MODEL_PATH):
        model = joblib.load(MODEL_PATH)
        print("ML Model loaded successfully.")
except Exception as e:
    print(f"Error loading model: {e}")

class PricingLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    old_price = db.Column(db.Float)
    new_price = db.Column(db.Float)
    multiplier = db.Column(db.Float)
    reason = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "product_id": self.product_id,
            "old_price": self.old_price,
            "new_price": self.new_price,
            "multiplier": self.multiplier,
            "reason": self.reason,
            "timestamp": self.timestamp.isoformat()
        }

with app.app_context():
    db.create_all()
    # Seed products if empty
    if not Product.query.first():
        p1 = Product(name="Premium Vodka Bottle", base_price=100.0, current_price=100.0, inventory_count=50)
        p2 = Product(name="VIP Table Access", base_price=500.0, current_price=500.0, inventory_count=5)
        db.session.add_all([p1, p2])
    
    # Seed pricing rules if empty (independent of product seeding)
    if not PricingRule.query.first():
        r1 = PricingRule(name="Low Inventory Surplus", rule_type="inventory_low", adjustment_factor=1.2)
        db.session.add(r1)
    
    db.session.commit()

@app.route('/products', methods=['GET'])
def get_products():
    products = Product.query.all()
    return jsonify([p.to_dict() for p in products])

@app.route('/rules', methods=['GET'])
def get_rules():
    rules = PricingRule.query.all()
    return jsonify([r.to_dict() for r in rules])

@app.route('/pricing-logs', methods=['GET'])
def get_pricing_logs():
    logs = PricingLog.query.order_by(PricingLog.timestamp.desc()).limit(10).all()
    return jsonify([l.to_dict() for l in logs])

@app.route('/calculate-price/<int:product_id>', methods=['POST'])
def calculate_price(product_id):
    product = Product.query.get_or_404(product_id)
    old_price = product.current_price
    
    # Inputs for ML
    now = datetime.now()
    hour = now.hour
    day_of_week = now.weekday()
    inventory_level = min(1.0, product.inventory_count / 100.0) # Assume 100 is max
    bartender_load = 0.5 # Simulated default
    
    multiplier = 1.0
    reason = "Standard Pricing"
    
    if model:
        # Predict using ML
        input_data = pd.DataFrame([[hour, day_of_week, inventory_level, bartender_load]], 
                                 columns=['hour', 'day_of_week', 'inventory_level', 'bartender_load'])
        multiplier = float(model.predict(input_data)[0])
        reason = "AI-Driven Optimization"
    else:
        # Fallback to rules
        rules = PricingRule.query.filter_by(is_active=True).all()
        for rule in rules:
            if rule.rule_type == 'inventory_low' and product.inventory_count < 10:
                multiplier *= rule.adjustment_factor
                reason = "Rule-based: Low Inventory"

    # Apply Ethical Guardrails (PRD: max +20% / max -15%)
    multiplier = max(0.85, min(1.20, multiplier))
    
    new_price = round(product.base_price * multiplier, 2)
    product.current_price = new_price
    
    # Log the change
    log = PricingLog(
        product_id=product.id,
        old_price=old_price,
        new_price=new_price,
        multiplier=round(multiplier, 2),
        reason=reason
    )
    db.session.add(log)
    db.session.commit()
    
    response = product.to_dict()
    response['ai_multiplier'] = round(multiplier, 2)
    response['reason'] = reason
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
