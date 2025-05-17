"""
Django settings for autodocpro project.

Production-ready configuration with security best practices.
"""

from pathlib import Path
import os
import socket
import logging
from datetime import timedelta
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Базовые пути проекта
BASE_DIR = Path(__file__).resolve().parent.parent

# ==================== НАСТРОЙКИ БЕЗОПАСНОСТИ ====================
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY and os.getenv('DEBUG') == 'True':
    SECRET_KEY = 'django-insecure-dev-key-only'  # Только для разработки
elif not SECRET_KEY:
    raise ValueError("SECRET_KEY must be set in production")

DEBUG = os.getenv('DEBUG', 'False') == 'True'

# Обработка ALLOWED_HOSTS и CSRF_TRUSTED_ORIGINS
DEFAULT_ALLOWED_HOSTS = ['127.0.0.1', 'localhost']
PRODUCTION_HOST = os.getenv('RAILWAY_STATIC_URL', 'web-production-a798.up.railway.app')
if PRODUCTION_HOST:
    DEFAULT_ALLOWED_HOSTS.append(PRODUCTION_HOST)

allowed_hosts = os.getenv('ALLOWED_HOSTS', '').split(',')
ALLOWED_HOSTS = [host.strip() for host in allowed_hosts if host.strip()] or DEFAULT_ALLOWED_HOSTS

DEFAULT_CSRF_TRUSTED_ORIGINS = []
if PRODUCTION_HOST:
    DEFAULT_CSRF_TRUSTED_ORIGINS.append(f'https://{PRODUCTION_HOST}')

csrf_origins = os.getenv('CSRF_TRUSTED_ORIGINS', '').split(',')
CSRF_TRUSTED_ORIGINS = [
    origin.strip() for origin in csrf_origins 
    if origin.strip() and (
        origin.startswith('http://') or 
        origin.startswith('https://')
    )
] or DEFAULT_CSRF_TRUSTED_ORIGINS

SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'True') == 'True'
CSRF_COOKIE_SECURE = os.getenv('CSRF_COOKIE_SECURE', 'True') == 'True'

# ==================== НАСТРОЙКИ ПРИЛОЖЕНИЙ ====================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    'rest_framework',
    'whitenoise.runserver_nostatic',
    'documents.apps.DocumentsConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
    INTERNAL_IPS = ['127.0.0.1']
    hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
    INTERNAL_IPS += [ip[:-1] + '1' for ip in ips]

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

# ==================== НАСТРОЙКИ БАЗЫ ДАННЫХ ====================
# Основные настройки базы данных
DATABASES = {
    'default': {
        'ENGINE': os.getenv('DB_ENGINE', 'django.db.backends.sqlite3'),
        'NAME': os.getenv('DB_NAME', BASE_DIR / 'db.sqlite3'),
        'USER': os.getenv('DB_USER', ''),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', ''),
        'PORT': os.getenv('DB_PORT', ''),
    }
}

# Альтернативная настройка через DATABASE_URL (для Railway и других платформ)
if os.getenv('DATABASE_URL'):
    try:
        import dj_database_url
        db_from_env = dj_database_url.config(conn_max_age=600)
        DATABASES['default'].update(db_from_env)
    except ImportError:
        logging.warning("dj-database-url package not found. Using standard database configuration.")

# ==================== ОСНОВНЫЕ НАСТРОЙКИ ====================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True

# ==================== СТАТИЧЕСКИЕ ФАЙЛЫ И MEDIA ====================
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Настройки WhiteNoise
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ==================== НАСТРОЙКИ API ====================
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
if not DEEPSEEK_API_KEY and not DEBUG:
    raise ValueError("DEEPSEEK_API_KEY must be set in production")

DEEPSEEK_API_URL = os.getenv('DEEPSEEK_API_URL', 'https://api.deepseek.com/v1')
DEEPSEEK_MODEL = os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')
DEEPSEEK_MAX_RETRIES = int(os.getenv('DEEPSEEK_MAX_RETRIES', 3))
DEEPSEEK_TIMEOUT = int(os.getenv('DEEPSEEK_TIMEOUT', 30))

AI_CONFIG = {
    'CACHE_TIMEOUT': timedelta(hours=int(os.getenv('AI_CACHE_HOURS', 24))),
    'MAX_TOKENS': int(os.getenv('AI_MAX_TOKENS', 4000)),
    'TEMPERATURE': float(os.getenv('AI_TEMPERATURE', 0.7)),
    'DOCUMENT_TEMPERATURE': float(os.getenv('AI_DOCUMENT_TEMPERATURE', 0.3)),
}

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer' if DEBUG else None,
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'deepseek_api': '5/minute',
    },
}
# Удаляем None из RENDERER_CLASSES
REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = [
    r for r in REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] if r is not None
]

# ==================== ЛОГИРОВАНИЕ ====================
LOGGING_DIR = BASE_DIR / 'logs'
LOGGING_DIR.mkdir(exist_ok=True)

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
            'formatter': 'verbose',
        },
        'file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGGING_DIR / 'django.log',
            'maxBytes': 1024 * 1024 * 5,  # 5 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'documents': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
    },
}

# ==================== PRODUCTION SETTINGS ====================
if not DEBUG:
    # Security
    SECURE_HSTS_SECONDS = 3600
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    
    # Whitenoise optimization
    WHITENOISE_MANIFEST_STRICT = False
    WHITENOISE_MAX_AGE = 31536000  # 1 year
    
    # Database permissions
    db_path = BASE_DIR / 'db.sqlite3'
    if db_path.exists():
        try:
            db_path.chmod(0o644)
        except PermissionError as e:
            logging.getLogger('django').warning(f"Could not set database permissions: {e}")
