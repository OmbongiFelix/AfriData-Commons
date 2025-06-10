from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    path('api/', views.api_request, name='api_request'),
    ]
