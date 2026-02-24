import os
import time
from werkzeug.utils import secure_filename
from flask import current_app


# Разрешённые расширения файлов
ALLOWED_EXTENSIONS = {'stl', 'obj'}

def allowed_file(filename):
    # Проверяет, имеет ли файл допустимое расширение.
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_unique_filename(filename):
    # Генерирует уникальное имя файла, добавляя временную метку.
    name, ext = os.path.splitext(filename)
    # Заменяем пробелы и небезопасные символы через secure_filename
    safe_name = secure_filename(name)
    timestamp = int(time.time())
    return f"{safe_name}_{timestamp}{ext}"

def save_uploaded_file(file):
    """
    Сохраняет загруженный файл в папку UPLOAD_FOLDER.
    Возвращает относительный путь к файлу (например, 'uploads/имя_файла.ext')
    или None в случае ошибки.
    """
    if file and allowed_file(file.filename):
        # Генерируем безопасное уникальное имя
        filename = get_unique_filename(file.filename)
        # Формируем полный путь для сохранения
        upload_folder = current_app.config['UPLOAD_FOLDER']
        file_path = os.path.join(upload_folder, filename)
        # Сохраняем файл
        file.save(file_path)
        # Возвращаем путь относительно корня приложения (для хранения в БД)
        return os.path.join('uploads', filename)
    return None

def delete_file(file_path):
    """Удаляет файл по относительному пути (если существует)."""
    if file_path:
        full_path = os.path.join(current_app.root_path, file_path)
        if os.path.exists(full_path):
            os.remove(full_path)
            return True
    return False

# Опционально: функция для извлечения веса из STL
def get_weight_from_stl(file_path, density=1.24):
    """
    Анализирует STL-файл и возвращает примерный вес в граммах.
    density — плотность материала (г/см³), по умолчанию для PLA.
    """
    try:
        from stl import mesh
        # Загружаем mesh из файла
        stl_mesh = mesh.Mesh.from_file(file_path)
        # Получаем объём (в единицах модели, обычно мм³)
        volume = stl_mesh.get_mass_properties()[0]
        # Переводим в см³ (1 см³ = 1000 мм³)
        volume_cm3 = volume / 1000.0
        # Вес = объём * плотность
        weight = volume_cm3 * density
        return round(weight, 2)
    except ImportError:
        # Если библиотека не установлена, возвращаем None
        return None
    except Exception as e:
        # Логируем ошибку, но не прерываем выполнение
        print(f"Ошибка при анализе STL: {e}")
        return None