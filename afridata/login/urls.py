from django.urls import path
from . import views

urlpatterns = [
    path('login', views.render_login_page, name='login_page'),
    ]
