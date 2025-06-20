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
    
    # Alternative class-based view URLs (commented out by default)
    # path('', views.HomeView.as_view(), name='home_cbv'),
    # path('api/search-cbv/', views.DatasetSearchView.as_view(), name='search_cbv'),
    # path('api/trending-cbv/', views.TrendingDatasetsView.as_view(), name='trending_cbv'),
    # path('api/filter-cbv/', views.FilterDatasetsView.as_view(), name='filter_cbv'),
]