from django.contrib import admin
from .models import Quiz, Question

# Register your models here.
@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    pass

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    pass