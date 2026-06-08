from django.urls import re_path

from . import consumers


websocket_urlpatterns = [
    # Route to receive progress updates for an individual item
    re_path(r'ws/items/(?P<item_id>\d+)/$', consumers.ItemProgressConsumer.as_asgi()),
]
