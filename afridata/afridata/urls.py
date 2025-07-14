from django.contrib import admin
from django.urls import path, include
from schema_graph.views import Schema

urlpatterns = [
    path('admin/', admin.site.urls),
    #path('', include('home.urls')),
    path('', lambda request: HttpResponse("Homepage is working ✅")),
    path('api/', include('api.urls')),
    path('accounts/', include('accounts.urls')),
    path('dataset/', include('dataset.urls')),
    path('user/', include('user.urls')),
    path('community/', include('community.urls')),

    #url to schema diagram
    path("schema/", Schema.as_view()),
]
