# models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Создаём объект db, который будет связывать SQLAlchemy с нашим Flask-приложением
db = SQLAlchemy()

# Модель для клиентов
class Client(db.Model):
    __tablename__ = 'clients'  # имя таблицы в базе данных (необязательно, по умолчанию будет 'client')
    
    id = db.Column(db.Integer, primary_key=True)  # первичный ключ, автоинкремент
    name = db.Column(db.String(100), nullable=False)  # имя клиента, обязательное поле
    phone = db.Column(db.String(20))  # телефон, может быть пустым
    email = db.Column(db.String(100))
    telegram = db.Column(db.String(100))
    
    # Связь с заказами: один клиент может иметь много заказов.
    # backref создаст поле 'client' в модели Order, через которое можно получить объект клиента.
    # lazy=True означает, что данные заказов будут загружаться только при обращении (экономит память).
    orders = db.relationship('Order', backref='client', lazy=True)

# Модель для материалов
class Material(db.Model):
    __tablename__ = 'materials'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)  # название материала, должно быть уникальным
    price_per_gram = db.Column(db.Float, nullable=False)  # цена за грамм, обязательное поле
    
    # Связь с заказами: один материал может использоваться во многих заказах.
    orders = db.relationship('Order', backref='material_ref', lazy=True)  # backref назовём material_ref, чтобы избежать путаницы

# Модель для заказов
class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)  # внешний ключ на clients.id
    model_name = db.Column(db.String(200))  # название модели
    weight = db.Column(db.Float)  # вес в граммах
    material_id = db.Column(db.Integer, db.ForeignKey('materials.id'))  # внешний ключ на materials.id
    total_price = db.Column(db.Float)  # итоговая стоимость заказа (рассчитывается как weight * price)
    status = db.Column(db.String(50), default='new')  # статус: new, printing, ready, delivered
    date_created = db.Column(db.DateTime, default=datetime.utcnow)  # дата создания, по умолчанию текущее время UTC
    file_path = db.Column(db.String(300))  # путь к загруженному файлу (опционально)
    
    # Определяем связь с материалом как объект (для удобства доступа)
    # material = db.relationship('Material')  # можно не писать, если используем backref, но для ясности добавим
    # Мы уже создали backref='material_ref' в Material, поэтому можем обращаться order.material_ref.
    # Чтобы было проще, переопределим:
    material = db.relationship('Material')  # это даст нам order.material