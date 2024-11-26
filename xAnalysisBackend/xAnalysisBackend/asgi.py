"""
ASGI config for xAnalysisBackend project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import TweetProcessor.routing  # Replace with the app where routing will be defined

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'xAnalysisBackend.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket":
        URLRouter(
            TweetProcessor.routing.websocket_urlpatterns  # Define websocket URL patterns in this module
        )

})
