from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as CustomUserAdmin
from .models import Recipe


@admin.register(get_user_model())
class UserAdmin(CustomUserAdmin):
    list_display = ["email", "name", "is_staff", "is_superuser", "is_active"]
    ordering = ["id"]
    fieldsets = [(None, {"fields": ["email", "name"]}),
                 ("دسترسی ها", {"fields": ["is_staff", "is_superuser", "is_active"]}),
                 ("تاریخ ها", {"fields": ["last_login"]}),
                 ]
    readonly_fields = ["last_login"]
    add_fieldsets = [
        [None, {
            "fields": ["email", "name", "password1", "password2", "is_active", "is_superuser", "is_staff"],
            "classes": ["wide", ]
        }]
    ]


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    pass
