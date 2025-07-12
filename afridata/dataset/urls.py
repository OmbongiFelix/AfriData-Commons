from django.urls import path
from . import views

urlpatterns = [
    path('', views.dataset_list, name='dataset_list'),
    #path('dataset/<int:dataset_id>/', views.render_dataset, name='dataset_page'),
    path('dataset/<int:dataset_id>/', views.dataset_detail, name='dataset_detail'),
    path('dataset/<int:dataset_id>/preview/', views.dataset_preview, name='dataset_preview'),
    path('dataset/<int:dataset_id>/download/', views.download_dataset, name='download_dataset'),
    path('dataset/<int:dataset_id>/comments/', views.dataset_comments, name='dataset_comments'),
    #path('dataset/<int:dataset_id>/comment/post/', views.post_comment, name='post_comment'),
    path('comment/<int:dataset_id>/post/', views.post_comment, name='post_comment'),
    path('comment/<int:comment_id>/upvote/', views.upvote_comment, name='upvote_comment'),
    path('datasets/upload/', views.upload_dataset, name='upload_dataset'),
    #path('datasets/upload/ajax/', views.upload_dataset_ajax, name='upload_dataset_ajax'),
]

