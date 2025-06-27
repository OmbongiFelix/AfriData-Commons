# home/urls.py
from django.urls import path
from . import views

app_name = 'home'

urlpatterns = [
    # Homepage
    path('', views.default_home, name='default_home'),
    
    # API endpoints for dataset operations
    path('api/search/', views.search_datasets, name='search_datasets'),
    path('api/trending/', views.trending_datasets, name='trending_datasets'),
    path('api/filter/', views.filter_datasets, name='filter_datasets'),
    path('api/stats/', views.dataset_stats, name='dataset_stats'),
    
    # api documentation
    path('api/docs/', views.api_docs, name='api_docs')
]