
import os
from .base import *

# CRITICAL: Production MUST have DEBUG = False
DEBUG = False

# Database: Use PostgreSQL for production
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('POSTGRES_DB'),
        'USER': os.environ.get('POSTGRES_USER'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD'),
        'HOST': os.environ.get('DB_HOST', 'db'),  # 'db' for Docker
        'PORT': os.environ.get('DB_PORT', '5432'),
        # Performance optimizations
        'CONN_MAX_AGE': 60,
        'OPTIONS': {
            'connect_timeout': 10,
        }
    }
}

# Static files for production
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')


# Production allowed hosts (IMPORTANT: Only allow your domains)
ALLOWED_HOSTS = ['*']

CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',      
    'http://localhost:3001',      
    'http://localhost:5173',      
    'http://localhost:8080',      
    'http://127.0.0.1:5500',      
    'http://127.0.0.1:5501',      
    'http://127.0.0.1:8000',      
    'http://localhost:8000',      
    'http://172.252.13.75:7777',  
    'http://172.252.13.75:6543',  
    'http://172.252.13.75:6724',  
    'http://172.252.13.75:8083',  
    'http://206.162.244.143:6741',
    'http://127.0.0.1:8000',
    'http://31.97.99.135:8000',
    'https://puttputtplay.com',
    'https://api.puttputtplay.com',
]

CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8000',
    'http://127.0.0.1:5500',
    'http://127.0.0.1:5501',
    'http://127.0.0.1:8000',
    'http://localhost:3000',
    'http://localhost:5173',
    'http://172.252.13.75:7777',  
    'http://172.252.13.75:6543',  
    'http://172.252.13.75:6724',  
    'http://172.252.13.75:8083',  
    'http://206.162.244.143:6741',
    'http://127.0.0.1:8000',
    'http://31.97.99.135:8000',
    'https://puttputtplay.com',
    'https://api.puttputtplay.com',
]



# Update DRF settings for production
REST_FRAMEWORK.update({
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.UserRateThrottle',
        'rest_framework.throttling.AnonRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'user': '1000/hour',  # Adjust based on your needs
        'anon': '100/hour',   # Adjust based on your needs
    },
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
})



# Logging configuration for development
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
    },
}


# Security headers
X_FRAME_OPTIONS = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True

print("✅ Production settings loaded")
