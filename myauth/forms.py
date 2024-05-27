from django import forms
from django.db import models
from .models import User
from django.contrib.auth.forms import UserCreationForm

class UserForm(UserCreationForm):
    password1=forms.CharField(widget=forms.PasswordInput())
    password2=forms.CharField(widget=forms.PasswordInput())
    class Meta:
        model = User
        # fields = ('username', 'phone', 'email', 'password1', 'password2')  # Specify the fields to include in the form
        fields = ('first_name', 'last_name', 'email', 'password1', 'password2')  # Specify the fields to include in the form
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].label = 'Password'
        self.fields['password2'].label = 'Confirm Password'
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'

     

    
