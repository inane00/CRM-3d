// static/js/calc.js

// Ждём полной загрузки DOM
document.addEventListener('DOMContentLoaded', function () {
    // Находим нужные элементы
    const materialSelect = document.getElementById('material_id');
    const weightInput = document.getElementById('weight');
    const priceField = document.getElementById('calculated_price');

    // Если какой-то элемент не найден (например, мы не на странице заказа), выходим
    if (!materialSelect || !weightInput || !priceField) return;

    // Функция для обновления цены
    function updatePrice() {
        const materialId = materialSelect.value;
        const weight = weightInput.value;

        // Проверяем, что оба поля заполнены и вес больше 0
        if (!materialId || !weight || parseFloat(weight) <= 0) {
            priceField.value = '';
            return;
        }

        // Формируем URL с параметрами запроса
        const url = `/calculate_price?weight=${encodeURIComponent(weight)}&material_id=${encodeURIComponent(materialId)}`;

        // Отправляем GET-запрос через Fetch API
        fetch(url)
            .then(response => {
                // Проверяем, что ответ успешный (статус 200-299)
                if (!response.ok) {
                    throw new Error('Ошибка сервера');
                }
                return response.json(); // парсим JSON
            })
            .then(data => {
                if (data.price) {
                    priceField.value = data.price.toFixed(2) + ' руб.';
                } else {
                    priceField.value = 'Ошибка';
                }
            })
            .catch(error => {
                console.error('Ошибка при расчёте цены:', error);
                priceField.value = 'Ошибка';
            });
    }

    // Добавляем обработчики событий: при изменении материала или вводе веса
    materialSelect.addEventListener('change', updatePrice);
    weightInput.addEventListener('input', updatePrice); // input срабатывает при каждом вводе
});