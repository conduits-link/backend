from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, EditorFile

# Ensure users and files can be accessed from Django admin site.
admin.site.register(User, UserAdmin)
admin.site.register(EditorFile)