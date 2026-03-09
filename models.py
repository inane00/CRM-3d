from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Client(db.Model):
    __tablename__ = 'clients'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    telegram = db.Column(db.String(100))
    
    # Связь с заказами (односторонняя, обратная ссылка создаётся в Order)
    orders = db.relationship('Order', back_populates='client', lazy=True)

class Material(db.Model):
    __tablename__ = 'materials'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    price_per_gram = db.Column(db.Float, nullable=False)
    
    # Связь с заказами
    orders = db.relationship('Order', back_populates='material', lazy=True)

class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    model_name = db.Column(db.String(200))
    weight = db.Column(db.Float)
    material_id = db.Column(db.Integer, db.ForeignKey('materials.id'))
    total_price = db.Column(db.Float)
    status = db.Column(db.String(50), default='new')
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    file_path = db.Column(db.String(300))
    
    # Явные двунаправленные связи
    client = db.relationship('Client', back_populates='orders')
    material = db.relationship('Material', back_populates='orders')

class OrderLog(db.Model):
    __tablename__ = 'order_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    field_name = db.Column(db.String(50))        # название изменённого поля
    old_value = db.Column(db.String(500))        # старое значение (в виде строки)
    new_value = db.Column(db.String(500))        # новое значение
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    # user_id можно добавить позже, когда будет аутентификация
    
    # связь с заказом
    order = db.relationship('Order', backref='logs')


class CalculatorSettings(db.Model):
    __tablename__ = 'calculator_settings'
    
    id = db.Column(db.Integer, primary_key=True)  # всегда будет id=1
    electricity_cost_per_kwh = db.Column(db.Float, default=5.0)  # стоимость электричества, руб/кВт*ч
    printing_time_hours_per_gram = db.Column(db.Float, default=0.01)  # время печати 1 грамма (в часах)
    tax_percent = db.Column(db.Float, default=4.0)  # налог, % от себестоимости
    consumables_percent = db.Column(db.Float, default=5.0)  # расходники, % от себестоимости
    depreciation_percent = db.Column(db.Float, default=10.0)  # амортизация, % от себестоимости
    profit_percent = db.Column(db.Float, default=20.0)  # прибыль, % от себестоимости с налогом