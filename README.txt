AutoDocPro
==========

Django-приложение для автоматизированного создания юридических документов с интеграцией DeepSeek AI.

Deploy на Render, адрес: https://autodocpro.onrender.com

Основные возможности:
- Генерация документов на основе шаблонов (HTML → PDF/DOCX)
- Интеграция с DeepSeek AI для обработки текста
- Динамические формы для заполнения данных
- Кэширование запросов к API
- Логирование всех операций

API Интеграция (DeepSeek)
-------------------------
Приложение использует DeepSeek API для обработки текста. Основные методы:

1. **Генерация текста**
   - Конечная точка: `chat/completions`
   - Параметры:
     * `prompt`: Текст запроса
     * `max_tokens`: Максимальное количество токенов (по умолчанию 2000)
     * `temperature`: Параметр креативности (0-1)

   Пример запроса:
   ```python
   response = DeepSeekIntegration.generate_text(
       prompt="Сформируйте юридическое заключение...",
       max_tokens=1500,
       temperature=0.7
   )


Структура проекта:
autodocpro/               # Основное приложение Django
├── documents/            # Модуль для работы с документами
│   ├── models.py         # Модели данных
│   ├── views.py          # Логика отображения
│   ├── forms.py          # Формы для ввода данных
│   ├── templates/        # Шаблоны документов
│   └── services.py       # Бизнес-логика
├── media/                # Загружаемые файлы
├── static/               # CSS/JS/изображения
├── templates/            # Базовые шаблоны
└── .env                  # Конфигурация окружения


Особенности реализации:
Автоматическое кэширование ответов (настройки в settings.py)
Логирование всех запросов в базу данных (модель AIRequestHistory)
Обработка ошибок с сохранением в лог-файлы
Таймаут запросов: 30 сек (настраивается)

Требования к API:
Обязательный заголовок: Authorization: Bearer {API_KEY}
Формат данных: JSON
Базовый URL: https://api.deepseek.com/v1/

Настройки API (в .env):
DEEPSEEK_API_KEY=your_api_key_here
DEEPSEEK_API_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_TIMEOUT=30
AI_CACHE_TIMEOUT=3600 # 1 час кэширования

Установка
---------
1. Клонируйте репозиторий:
   git clone [URL репозитория]

2. Создайте и активируйте виртуальное окружение:
   python -m venv Autodocpro_env
   .\Autodocpro_env\Scripts\activate

3. Установите зависимости:
   pip install -r requirements.txt

4. Настройте базу данных:
   python manage.py migrate

5. Создайте суперпользователя:
   python manage.py createsuperuser

6. Запустите сервер:
   python manage.py runserver

Зависимости
-----------
Основные зависимости (см. requirements.txt):
- Django>=4.2
- python-docx
- pdfkit
- django-environ

Использование
-------------
1. Откройте в браузере: http://localhost:8000/
2. Выберите тип документа (иск, заявление и т.д.)
3. Заполните форму данными
4. Сгенерируйте и скачайте документ

Доступные шаблоны:
- appeal_template.html - Шаблон апелляции
- claim_template.html - Шаблон искового заявления
- motion_template.html - Шаблон ходатайства

