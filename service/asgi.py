"""
ASGI config for backend project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/howto/deployment/asgi/
"""

import os

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator, OriginValidator
from django.core.asgi import get_asgi_application
from django.urls import path

from api.websockets import ChatConsumer
from service.core.SocketMiddleware import SocketAuthMiddleware

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "service.settings")

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": SocketAuthMiddleware(
            URLRouter([path("ws/chat/<room_id>/", ChatConsumer.as_asgi())])
        ),
    }
)
