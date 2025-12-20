from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    base_price = db.Column(db.Float, nullable=False)
    current_price = db.Column(db.Float, nullable=False)
    inventory_count = db.Column(db.Integer, default=0)
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "base_price": self.base_price,
            "current_price": self.current_price,
            "inventory_count": self.inventory_count
        }

class PricingRule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    rule_type = db.Column(db.String(50), nullable=False) # e.g., 'inventory_low', 'time_of_day'
    adjustment_factor = db.Column(db.Float, nullable=False) # e.g., 1.10 for +10%
    is_active = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "rule_type": self.rule_type,
            "adjustment_factor": self.adjustment_factor,
            "is_active": self.is_active
        }
