# mpesa/urls.py
from django.urls import path
from . import views

app_name = 'mpesa'

urlpatterns = [
    # Token purchase and payment pages
    path('purchase/', views.token_purchase, name='token_purchase'),
    path('token/', views.token, name='token'),
    path('pay/', views.pay, name='pay'),
    
    # Payment processing
    path('stk/', views.stk, name='stk_push'),
    path('callback/', views.mpesa_callback, name='callback'),
    
    # Payment status and history
    path('status/<int:purchase_id>/', views.payment_status, name='payment_status'),
    path('transactions/', views.transaction_history, name='transaction_history'),
    path('balance/', views.check_balance, name='check_balance'),
]