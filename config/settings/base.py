
from pathlib import Path
from dotenv import load_dotenv
import os
from datetime import timedelta
from apps.custom_admin.custom_admin import *
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
SECRET_KEY = os.environ.get('SECRET_KEY')
DEBUG = False
ALLOWED_HOSTS = []


SUMMERNOTE_CONFIG = {
    'iframe': True,  # use iframe mode
    'toolbar': [
        ['style', ['style']],
        ['font', ['bold', 'italic', 'underline', 'clear']],
        ['fontname', ['fontname']],
        ['color', ['color']],
        ['para', ['ul', 'ol', 'paragraph']],
        ['table', ['table']],
        ['insert', ['link']],
        ['view', ['fullscreen', 'codeview']],
    ],
}


# Optional but handy defaults
TINYMCE_DEFAULT_CONFIG = {
    "height": 420,
    "menubar": True,
    "plugins": "advlist autolink lists link image charmap preview anchor "
               "searchreplace visualblocks code fullscreen insertdatetime media "
               "table help wordcount",
    "toolbar": "undo redo | styles | bold italic underline | alignleft aligncenter alignright alignjustify | "
               "bullist numlist outdent indent | link image media | table | code | preview",
    "block_formats": "Paragraph=p; Heading 2=h2; Heading 3=h3",
    "content_style": "body {font-family: -apple-system, Segoe UI, Roboto, Arial, sans-serif;}",
    "branding": False,
}


# Application definition
INSTALLED_APPS = [
    "unfold",
    
    # 'jet',
    # 'daisyui_dashboard',
    # "admin_interface",
    # "colorfield",
    
    # Django core apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party apps (uncomment/add as needed)
    'rest_framework',
    'rest_framework_simplejwt',
    # 'django.contrib.sites',  # Required by allauth
    'corsheaders',
    # 'allauth',
    'allauth.account',
    # 'allauth.socialaccount',
    'whitenoise.runserver_nostatic',
    # 'django_celery_beat',
    # 'schema_viewer',
    'django_filters',
    # 'django_celery_beat',
    "channels",
    
    "tinymce",
    # Local apps (your custom apps - modify for each project)
    'apps.core',
    'apps.auths',
    'apps.file_uploader',
    'apps.contacts',
    'apps.notification',
    'apps.chat',
    'django_summernote',
    'apps.custom_home',
    # Food delivery apps
    'apps.merchant',
    'apps.customer',
    'apps.rider',
    'apps.orders',
    'apps.admin_panel',
]

X_FRAME_OPTIONS = "SAMEORIGIN"              # allows you to use modals insated of popups
SILENCED_SYSTEM_CHECKS = ["security.W019"]  # ignores redundant warning messages

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Static files serving
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # CORS handling
    'django.middleware.common.CommonMiddleware',
    "django.middleware.csrf.CsrfViewMiddleware",
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',  # Django-allauth
    'django.middleware.gzip.GZipMiddleware',  # gzip compression for performance
    # 'debug_toolbar.middleware.DebugToolbarMiddleware',  ##Uncomment for debug toolbar
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "apps/templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.notification.context_processors.notification_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Custom User Model (uncomment and modify as needed)
AUTH_USER_MODEL = 'auths.CustomUser'


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Authentication backends
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# Django-allauth settings
SITE_ID = 1
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# Session configuration
SESSION_COOKIE_AGE = 3600  # 1 hour


# Media files configuration
# Option 1: Local media files (development)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Option 2: AWS S3/DigitalOcean Spaces (production)
AWS_S3_ENDPOINT_URL = os.getenv(
    'AWS_S3_ENDPOINT_URL', 'https://nyc3.digitaloceanspaces.com')
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',
    'ACL': 'public-read',
}
if AWS_STORAGE_BUCKET_NAME:
    MEDIA_URL = f'{AWS_S3_ENDPOINT_URL}/{AWS_STORAGE_BUCKET_NAME}/'

# Paystack payment gateway
PAYSTACK_SECRET_KEY = os.getenv('PAYSTACK_SECRET_KEY', '')
PAYSTACK_PUBLIC_KEY = os.getenv('PAYSTACK_PUBLIC_KEY', '')

# Email configuration

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp-relay.brevo.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False  # important for Brevo on 587

EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')

DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL')   # "Putt putt play <Juan@puttputtplay.com>"
CONTACT_EMAIL = os.getenv('CONTACT_EMAIL')  

# SMS gateway configuration (Twilio - works internationally)
TWILIO_ENABLED = os.getenv('TWILIO_ENABLED', 'true').lower() in ('true', '1', 'yes')
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN', '')
TWILIO_FROM_NUMBER = os.getenv('TWILIO_FROM_NUMBER', '')



# Django REST Framework configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.AllowAny',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    'EXCEPTION_HANDLER': 'apps.core.utils.custom_exception_handler.custom_exception_handler',
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ]
}

# Simple JWT configuration
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=5),  # Adjust as needed
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),


}
BASE_URL = os.getenv('BASE_URL')

# CORS configuration (base settings - will be overridden)
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = []
CSRF_TRUSTED_ORIGINS = []

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

CORS_ALLOW_METHODS = [
    'GET',
    'POST',
    'PUT',
    'DELETE',
    'PATCH',
    'OPTIONS'
]

# Payment gateways
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
STRIPE_PUBLIC_KEY = os.getenv('STRIPE_PUBLIC_KEY')
# STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')

#paypal 
PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET")
PAYPAL_MODE = os.getenv("PAYPAL_MODE")

PAYPAL_RETURN_URL = 'http://localhost:8000/api/v1/payment/checkout/paypal/confirm/'
PAYPAL_CANCEL_URL = 'http://localhost:8000/api/v1/payment/checkout/paypal/cancel/'


# Password hashers
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
]


# Celery configuration (for background tasks)
CELERY_BROKER_URL = 'redis://redis:6379/0'
CELERY_RESULT_BACKEND = 'redis://redis:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'




# ====
ASGI_APPLICATION = 'config.asgi.application'
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            # 'redis' is the service name in docker-compose
            "hosts": [('redis', 6379)],
        },
    },
}


# Static files configuration
STATIC_URL = '/static/'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
STATICFILES_DIRS = [BASE_DIR / 'static']  # must be a list or tuple
STATIC_ROOT = BASE_DIR / 'staticfiles'  # optional but needed for collectstatic