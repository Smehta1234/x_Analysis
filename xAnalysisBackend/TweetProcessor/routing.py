# routing.py
from django.urls import re_path
from . import consumers

# Define WebSocket URL patterns with a keyword as an input
websocket_urlpatterns = [
    re_path(r'ws/keyword/(?P<keyword>\w+)/$', consumers.KeywordConsumer.as_asgi()),
]
