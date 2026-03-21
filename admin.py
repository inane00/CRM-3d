from flask_admin.contrib.sqla import ModelView
from models import db, Client, Material, Order, OrderLog

class OrderLogView(ModelView):
    column_list = ('order', 'field_name', 'old_value', 'new_value', 'timestamp')
    column_labels = {
        'order': 'Заказ',
        'field_name': 'Поле',
        'old_value': 'Старое значение',
        'new_value': 'Новое значение',
        'timestamp': 'Время'
    }
    column_default_sort = ('timestamp', True)
    column_searchable_list = ('field_name', 'old_value', 'new_value')
    column_filters = ('order_id', 'field_name', 'timestamp')
    can_create = False
    can_edit = False
    can_delete = False
    column_formatters = {
        'order': lambda v, c, m, p: f"Заказ #{m.order.id} ({m.order.model_name})" if m.order else ''
    }

def register_admin_views(admin):
    admin.add_view(ModelView(Client, db.session))
    admin.add_view(ModelView(Order, db.session))
    admin.add_view(ModelView(Material, db.session))
    admin.add_view(OrderLogView(OrderLog, db.session))