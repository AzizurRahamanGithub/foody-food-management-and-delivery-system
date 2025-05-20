# debug_settings.py
# Create this file in your project root and run it

import pathlib
import os
from dotenv import load_dotenv

# Try loading .env from different locations
print("=== CHECKING .env FILE LOCATIONS ===")

# Check project root
if os.path.exists('.env'):
    print("✅ .env found in project root (CORRECT)")
    load_dotenv()
else:
    print("❌ .env NOT found in project root")

# Check settings directory
if os.path.exists('config/settings/.env'):
    print("⚠️  .env found in config/settings/ (WRONG LOCATION)")
else:
    print("✅ No .env in config/settings/ (good)")

print(f"\n=== ENVIRONMENT VARIABLES ===")
print(f"DJANGO_ENVIRONMENT: {os.getenv('DJANGO_ENVIRONMENT')}")
print(f"SECRET_KEY exists: {bool(os.getenv('SECRET_KEY'))}")
print(f"Working directory: {os.getcwd()}")

# Check file structure
config_dir = pathlib.Path('config')
print(f"\n=== FILE STRUCTURE ===")
print(f"config/ exists: {config_dir.exists()}")
# Should be False
print(f"config/settings.py exists: {(config_dir / 'settings.py').exists()}")
# Should be True
print(f"config/settings/ exists: {(config_dir / 'settings').exists()}")
print(
    f"config/settings/__init__.py exists: {(config_dir / 'settings' / '__init__.py').exists()}")

# List files in settings directory
settings_dir = config_dir / 'settings'
if settings_dir.exists():
    print(f"\n=== FILES IN config/settings/ ===")
    for file in settings_dir.iterdir():
        print(f"  {file.name}")

# Test Django settings loading
try:
    print(f"\n=== TESTING DJANGO SETTINGS ===")
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    import django
    django.setup()
    from django.conf import settings

    print(f"✅ Settings loaded successfully")
    print(f"Settings module: {settings.SETTINGS_MODULE}")
    print(f"DEBUG: {settings.DEBUG}")
    print(f"Database engine: {settings.DATABASES['default']['ENGINE']}")
    print(f"Environment: {os.getenv('DJANGO_ENVIRONMENT')}")

except Exception as e:
    print(f"❌ Error loading settings: {e}")
    import traceback
    traceback.print_exc()
