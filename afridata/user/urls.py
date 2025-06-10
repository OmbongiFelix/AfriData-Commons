from django.urls import path
from . import views

urlpatterns = [
    path('user', views.user_profile, name='user_profile'),
    ]
