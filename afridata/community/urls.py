# community/urls.py
from django.urls import path
from . import views

app_name = 'community'

urlpatterns = [
    # Main community page
    path('', views.community_page, name='community'),
    
    # Topic pages
    path('topic/<int:pk>/', views.topic_detail, name='topic_detail'),
    path('topic/<int:topic_pk>/create-thread/', views.create_thread, name='create_thread'),
    
    # Thread pages
    path('thread/<int:pk>/', views.thread_detail, name='thread_detail'),
    path('thread/<int:thread_pk>/reply/', views.create_post, name='create_post'),
    
    # AJAX endpoints
    path('post/<int:post_pk>/vote/', views.vote_post, name='vote_post'),
    
    # Search
    path('search/', views.search_threads, name='search'),
    
    # User profiles
    path('user/<str:username>/', views.user_profile, name='user_profile'),
]