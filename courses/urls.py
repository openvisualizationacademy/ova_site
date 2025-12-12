from django.urls import path
from .views import update_progress

urlpatterns = [
    path("progress/update/", update_progress, name="update_progress"),
]
