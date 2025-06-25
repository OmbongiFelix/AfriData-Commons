# urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Existing URLs
    path('', views.login_signup_page, name='login_signup'),
    path('login/', views.authenticate_login, name='authenticate_login'),
    path('signup/', views.process_signup, name='process_signup'),
    path('home/', views.home_page, name='home'),
    path('logout/', views.logout_user, name='logout'),

    # Profile URLs
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile_view, name='edit_profile'),  # New
    path('profile/<int:user_id>/', views.public_profile_view, name='public_profile'),  # New

     # API URLs
    path('api/check-email/', views.check_email_exists, name='check_email_exists'),
    path('api/check-username/', views.check_username_exists, name='check_username_exists'),

    # Static Pages
    path('terms/', views.terms, name='terms'),
    path('privacy', views.privacy_policy, name='privacy_policy'),
]



