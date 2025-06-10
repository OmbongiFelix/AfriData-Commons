from django.urls import path
from . import views

urlpatterns = [
    path('dataset', views.render_dataset, name='dataset_page'),
    ]
