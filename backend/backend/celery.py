"""
Celery application for asynchronous task processing.

The Celery app instance is created here.  It loads Django settings using
`CELERY_CONFIG_MODULE` and automatically discovers tasks across all installed
Django apps.  Celery uses Redis for both the broker and result backend by
default, but you can override these via environment variables.
"""
from __future__ import annotations

import os

from celery import Celery


# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

# Read the broker and result backend from environment variables.  If
# unspecified, default to a local Redis instance.  For production use, you
# should configure these via a `.env` file or your process manager.
broker_url = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
result_backend = os.getenv('CELERY_RESULT_BACKEND', broker_url)

app = Celery('backend', broker=broker_url, backend=result_backend)

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.  - namespace='CELERY' means
# all celery-related configuration keys should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self: Celery, *args: object, **kwargs: object) -> None:
    """
    A simple Celery task for debugging purposes.

    You can call this task from anywhere in your code base to ensure that
    Celery is properly configured and running.  It simply prints the task
    request information.
    """
    print(f'Request: {self.request!r}')
