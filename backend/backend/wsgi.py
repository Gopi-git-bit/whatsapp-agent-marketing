"""
WSGI config for backend project.

This module exposes the WSGI callable as a module-level variable named
``application``.  It allows the project to be served by WSGI servers such as
Gunicorn or uWSGI.  Note that when using WebSockets (via Channels) an ASGI
server should be used instead.
"""
import os
from django.core.wsgi import get_wsgi_application  # type: ignore

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

application = get_wsgi_application()
