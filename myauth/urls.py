from django.urls import path,  include
from .views import *
app_name = 'myauth'


urlpatterns = [
    path('login/', loginPage, name="loginPage"),
    path('logout/', logoutPage, name="logoutPage")
]
