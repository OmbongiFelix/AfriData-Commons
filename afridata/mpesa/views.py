# mpesa/views.py
import json
import logging
from datetime import datetime, timezone
from decimal import Decimal

import requests
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.conf import settings
from django.urls import reverse

from .credentials import MpesaAccessToken, LipanaMpesaPpassword, MpesaConfig
from accounts.models import CustomUser, TokenPurchase, UserProfile
from dataset.models import TokenTransaction

# Set up logging
logger = logging.getLogger(__name__)

# Token package configurations
TOKEN_PACKAGES = {
    'basic': {'tokens': 100, 'kes_amount': 1000, 'usd_amount': 10},
    'standard': {'tokens': 500, 'kes_amount': 4000, 'usd_amount': 40},
    'premium': {'tokens': 1200, 'kes_amount': 8000, 'usd_amount': 80},
    'mega': {'tokens': 3000, 'kes_amount': 15000, 'usd_amount': 150},
}

@login_required
def token_purchase(request):
    """Display token purchase page with available packages"""
    try:
        context = {
            'packages': TOKEN_PACKAGES,
            'user_profile': request.user.profile,
        }
        
        return render(request, 'mpesa/token_purchase.html', context)
        
    except Exception as e:
        logger.error(f"Error in token_purchase view: {e}")
        messages.error(request, "Error loading token purchase page. Please try again.")
        return redirect('accounts:token_dashboard')  # Redirect to token dashboard

