
import os
from django.core.wsgi import get_wsgi_application
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set correct settings module based on environment
environment = os.getenv('DJANGO_ENVIRONMENT', 'development')
if environment == 'production':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
else:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

application = get_wsgi_application()
