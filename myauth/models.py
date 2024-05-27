from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from .Manager import CustomUserManager
from django.core.validators import RegexValidator
import uuid


class User(AbstractUser):
    username = models.CharField(max_length=20, null=True, blank=True)
    first_name = models.CharField(max_length=30, null=True, blank=True)  # Add this field
    last_name = models.CharField(max_length=30, null=True, blank=True)  
    email = models.EmailField(unique=True)
    created = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email