@login_required
def token(request):
    """Generate and display M-Pesa access token"""
    try:
        # Get access token
        access_token = MpesaAccessToken.get_token()
        
        context = {
            'token': access_token,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'config': MpesaConfig.get_config()
        }
        
        return render(request, 'token.html', context)
        
    except Exception as e:
        logger.error(f"Error generating M-Pesa token: {e}")
        context = {
            'token': None,
            'error': str(e),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        return render(request, 'token.html', context)

@login_required
def pay(request):
    """Display payment form with token packages"""
    context = {
        'packages': TOKEN_PACKAGES,
        'user_profile': request.user.profile,
    }
    return render(request, 'pay.html', context)

@login_required
@require_http_methods(["POST"])
def stk(request):
    """Process STK Push payment for token purchase"""
    try:
        # Get form data
        phone = request.POST.get('phone', '').strip()
        amount = request.POST.get('amount', '').strip()
        package_type = request.POST.get('package', '').strip()
        
        # Validate inputs
        if not phone or not amount or not package_type:
            return JsonResponse({'success': False, 'message': 'Missing required fields'}, status=400)
        
        # Validate package
        if package_type not in TOKEN_PACKAGES:
            return JsonResponse({'success': False, 'message': 'Invalid package selected'}, status=400)
        
        package_info = TOKEN_PACKAGES[package_type]
        
        # Validate amount matches package
        if int(amount) != package_info['kes_amount']:
            return JsonResponse({'success': False, 'message': 'Amount does not match selected package'}, status=400)
        
        # Format phone number
        if phone.startswith('0'):
            phone = '254' + phone[1:]
        elif phone.startswith('+254'):
            phone = phone[1:]
        elif not phone.startswith('254'):
            phone = '254' + phone
        
        if not phone.isdigit() or len(phone) != 12:
            return JsonResponse({'success': False, 'message': 'Invalid phone number format. Use format: 0712345678'}, status=400)
        
        # Create pending purchase record
        with transaction.atomic():
            token_purchase = TokenPurchase.objects.create(
                user=request.user,
                package=package_type,
                tokens_purchased=package_info['tokens'],
                usd_amount=Decimal(str(package_info['usd_amount'])),
                payment_status='pending'
            )
        
        # Get M-Pesa credentials
        access_token = MpesaAccessToken.get_token()
        password_data = LipanaMpesaPpassword.generate_password()
        config = MpesaConfig.get_config()
        
        # Prepare STK Push request
        api_url = config['stk_push_url']
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
        
        account_reference = f"TOKENS-{token_purchase.id}"
        
        payload = {
            "BusinessShortCode": password_data['shortcode'],
            "Password": password_data['password'],
            "Timestamp": password_data['timestamp'],
            "TransactionType": "CustomerPayBillOnline",
            "Amount": int(amount),
            "PartyA": phone,
            "PartyB": password_data['shortcode'],
            "PhoneNumber": phone,
            "CallBackURL": "https://748f2b6a94e5.ngrok-free.app/mpesa/callback/",
            "AccountReference": account_reference,
            "TransactionDesc": f"{package_info['tokens']} tokens purchase"
        }

        logger.debug("STK Payload: %s", json.dumps(payload))
        logger.debug("Headers: %s", headers)

        response = requests.post(api_url, json=payload, headers=headers, timeout=30)

        try:
            response_data = response.json()
        except ValueError:
            logger.error("Invalid JSON from Safaricom: %s", response.text)
            return JsonResponse({'success': False, 'message': 'Invalid response from M-Pesa'}, status=500)

        logger.info(f"STK Push response: {response_data}")

        # Handle failed STK push
        if response.status_code != 200 or response_data.get('ResponseCode') != '0':
            token_purchase.payment_status = 'failed'
            token_purchase.save(update_fields=['payment_status'])
            return JsonResponse({
                'success': False,
                'message': response_data.get('errorMessage') or response_data.get('ResponseDescription') or 'STK push failed',
                'details': response_data
            }, status=400)

        # STK push successful
        token_purchase.stripe_payment_intent_id = response_data.get('CheckoutRequestID')
        token_purchase.save(update_fields=['stripe_payment_intent_id'])

        return JsonResponse({
            'success': True,
            'message': 'STK push sent successfully. Please check your phone.',
            'checkout_request_id': response_data.get('CheckoutRequestID'),
            'merchant_request_id': response_data.get('MerchantRequestID')
        })

    except requests.exceptions.RequestException as e:
        logger.error(f"STK Push request error: {e}")
        return JsonResponse({'success': False, 'message': 'Network error. Please try again.'}, status=500)
        
    except Exception as e:
        logger.error(f"STK Push error: {e}")
        return JsonResponse({'success': False, 'message': 'An error occurred. Please try again.'}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def mpesa_callback(request):
    """Handle M-Pesa payment callback from Safaricom"""
    try:
        # Decode JSON payload
        callback_data = json.loads(request.body.decode('utf-8'))
        logger.info(f"M-Pesa callback received: {json.dumps(callback_data, indent=2)}")
        
        stk_callback = callback_data.get('Body', {}).get('stkCallback', {})
        result_code = stk_callback.get('ResultCode')
        checkout_request_id = stk_callback.get('CheckoutRequestID')

        if not checkout_request_id:
            logger.error("Callback missing CheckoutRequestID")
            return HttpResponse(status=200)

        # Find pending purchase
        try:
            token_purchase = TokenPurchase.objects.get(
                stripe_payment_intent_id=checkout_request_id,
                payment_status='pending'
            )
        except TokenPurchase.DoesNotExist:
            logger.warning(f"No matching purchase found for CheckoutRequestID: {checkout_request_id}")
            return HttpResponse(status=200)

        if result_code == 0:
            # Successful payment
            with transaction.atomic():
                token_purchase.payment_status = 'completed'
                token_purchase.completed_at = timezone.now()
                token_purchase.save(update_fields=['payment_status', 'completed_at'])

                # Add tokens to user profile
                user_profile = token_purchase.user.profile
                user_profile.add_tokens(
                    amount=token_purchase.tokens_purchased,
                    transaction_type='purchase',
                    description=f'Purchased {token_purchase.package} package via M-Pesa'
                )

                logger.info(f"Tokens added for {token_purchase.user.username} ({token_purchase.tokens_purchased})")
        else:
            # Failed payment
            token_purchase.payment_status = 'failed'
            token_purchase.save(update_fields=['payment_status'])
            logger.info(f"Payment failed for user {token_purchase.user.username} | ResultCode: {result_code}")

        return HttpResponse(status=200)

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in callback: {e}")
        return HttpResponse("Invalid JSON", status=400)

    except Exception as e:
        logger.exception(f"Unhandled error processing callback: {e}")
        return HttpResponse("Server Error", status=500)

@login_required
def payment_status(request, purchase_id):
    """Check payment status"""
    try:
        purchase = get_object_or_404(
            TokenPurchase, 
            id=purchase_id, 
            user=request.user
        )
        
        return JsonResponse({
            'status': purchase.payment_status,
            'tokens': purchase.tokens_purchased,
            'amount': float(purchase.usd_amount),
            'created_at': purchase.created_at.isoformat(),
            'completed_at': purchase.completed_at.isoformat() if purchase.completed_at else None
        })
        
    except TokenPurchase.DoesNotExist:
        return JsonResponse({
            'error': 'Purchase not found'
        }, status=404)

@login_required
def transaction_history(request):
    """Display user's token transaction history"""
    try:
        transactions = TokenTransaction.objects.filter(
            user=request.user
        ).order_by('-created_at')[:20]  # Last 20 transactions
        
        purchases = TokenPurchase.objects.filter(
            user=request.user
        ).order_by('-created_at')[:10]  # Last 10 purchases
        
        context = {
            'transactions': transactions,
            'purchases': purchases,
            'user_profile': request.user.profile,
        }
        
        return render(request, 'accounts/transaction_history.html', context)
        
    except Exception as e:
        logger.error(f"Error in transaction_history view: {e}")
        messages.error(request, "Error loading transaction history.")
        return redirect('accounts:token_dashboard')

@login_required
def check_balance(request):
    """API endpoint to check user's token balance"""
    try:
        profile = request.user.profile
        return JsonResponse({
            'token_balance': profile.token_balance,
            'total_earned': profile.total_tokens_earned,
            'total_spent': profile.total_tokens_spent,
            'is_premium': profile.is_premium_subscriber
        })
    except Exception as e:
        logger.error(f"Error checking balance: {e}")
        return JsonResponse({'error': 'Unable to fetch balance'}, status=500)