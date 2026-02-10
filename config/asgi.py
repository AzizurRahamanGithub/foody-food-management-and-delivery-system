
import os
import django
from django.core.asgi import get_asgi_application
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set correct settings module based on environment
environment = os.getenv("DJANGO_ENVIRONMENT", "development")
if environment == "production":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")
else:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

# Setup Django BEFORE importing anything else
django.setup()

# Get the Django ASGI application early to ensure apps are loaded
django_asgi_app = get_asgi_application()

# NOW import the Django Channels components AFTER django.setup()
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from apps.chat.middleware import JWTAuthMiddleware
from apps.chat import routing as chat_routing
from apps.orders import routing as orders_routing

# Main ASGI application with JWT middleware
application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        JWTAuthMiddleware(
            URLRouter(
                chat_routing.websocket_urlpatterns +
                orders_routing.websocket_urlpatterns
            )
        )
    ),
})
