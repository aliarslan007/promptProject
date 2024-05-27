from django.contrib import admin
from .models import User


class UserModelAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'created',) 

admin.site.register(User, UserModelAdmin)
