# pricing.py
# Модуль для расчёта стоимости заказов 3D-печати

from models import db, Material, CalculatorSettings, ServiceParameter

def calculate_final_price(material_id, weight, order=None, services=None):
    """
    Рассчитывает итоговую цену с учётом глобальных/индивидуальных настроек
    и дополнительных услуг (покраска, срочность и т.д.)
    
    Аргументы:
        material_id: ID материала
        weight: вес модели в граммах
        order: объект Order (для индивидуальных настроек, может быть None)
        services: список словарей с полями service_id, custom_value
    
    Возвращает:
        float: итоговая цена в рублях
    """
    material = db.session.get(Material, material_id)
    if not material:
        return None

    # 1. Получаем настройки (глобальные или из заказа)
    settings = _get_settings(order)
    
    # 2. Базовый расчёт себестоимости
    plastic_cost = weight * material.price_per_gram
    electricity_cost = weight * settings['printing_time_hours_per_gram'] * settings['electricity_cost']
    base_cost = plastic_cost + electricity_cost
    consumables = base_cost * settings['consumables_percent'] / 100
    depreciation = base_cost * settings['depreciation_percent'] / 100
    cost_with_tax = (base_cost + consumables + depreciation) * (1 + settings['tax_percent'] / 100)
    final_price = cost_with_tax * (1 + settings['profit_percent'] / 100)
    
    # 3. Добавляем стоимость дополнительных услуг
    services_total = _calculate_services_cost(services, weight, final_price)
    
    return round(final_price + services_total, 2)


def calculate_price_breakdown(material_id, weight, order=None, services=None):
    """
    Возвращает детальную разбивку цены для отображения пользователю.
    
    Возвращает словарь с компонентами цены:
    {
        'plastic_cost': float,
        'electricity_cost': float,
        'consumables': float,
        'depreciation': float,
        'tax': float,
        'profit': float,
        'services': [{'name': str, 'amount': float}, ...],
        'total': float
    }
    """
    material = db.session.get(Material, material_id)
    if not material:
        return None
    
    settings = _get_settings(order)
    
    plastic_cost = weight * material.price_per_gram
    electricity_cost = weight * settings['printing_time_hours_per_gram'] * settings['electricity_cost']
    base_cost = plastic_cost + electricity_cost
    consumables = base_cost * settings['consumables_percent'] / 100
    depreciation = base_cost * settings['depreciation_percent'] / 100
    cost_with_tax = (base_cost + consumables + depreciation) * (1 + settings['tax_percent'] / 100)
    tax = cost_with_tax - (base_cost + consumables + depreciation)
    profit = cost_with_tax * settings['profit_percent'] / 100
    final_price = cost_with_tax + profit
    
    # Разбивка по услугам
    services_breakdown = []
    if services:
        for svc_data in services:
            service = db.session.get(ServiceParameter, svc_data['service_id'])
            if service and service.is_active:
                value = svc_data.get('custom_value', service.value)
                if service.calculation_type == 'per_gram':
                    amount = value * weight
                elif service.calculation_type == 'percent':
                    amount = final_price * value / 100
                else:  # fixed
                    amount = value
                services_breakdown.append({
                    'name': service.name,
                    'amount': round(amount, 2)
                })
    
    return {
        'plastic_cost': round(plastic_cost, 2),
        'electricity_cost': round(electricity_cost, 2),
        'consumables': round(consumables, 2),
        'depreciation': round(depreciation, 2),
        'tax': round(tax, 2),
        'profit': round(profit, 2),
        'services': services_breakdown,
        'total': round(final_price + sum(s['amount'] for s in services_breakdown), 2)
    }


def _get_settings(order=None):
    """
    Внутренняя функция: возвращает настройки расчёта.
    Если передан order с use_custom_settings=True, использует индивидуальные настройки.
    Иначе возвращает глобальные настройки из CalculatorSettings.
    """
    # Получаем глобальные настройки
    global_settings = CalculatorSettings.query.get(1)
    if not global_settings:
        global_settings = CalculatorSettings(id=1)
        db.session.add(global_settings)
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            global_settings = CalculatorSettings.query.get(1)
    
    # Базовые глобальные значения
    default_settings = {
        'electricity_cost': global_settings.electricity_cost_per_kwh,
        'tax_percent': global_settings.tax_percent,
        'profit_percent': global_settings.profit_percent,
        'consumables_percent': global_settings.consumables_percent,
        'depreciation_percent': global_settings.depreciation_percent,
        'printing_time_hours_per_gram': global_settings.printing_time_hours_per_gram
    }
    
    # Если есть индивидуальные настройки, заменяем только те, что заданы
    if order and hasattr(order, 'use_custom_settings') and order.use_custom_settings:
        result = default_settings.copy()
        
        # Заменяем только те поля, которые явно заданы (не None)
        if order.custom_electricity_cost is not None:
            result['electricity_cost'] = order.custom_electricity_cost
        if order.custom_tax_percent is not None:
            result['tax_percent'] = order.custom_tax_percent
        if order.custom_profit_percent is not None:
            result['profit_percent'] = order.custom_profit_percent
        if order.custom_consumables_percent is not None:
            result['consumables_percent'] = order.custom_consumables_percent
        if order.custom_depreciation_percent is not None:
            result['depreciation_percent'] = order.custom_depreciation_percent
        
        return result
    
    return default_settings


def _calculate_services_cost(services, weight, base_price):
    """
    Внутренняя функция: рассчитывает стоимость всех выбранных услуг.
    """
    if not services:
        return 0
    
    total = 0
    for svc_data in services:
        service = db.session.get(ServiceParameter, svc_data['service_id'])
        if service and service.is_active:
            value = svc_data.get('custom_value', service.value)
            if service.calculation_type == 'per_gram':
                total += value * weight
            elif service.calculation_type == 'percent':
                total += base_price * value / 100
            elif service.calculation_type == 'fixed':
                total += value
    return total