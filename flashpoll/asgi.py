import os
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from django.urls import path
from poll.consumers import VoteConsumer   

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "flashpoll.settings")

django_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_app,                        
    "websocket": URLRouter([
        path("ws/poll/<slug:slug>/", VoteConsumer.as_asgi()),
    ]),
})
