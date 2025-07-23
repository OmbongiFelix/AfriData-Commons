# accounts/urls.py
from django.urls import path
from . import views
from home.views import default_home
#from dataset.views import home

urlpatterns = [
    # Existing URLs
    path('', views.login_signup_page, name='login_signup'),
    path('login/', views.authenticate_login, name='authenticate_login'),
    path('signup/', views.process_signup, name='process_signup'),
    path('home/', views.home, name='home'),
    path('logout/', views.logout_user, name='logout'),

    #default home
    path('default_home/', default_home, name='default_home'),
    #path('default_home/', views.home, name='default_home'),

    #alias
    path('login_signup/', views.login_signup_page),  # no need for a new name

    # Profile URLs
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile_view, name='edit_profile'),
    path('profile/<int:user_id>/', views.public_profile_view, name='public_profile'),

    # Token and Referral URLs (MISSING)
    path('token_purchase', views.token_purchase, name='token_purchase'),
    path('tokens/', views.token_dashboard, name='token_dashboard'),
    path('referrals/', views.referrals_view, name='referrals'),

    # API URLs
    path('api/check-email/', views.check_email_exists, name='check_email_exists'),
    path('api/check-username/', views.check_username_exists, name='check_username_exists'),
    path('api/check-referral/', views.check_referral_code, name='check_referral_code'),  # MISSING

    # Static Pages
    path('terms/', views.terms, name='terms'),
    path('privacy/', views.privacy_policy, name='privacy_policy'),
    path('settings/', views.settings, name='settings'),
    path('data-standards/', views.data_standards, name='data_standards'),
    path('data-license/', views.data_license, name='data_license'),

    #download license PDF
    path('download-license/', views.download_license_pdf, name='download_license_pdf'),
]