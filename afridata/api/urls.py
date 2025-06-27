#api/urls.py
# Handle the API routing
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'api'

router = DefaultRouter()
router.register(r'datasets', views.DatasetViewSet)
router.register(r'users', views.UserViewSet)

urlpatterns = [
    path('v1/', include(router.urls)),
    path('auth/', include('rest_framework.urls')),
    path('api/', views.api_request, name='api_request'),
]

