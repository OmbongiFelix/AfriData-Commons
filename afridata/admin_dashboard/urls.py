# admin_dashboard/urls.py
from django.urls import path
from . import views

app_name = 'admin_dashboard'

urlpatterns = [
    # Dashboard home
    path('', views.dashboard_home, name='dashboard_home'),
    
    # User management
    path('users/', views.user_management, name='user_management'),
    path('users/<int:user_id>/', views.user_detail, name='user_detail'),
    path('users/<int:user_id>/toggle-status/', views.toggle_user_status, name='toggle_user_status'),
    
    # Dataset management
    path('datasets/', views.dataset_management, name='dataset_management'),
    
    # Community management
    path('community/', views.community_management, name='community_management'),
    
    # API management
    path('api/', views.api_management, name='api_management'),
    
    # System logs
    path('logs/', views.system_logs, name='system_logs'),
    
    # Data export
    path('export/', views.export_data, name='export_data'),
    
    # Analytics API
    path('api/analytics/', views.analytics_api, name='analytics_api'),
]