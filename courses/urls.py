from django.urls import path
from .views import submit_quiz, update_progress

urlpatterns = [
    path("quiz/<int:quiz_id>/submit/", submit_quiz, name="submit_quiz"),
    path("progress/update/", update_progress, name="update_progress"),
]
