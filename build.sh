#!/bin/bash
# build.sh - Скрипт для сборки Django-проекта на Render.com

# Выход при ошибке любой команды
set -o errexit
set -o pipefail
set -o nounset

echo "=== Начало процесса сборки ==="

# 1. Установка зависимостей
echo "Установка Python-зависимостей..."
pip install -r requirements.txt

# 2. Проверка подключения к БД (опционально)
echo "Проверка подключения к базе данных..."
python -c "
import django
django.setup()
from django.db import connection
try:
    connection.ensure_connection()
    print('✓ Успешное подключение к БД')
except Exception as e:
    print('✗ Ошибка подключения к БД:', str(e))
    raise
"

# 3. Создание миграций
echo "Создание миграций..."
python manage.py makemigrations || {
    echo "⚠ Ошибка при создании миграций. Продолжение без новых миграций..."
}

# 4. Применение миграций
echo "Применение миграций к базе данных..."
python manage.py migrate --noinput || {
    echo "❌ Критическая ошибка: не удалось применить миграции"
    exit 1
}

# 5. Сбор статических файлов (для production)
echo "Сбор статических файлов..."
python manage.py collectstatic --noinput --clear || {
    echo "⚠ Ошибка при сборе статических файлов"
}

# 6. Дополнительные команды (если нужно)
# Например, создание суперпользователя или загрузка фикстур
# echo "Создание суперпользователя..."
# python manage.py createsuperuser --noinput || true

echo "=== Сборка успешно завершена ==="