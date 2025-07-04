# api/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DatasetViewSet, CommentViewSet, UserProfileView, 
    APIKeyViewSet, APIUsageStatsView, APIUsageViewSet,
    AuthViewSet, PublicStatsView
)

# Create router and register viewsets
router = DefaultRouter()
router.register(r'datasets', DatasetViewSet)
router.register(r'comments', CommentViewSet)
router.register(r'api-keys', APIKeyViewSet, basename='apikey')
router.register(r'usage', APIUsageViewSet, basename='usage')
router.register(r'auth', AuthViewSet, basename='auth')

app_name = 'api'

urlpatterns = [
    # API routes
    path('v1/', include(router.urls)),
    
    # Individual endpoints
    path('v1/user/profile/', UserProfileView.as_view(), name='user-profile'),
    path('v1/stats/', APIUsageStatsView.as_view(), name='api-usage-stats'),
    path('v1/public/stats/', PublicStatsView.as_view(), name='public-stats'),
    
    # API documentation endpoints (for the HTML page)
    path('docs/', include([
        path('', include('home.urls')),  # This will include the API docs template
    ])),
]