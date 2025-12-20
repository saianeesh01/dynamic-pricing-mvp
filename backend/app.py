from flask import Flask, jsonify, request
from flask_cors import CORS
from models import db, Product, PricingRule
import os

app = Flask(__name__)
CORS(app)

# Configuration
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'pricing.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()
    # Seed data if empty
    if not Product.query.first():
        p1 = Product(name="Premium Vodka Bottle", base_price=100.0, current_price=100.0, inventory_count=50)
        p2 = Product(name="VIP Table Access", base_price=500.0, current_price=500.0, inventory_count=5)
        db.session.add_all([p1, p2])
        
        # Add basic rules
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

@app.route('/calculate-price/<int:product_id>', methods=['POST'])
def calculate_price(product_id):
    product = Product.query.get_or_404(product_id)
    rules = PricingRule.query.filter_by(is_active=True).all()
    
    new_price = product.base_price
    
    # Very basic rule engine application
    for rule in rules:
        if rule.rule_type == 'inventory_low' and product.inventory_count < 10:
            new_price *= rule.adjustment_factor
            
    product.current_price = round(new_price, 2)
    db.session.commit()
    
    return jsonify(product.to_dict())

if __name__ == '__main__':
    app.run(debug=True, port=5000)
