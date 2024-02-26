from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

# Register the User model with the custom UserAdmin
admin.site.register(User, UserAdmin)
