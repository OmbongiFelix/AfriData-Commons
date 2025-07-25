from django.contrib import admin
from django.urls import path, include
from schema_graph.views import Schema

urlpatterns = [
    path('admin/', admin.site.urls),
    path('admin_dashboard/', include('admin_dashboard.urls')),
    path('', include('home.urls')),
    path('api/', include('api.urls')),
    path('accounts/', include('accounts.urls')),
    path('dataset/', include('dataset.urls')),
    path('community/', include('community.urls')),
    path('mpesa/', include('mpesa.urls')),

    #url to schema diagram
    path("schema/", Schema.as_view()),
]
