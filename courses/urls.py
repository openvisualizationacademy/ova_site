from django.urls import path
from .views import update_progress, generate_certificate

urlpatterns = [
    path("progress/update/", update_progress, name="update_progress"),
    path(
        "courses/<int:course_id>/certificate/",
        generate_certificate,
        name="generate_certificate",
    ),
]
