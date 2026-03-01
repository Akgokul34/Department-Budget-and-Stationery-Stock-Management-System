from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Department

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['username', 'email', 'role', 'department', 'is_staff']
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('role', 'department')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('role', 'department')}),
    )

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Department)
