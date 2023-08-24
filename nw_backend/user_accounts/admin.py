from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import EditorFile, User

admin.site.register(EditorFile)
admin.site.register(User, UserAdmin)
