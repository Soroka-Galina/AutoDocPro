import os
from pathlib import Path
import socket
from datetime import timedelta

# ===== Инициализация настроек =====
BASE_DIR = Path(__file__).resolve().parent.parent

print("\n=== Инициализация настроек ===")
print("Используются системные переменные окружения")

# ===== Проверка обязательных переменных =====
def get_required_env(var_name):
    value = os.getenv(var_name)
    if not value:
        raise ValueError(f"Необходимо установить переменную окружения: {var_name}")
    return value

DJANGO_SECRET_KEY = get_required_env('DJANGO_SECRET_KEY')
DEEPSEEK_API_KEY = get_required_env('DEEPSEEK_API_KEY')

DEBUG = os.getenv('DJANGO_DEBUG', 'False').lower() == 'true'

# ===== Основные настройки Django =====
ALLOWED_HOSTS = [
    'web-production-a798.up.railway.app',
    '.railway.app',
    'localhost',
    '127.0.0.1',
    '[::1]',
]

CSRF_TRUSTED_ORIGINS = [
    'https://web-production-a798.up.railway.app',
    'https://*.railway.app',
    'http://localhost',
    'http://127.0.0.1',
]

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
    INTERNAL_IPS = ['127.0.0.1', 'localhost']
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

# ===== Настройки базы данных (SQLite для MVP) =====
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Для работы на Railway с SQLite
if os.environ.get('RAILWAY_ENVIRONMENT'):
    # Создаем директорию для базы данных, если ее нет
    db_dir = BASE_DIR / 'data'
    if not db_dir.exists():
        db_dir.mkdir()
    
    DATABASES['default']['NAME'] = db_dir / 'db.sqlite3'

# ===== Настройки аутентификации =====
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ===== Локализация =====
LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True

# ===== Статические файлы =====
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ===== Настройки DeepSeek API =====
DEEPSEEK_API_URL = os.getenv('DEEPSEEK_API_URL', 'https://api.deepseek.com/v1')
DEEPSEEK_API_VERSION = os.getenv('DEEPSEEK_API_VERSION', 'v1')
DEEPSEEK_MODEL = os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')
DEEPSEEK_MAX_RETRIES = int(os.getenv('DEEPSEEK_MAX_RETRIES', '3'))
DEEPSEEK_TIMEOUT = int(os.getenv('DEEPSEEK_TIMEOUT', '30'))

# ===== Настройки ИИ =====
AI_CONFIG = {
    'CACHE_TIMEOUT': timedelta(hours=int(os.getenv('AI_CACHE_HOURS', '24'))),
    'MAX_TOKENS': int(os.getenv('AI_MAX_TOKENS', '4000')),
    'TEMPERATURE': float(os.getenv('AI_TEMPERATURE', '0.7')),
    'DOCUMENT_TEMPERATURE': float(os.getenv('AI_DOCUMENT_TEMPERATURE', '0.3')),
}

# ===== Настройки REST Framework =====
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer' if DEBUG else None,
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
        'deepseek_api': '5/minute',
    },
}

# Удаляем None из списка рендереров
REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = [r for r in REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] if r is not None]

# ===== Настройки безопасности для production =====
if not DEBUG:
    SECURE_HSTS_SECONDS = 3600
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'

print("=== Настройки успешно загружены ===\n")
