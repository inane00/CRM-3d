from models import db, OrderLog

def log_order_creation(order):
    """Логирует создание заказа."""
    log = OrderLog(
        order_id=order.id,
        field_name='created',
        old_value='',
        new_value='Заказ создан'
    )
    db.session.add(log)
    # Не делаем commit здесь, чтобы можно было сгруппировать с основным коммитом

def log_order_update(order, old_data, new_data):
    """
    Логирует изменения полей заказа.
    old_data и new_data — словари с ключами-названиями полей.
    """
    for field in old_data.keys():
        old_val = old_data.get(field)
        new_val = new_data.get(field)
        if old_val != new_val:
            log = OrderLog(
                order_id=order.id,
                field_name=field,
                old_value=str(old_val) if old_val is not None else '',
                new_value=str(new_val) if new_val is not None else ''
            )
            db.session.add(log)

def log_order_deletion(order):
    """Логирует удаление заказа с сохранением информации."""
    log = OrderLog(
        order_id=order.id,  # пока id ещё существует
        field_name='deleted',
        old_value='',
        new_value='Заказ удалён',
        deleted_order_info=f"#{order.id} ({order.model_name})"  # сохраняем имя
    )
    db.session.add(log)