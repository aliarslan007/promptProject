from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from .models import User
from django.core.mail import send_mail, BadHeaderError
from .forms import UserForm
import random
from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError

def loginPage (request):
    page='login'

    print("in loginPage function")
    if request.user.is_authenticated:
        return redirect('promptapp:promptActionPage')
    if request.method=="POST":
        email=request.POST.get('email').lower()
        password=request.POST.get('password')
        # username=request.POST.get('username')
        print("user entered email is "+email)
        print("user entered email is "+password)
        try:
            user=User.objects.get(email=email)
            print("data  email is "+user.email)
            print("data password is "+user.password)
            user=authenticate(request,email=email, password=password)
            print(user)
            if user is not None:
                login(request, user)
                return redirect('promptapp:promptActionPage')
            else:
                login_error_message = "Invalid username or password. Please try again."
                return render(request, 'myauth/loginPage.html', {'login_error_message': login_error_message})
        except:
            login_error_message = "User does not exist."
            return render(request, 'myauth/loginPage.html', {'page': page, 'login_error_message': login_error_message})
    context={'page':page}
    return render(request, 'myauth/loginPage.html', context)


def logoutPage(request): 
        logout(request)
        return redirect('myauth:loginPage')

