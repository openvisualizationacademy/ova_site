from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Custom Fields', {
            'fields': ('phone', 'profile_pic'),
        }),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Custom Fields', {
            'fields': ('phone', 'profile_pic'),
        }),
    )

    list_display = BaseUserAdmin.list_display + ('phone',)
