from .base import *
DEBUG = True
ALLOWED_HOSTS = ['*']
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

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
]


STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_ROOT = BASE_DIR / 'media'

# Local Redis for dev (base.py points to docker service name 'redis')
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [('127.0.0.1', 6379)],
        },
    },
}

SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False



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

print("🧑‍💻🛠️🔧Development settings loaded")
