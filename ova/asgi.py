import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ova.settings.dev")

# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.
django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
})
