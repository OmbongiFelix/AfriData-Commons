# urls.py
from django.urls import path
from . import views

urlpatterns = [
    #path('login', views.render_login_page, name='login_page'),
    path('', views.login_signup_page, name='login_signup'),
    path('login/', views.authenticate_login, name='authenticate_login'),
    path('signup/', views.process_signup, name='process_signup'),
    path('home/', views.home_page, name='home'),
    path('logout/', views.logout_user, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('api/check-email/', views.check_email_exists, name='check_email_exists'),
    path('api/check-username/', views.check_username_exists, name='check_username_exists'),
    path('terms/', views.terms, name='terms'),
    path('privacy', views.privacy_policy, name='privacy_policy'),
]