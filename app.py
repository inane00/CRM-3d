# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from models import db, Client, Material, Order
from flask import Flask
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
import os
from file_utils import save_uploaded_file, delete_file, get_weight_from_stl, allowed_file
from flask import send_from_directory, abort


# Создаём экземпляр Flask-приложения
app = Flask(__name__)

# Конфигурация приложения
# SECRET_KEY нужен для защиты сессий и flash-сообщений. В реальном проекте его хранят в переменных окружения.
app.config['SECRET_KEY'] = 'your-secret-key-here'  # замените на случайную строку

# URI базы данных: указываем SQLite и имя файла. Будет создан файл instance/crm.db
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///crm.db'

# Отключаем сигнализацию об изменениях (чтобы не тратить ресурсы)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Инициализируем БД с нашим приложением
db.init_app(app)

app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'uploads') # Настройка пути к папке 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Ограничение максимального размера файла (16 MB)
# Проверка, что папка uploads существует
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Создаём таблицы, если их ещё нет
# Для этого используем контекст приложения
with app.app_context():
    db.create_all()
    # Добавим начальные материалы, если таблица пуста
    if not Material.query.first():
        db.session.add(Material(name='PLA', price_per_gram=0.05))
        db.session.add(Material(name='ABS', price_per_gram=0.06))
        db.session.add(Material(name='PETG', price_per_gram=0.07))
        db.session.commit()
        print("Материалы добавлены в БД")  # для отладки

# --- Маршруты (endpoints) ---

# Главная страница - список всех заказов
@app.route('/')
def index():
    # Получаем все заказы из БД, сортируем по дате создания (новые сверху)
    orders = Order.query.order_by(Order.date_created.desc()).all()
    # Передаём список заказов в шаблон index.html
    return render_template('index.html', orders=orders)

# --- Маршруты для клиентов ---

# Список клиентов
@app.route('/clients')
def client_list():
    clients = Client.query.all()
    return render_template('client_list.html', clients=clients)

# Добавление нового клиента (GET - показать форму, POST - сохранить)
@app.route('/client/new', methods=['GET', 'POST'])
def new_client():
    if request.method == 'POST':
        # Получаем данные из формы
        name = request.form['name']
        phone = request.form['phone']
        email = request.form['email']
        telegram = request.form['telegram']
        
        # Создаём объект Client
        client = Client(name=name, phone=phone, email=email, telegram=telegram)
        
        # Добавляем в сессию БД и сохраняем
        db.session.add(client)
        db.session.commit()
        
        # flash-сообщение (будет показано на следующей странице)
        flash('Клиент успешно добавлен', 'success')
        return redirect(url_for('client_list'))
    
    # GET-запрос: просто показываем форму
    return render_template('client_form.html', client=None)

# Редактирование клиента
@app.route('/client/<int:id>/edit', methods=['GET', 'POST'])
def edit_client(id):
    client = Client.query.get_or_404(id)  # если клиент не найден, вернётся 404 ошибка
    if request.method == 'POST':
        client.name = request.form['name']
        client.phone = request.form['phone']
        client.email = request.form['email']
        client.telegram = request.form['telegram']
        db.session.commit()
        flash('Клиент обновлён', 'success')
        return redirect(url_for('client_list'))
    
    # GET: передаём клиента в форму, чтобы поля были предзаполнены
    return render_template('client_form.html', client=client)

# Удаление клиента
@app.route('/client/<int:id>/delete')
def delete_client(id):
    client = Client.query.get_or_404(id)
    db.session.delete(client)
    db.session.commit()
    flash('Клиент удалён', 'warning')
    return redirect(url_for('client_list'))

# --- Маршруты для заказов ---

