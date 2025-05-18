# settings.py
from pathlib import Path
import os
import dj_database_url
from datetime import timedelta

# Базовые пути проекта
BASE_DIR = Path(__file__).resolve().parent.parent

# Настройки безопасности
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')  # Обязательно задайте в переменных окружения Render!
DEBUG = os.getenv('DJANGO_DEBUG', 'False') == 'True'  # На продакшене должно быть False
ALLOWED_HOSTS = ['autodocpro.onrender.com', 'localhost']  # Добавьте ваш домен Render

# Настройки приложений
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Сторонние приложения
    'rest_framework',
    
    # Локальные приложения
    'documents.apps.DocumentsConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Добавлено для статики на Render
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'autodocpro.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'autodocpro.wsgi.application'

# База данных (используем dj-database-url для Render)
DATABASES = {
    'default': dj_database_url.config(
        default=os.getenv('DATABASE_URL'),  # Автоматически разбирает строку подключения Render
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# Валидация паролей
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Локализация
LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True

# Статические файлы (настройки для Whitenoise)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Медиа файлы
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Настройки DeepSeek API
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')  # Обязательно через переменные окружения
DEEPSEEK_API_URL = os.getenv('DEEPSEEK_API_URL', 'https://api.deepseek.com/v1')
DEEPSEEK_API_VERSION = os.getenv('DEEPSEEK_API_VERSION', 'v1')
DEEPSEEK_MODEL = os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')
DEEPSEEK_MAX_RETRIES = int(os.getenv('DEEPSEEK_MAX_RETRIES', 3))
DEEPSEEK_TIMEOUT = int(os.getenv('DEEPSEEK_TIMEOUT', 30))

# Настройки ИИ
AI_CONFIG = {
    'CACHE_TIMEOUT': timedelta(hours=int(os.getenv('AI_CACHE_HOURS', 24))),  # 24 часа по умолчанию
    'MAX_TOKENS': int(os.getenv('AI_MAX_TOKENS', 4000)),
    'TEMPERATURE': float(os.getenv('AI_TEMPERATURE', 0.7)),
    'DOCUMENT_TEMPERATURE': float(os.getenv('AI_DOCUMENT_TEMPERATURE', 0.3)),  # Более строгие настройки для документов
}

# Настройки REST Framework
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'deepseek_api': '5/minute',  # Лимит запросов к API
    },
    'EXCEPTION_HANDLER': 'rest_framework.views.exception_handler',
}

# Настройки кэширования (Redis для продакшена)
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://localhost:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Настройки логирования (используем /tmp/ для Render)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG' if DEBUG else 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose' if DEBUG else 'simple',
        },
        'file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': '/tmp/django_errors.log',  # Используем /tmp/ для Render
            'formatter': 'verbose',
        },
        'deepseek_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/tmp/deepseek_api.log',  # Используем /tmp/ для Render
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'documents': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        'deepseek': {
            'handlers': ['console', 'deepseek_file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Отключение системных проверок
SILENCED_SYSTEM_CHECKS = [
    "files.W002",
    "urls.W002",
]
