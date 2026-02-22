import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent



DEBUG = False
SECRET_KEY = '%uzn0c&q-%lcp^ycvdg$05xtsp=7-lup6h&gs5p%5u^&n8n@_v'

ALLOWED_HOSTS = ['creativebarbershop.pythonanywhere.com', '127.0.0.1', 'localhost']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # 3rd party
    'rest_framework',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.telegram',

    # Mening ilovalarim
    'users',
    'services',
    'masters',
    'schedule',
    'appointments',
    'payments',
    'subscriptions',
    'reviews',
    'notifications',
    'api',
    'telegrambot',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'barbershop.urls'

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

WSGI_APPLICATION = 'barbershop.wsgi.application'

# Ma'lumotlar bazasi (SQLite – soddalik uchun)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')  # collectstatic yig'adigan papka
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),  # sizning asl statik fayllaringiz
]


MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'users.User'

# Allauth sozlamalari
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']
ACCOUNT_FORMS = {
    'signup': 'users.forms.CustomSignupForm',
}
ACCOUNT_ADAPTER = 'users.adapters.CustomAccountAdapter'

SOCIALACCOUNT_PROVIDERS = {
    'telegram': {
        'APP': {
            'client_id': 'YOUR_BOT_TOKEN',  # Telegram bot tokeningiz
            'secret': '',
        },
        'METHOD': 'oauth2',
    }
}

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
}

# Telegram bot token
TELEGRAM_BOT_TOKEN = '8517155781:AAEC0x2RM2XCz7_fg5uDixs0omyEtBhlopc'

# Celery (agar kerak boʻlsa)
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

# SMS Aero sozlamalari
SMSAERO_EMAIL = 'abubakirmavlyanov2403@gmail.com'
SMSAERO_API_KEY = 'JWLg5cncVBfn4gQIGR1zpAj9Uejo4IbW'
SMSAERO_SIGN = 'Creative Barbershop'


# # YooKassa (agar kerak boʻlsa)
# YOOKASSA_SHOP_ID = 'your_shop_id'
# YOOKASSA_SECRET_KEY = 'your_secret_key'

# Async xavfsizlik (agar kerak boʻlsa)
import os
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