# Создание нового заказа
@app.route('/order/new', methods=['GET', 'POST'])
def new_order():
    if request.method == 'POST':
        # Получаем данные формы
        client_id = request.form['client_id']
        model_name = request.form['model_name']
        material_id = request.form['material_id']
        status = request.form['status']

        # Обработка веса из формы
        weight_str = request.form.get('weight', '')
        weight = None
        if weight_str:
            try:
                weight = float(weight_str)
            except ValueError:
                flash('Некорректное значение веса', 'danger')
                # Возвращаем форму с уже введёнными данными
                clients = Client.query.all()
                materials = Material.query.all()
                return render_template('order_form.html', order=None, clients=clients, materials=materials)

        # Обработка файла
        file = request.files.get('model_file')
        file_path = None
        if file and file.filename:
            if allowed_file(file.filename):
                file_path = save_uploaded_file(file)  # теперь это только имя
                if not file_path:
                    flash('Ошибка при сохранении файла.', 'danger')
            else:
                flash('Недопустимый тип файла. Разрешены только STL и OBJ.', 'danger')
                clients = Client.query.all()
                materials = Material.query.all()
                return render_template('order_form.html', order=None, clients=clients, materials=materials)

        # Если загружен STL, пытаемся вычислить вес (перезаписываем weight)
        if file_path and file_path.lower().endswith('.stl'):
            full_path = os.path.join(app.config['UPLOAD_FOLDER'], file_path)  # правильный путь
            calculated_weight = get_weight_from_stl(full_path)
            if calculated_weight:
                weight = calculated_weight
                flash(f'Вес автоматически рассчитан: {weight} г', 'info')

        # Проверка, что вес определён
        if weight is None:
            flash('Необходимо указать вес или загрузить STL-файл для авторасчёта', 'danger')
            clients = Client.query.all()
            materials = Material.query.all()
            return render_template('order_form.html', order=None, clients=clients, materials=materials)

        # Получаем материал и рассчитываем цену
        material = db.session.get(Material, material_id)
        if not material:
            flash('Материал не найден', 'danger')
            return redirect(url_for('new_order'))
        total_price = weight * material.price_per_gram

        # Создаём заказ
        order = Order(
            client_id=client_id,
            model_name=model_name,
            material_id=material_id,
            weight=weight,
            file_path=file_path,
            total_price=total_price,
            status=status
        )
        db.session.add(order)
        db.session.commit()

        # Отладочная информация (можно удалить)
        print(f"FILE: {file.filename if file else 'None'}")
        print(f"FILE_PATH: {file_path}")
        print(f"WEIGHT: {weight}")

        flash('Заказ создан', 'success')
        return redirect(url_for('index'))

    # GET-запрос
    clients = Client.query.all()
    materials = Material.query.all()
    return render_template('order_form.html', order=None, clients=clients, materials=materials)

# Редактирование заказа
@app.route('/order/<int:id>/edit', methods=['GET', 'POST'])
def edit_order(id):
    order = Order.query.get_or_404(id)
    if request.method == 'POST':
        order.client_id = request.form['client_id']
        order.model_name = request.form['model_name']
        order.material_id = request.form['material_id']
        order.weight = float(request.form['weight'])
        order.status = request.form['status']
        
        # Обработка нового файла
        file = request.files.get('model_file')
        if file and file.filename:
            if allowed_file(file.filename):
                if order.file_path:
                    delete_file(order.file_path)  # удаляем старый файл
                new_path = save_uploaded_file(file)  # новое имя
                order.file_path = new_path
                if new_path and new_path.lower().endswith('.stl'):
                    full_path = os.path.join(app.config['UPLOAD_FOLDER'], new_path)
                    calculated_weight = get_weight_from_stl(full_path)
                    if calculated_weight:
                        order.weight = calculated_weight
            else:
                flash('Недопустимый тип файла. Файл не сохранён.', 'danger')

        # Пересчитываем цену
        material = db.session.get(Material, order.material_id)
        order.total_price = order.weight * material.price_per_gram
        
        db.session.commit()
        flash('Заказ обновлён', 'success')
        return redirect(url_for('index'))
    
    clients = Client.query.all()
    materials = Material.query.all()
    return render_template('order_form.html', order=order, clients=clients, materials=materials)

# Удаление заказа
@app.route('/order/<int:id>/delete')
def delete_order(id):
    order = Order.query.get_or_404(id)
    if order.file_path:
        delete_file(order.file_path)
    db.session.delete(order)
    db.session.commit()
    flash('Заказ удалён', 'warning')
    return redirect(url_for('index'))

# --- AJAX-маршрут для расчёта цены ---
@app.route('/calculate_price')
def calculate_price():
    # Получаем параметры из запроса (вес и id материала)
    weight = request.args.get('weight', type=float)
    material_id = request.args.get('material_id', type=int)
    
    # Проверяем, что параметры переданы и корректны
    if not weight or not material_id:
        return jsonify({'error': 'Missing data'}), 400
    
    material = db.session.get(Material, material_id)
    if not material:
        return jsonify({'error': 'Material not found'}), 404
    
    price = weight * material.price_per_gram
    # Возвращаем JSON-ответ
    return jsonify({'price': round(price, 2)})

# Маршрут для скачивания файлов
@app.route('/uploads/<path:filename>')
def download_file(filename):
    """Отдаёт файл для скачивания."""
    # Здесь можно добавить проверку прав доступа (например, только для авторизованных)
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

# Админ-панель
admin = Admin(app, name='CRM Admin')
admin.add_view(ModelView(Client, db.session))
admin.add_view(ModelView(Order, db.session))
admin.add_view(ModelView(Material, db.session))

# Запуск приложения (только при прямом вызове скрипта)
if __name__ == '__main__':
    app.run(debug=True)  # debug=True позволяет автоматически перезагружать сервер при изменениях кода