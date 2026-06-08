"""
ASGI config for backend project.

This module exposes the ASGI callable as a module-level variable named
``application``.  It is necessary for running Django with an ASGI server
(such as Daphne or Uvicorn) to support WebSockets via Django Channels.
"""
import os

from django.core.asgi import get_asgi_application  # type: ignore
from django.urls import path

# Import Channels components to build a ProtocolTypeRouter.  Only import
# channels if installed; otherwise this file will still be importable in
# environments where only WSGI is used.
try:
    from channels.auth import AuthMiddlewareStack  # type: ignore
    from channels.routing import ProtocolTypeRouter, URLRouter  # type: ignore
    from core import routing as core_routing  # type: ignore
    CHANNELS_AVAILABLE = True
except ImportError:
    # Channels not installed
    CHANNELS_AVAILABLE = False


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

# Initialize the standard Django application for HTTP requests.
django_asgi_app = get_asgi_application()

if CHANNELS_AVAILABLE:
    # If channels is installed, wrap the Django application with a ProtocolTypeRouter
    application = ProtocolTypeRouter(
        {
            "http": django_asgi_app,
            # Route WebSocket connections to channels consumers via URL patterns
            "websocket": AuthMiddlewareStack(
                URLRouter(
                    core_routing.websocket_urlpatterns
                )
            ),
        }
    )
else:
    # If channels isn't installed, simply expose the Django ASGI application.
    application = django_asgi_app
