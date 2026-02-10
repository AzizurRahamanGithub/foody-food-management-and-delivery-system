from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
import multiprocessing
from celery.schedules import crontab

# Set default Django settings module for Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Create Celery app
app = Celery('config')

# Configure Celery using Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()

# Set multiprocessing start method
multiprocessing.set_start_method('spawn', force=True)

@app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery."""
    print(f'Request: {self.request!r}')
    
    
# settings.py
CELERY_BEAT_SCHEDULE = {
    'publish-daily-inspirations': {
        'task': 'apps.daily_inspiration.tasks.publish_scheduled_inspirations',
        'schedule': crontab(hour=6, minute=0),  # 6 AM daily
    },
}