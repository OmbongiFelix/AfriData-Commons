import io
import json
import logging
import numpy as np
import pandas as pd
import re

from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Avg, Count, Q, Sum
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.http import require_http_methods, require_POST

from accounts.models import CustomUser, LoginAttempt, TokenPurchase, UserProfile
from dataset.forms import DatasetUploadForm
from dataset.models import Comment, Dataset, Download, PremiumPurchase, Referral, TokenTransaction

User = get_user_model()



def terms(request):
    """Render the terms and conditions page"""
    return render(request, 'accounts/terms.html')


def settings(request):
    """Render settings page"""
    return render(request, 'accounts/settings.html')


def data_license(request):
    """Render the data license page"""
    return render(request, 'accounts/data_license.html')


def data_standards(request):
    """Render the data standards page"""
    return render(request, 'accounts/data_standards.html')


def privacy_policy(request):
    """Render the privacy policy page"""
    return render(request, 'accounts/privacy_policy.html')


def download_license_pdf(request):
    """Serve the data license PDF file"""
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="data_license.pdf"'
    with open('path/to/data_license.pdf', 'rb') as pdf:
        response.write(pdf.read())
    return response


def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def login_signup_page(request):
    """Render the login/signup page"""
    if request.user.is_authenticated:
        return redirect('home')
    
    context = {
        'page_title': 'Login / Sign Up'
    }
    return render(request, 'accounts/login.html', context)


@csrf_protect
@require_http_methods(["POST"])
def authenticate_login(request):
    """ Handles user authentication with security logging || Authenticate user login"""

    # Add debug logging to see what's happening
    logger = logging.getLogger(__name__)

    #Get form data
    email = request.POST.get('email', '').strip().lower()
    password = request.POST.get('password', '')
    remember_me = request.POST.get('remember_me', False)

    # DEBUG: Log all form data (remove password from logs in production)
    logger.debug(f"=== LOGIN ATTEMPT DEBUG ===")
    logger.debug(f"Email received: '{email}'")
    logger.debug(f"Password received: {'*' * len(password) if password else 'EMPTY'}")
    logger.debug(f"Remember me: {remember_me}")
    logger.debug(f"POST data keys: {list(request.POST.keys())}")
    
    
    # Get client info for logging
    ip_address = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')  #Browser and OS info 

    # Debug: Check what 'next' values we're getting
    next_post = request.POST.get('next')
    next_get = request.GET.get('next')
    logger.debug(f"Next from POST: {next_post}, Next from GET: {next_get}")
    
    if not email or not password:
        messages.error(request, 'Email and password are required.')
        LoginAttempt.objects.create(
            email=email,
            ip_address=ip_address,
            success=False,
            user_agent=user_agent
        )
        return redirect('login_signup')
    
    # Authenticate user
    user = authenticate(request, username=email, password=password)
    
    if user is not None:
        if user.is_active:
            login(request, user)
            
            # Set session expiry based on remember me
            if not remember_me:
                request.session.set_expiry(0)  # Browser session
            else:
                request.session.set_expiry(1209600)  # 2 weeks
            
            # Update last login IP
            user.last_login_ip = ip_address
            user.save(update_fields=['last_login_ip'])
            
            # Log successful attempt
            LoginAttempt.objects.create(
                email=email,
                ip_address=ip_address,
                success=True,
                user_agent=user_agent
            )
            
            messages.success(request, f'Welcome back, {user.get_short_name()}!')
            
            # FIXED: Better handling of next page redirect
            next_page = request.POST.get('next') or request.GET.get('next')

            # Debug logging
            logger.debug(f"Attempting redirect. Next page: {next_page}")
            
            if next_page:
                # Validate the next_page URL for security
                if url_has_allowed_host_and_scheme(next_page, allowed_hosts={request.get_host()}):
                    logger.debug(f"Redirecting to next page: {next_page}")
                    return redirect(next_page)
                else:
                    logger.warning(f"Invalid next page URL: {next_page}")
            
            # Default redirect to home
            logger.debug("Redirecting to home page")
            return redirect('home')
        else:
            messages.error(request, 'Your account is deactivated. Please contact support.')
    else:
        messages.error(request, 'Invalid email or password.')
        
    # Log failed attempt(for both inactive users and invalid credentials)
    LoginAttempt.objects.create(
        email=email,
        ip_address=ip_address,
        success=False,
        user_agent=user_agent
    )

    # Debug: Confirm we're redirecting due to failed login
    logger.debug(f"Login failed for {email}, redirecting to login page")
    
    return redirect('login_signup')


@csrf_protect
@require_http_methods(["POST"])
def process_signup(request):
    """Process user signup and store data in backend"""
    # Add comprehensive logging
    logger = logging.getLogger(__name__)
    logger.debug("=== SIGNUP ATTEMPT DEBUG ===")
    logger.debug(f"Method: {request.method}")
    logger.debug(f"POST data: {dict(request.POST)}")
    
    next_url = request.GET.get('next', '/')
    logger.debug(f"Next URL: {next_url}")
    
    try:
        # Get form data
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        full_name = request.POST.get('full_name', '').strip()
        username = request.POST.get('username', '').strip().lower()
        phone_number = request.POST.get('phone_number', '').strip()
        bio = request.POST.get('bio', '').strip()
        date_of_birth = request.POST.get('date_of_birth', '')
        referral_code = request.POST.get('referral_code', '').strip()
        
        logger.debug(f"Extracted data - Email: {email}, Full name: {full_name}, Username: {username}")
        
        # Validation
        errors = []
        
        if not email:
            errors.append('Email is required.')
        elif not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            errors.append('Please enter a valid email address.')
        elif CustomUser.objects.filter(email=email).exists():
            errors.append('Email already exists.')
        
        if not password:
            errors.append('Password is required.')
        elif len(password) < 8:
            errors.append('Password must be at least 8 characters long.')
        
        if password != confirm_password:
            errors.append('Passwords do not match.')
        
        if not full_name:
            errors.append('Full name is required.')
        elif len(full_name) < 2:
            errors.append('Full name must be at least 2 characters long.')
            
        # Generate username from full_name or email if not provided
        if not username:
            if full_name:
                username = full_name.lower().replace(' ', '_')
            else:
                username = email.split('@')[0]
            # Ensure uniqueness
            base_username = username
            counter = 1
            while CustomUser.objects.filter(username=username).exists():
                username = f"{base_username}_{counter}"
                counter += 1
            logger.debug(f"Generated username: {username}")
        elif len(username) < 3:
            errors.append('Username must be at least 3 characters long.')
        elif CustomUser.objects.filter(username=username).exists():
            errors.append('Username already exists.')
        elif not re.match(r'^[a-zA-Z0-9_]+$', username):
            errors.append('Username can only contain letters, numbers, and underscores.')
        
        # Validate referral code if provided
        referrer = None
        if referral_code:
            try:
                referrer = CustomUser.objects.get(referral_code=referral_code)
            except CustomUser.DoesNotExist:
                errors.append('Invalid referral code.')
        
        # Validate password strength
        try:
            validate_password(password)
        except ValidationError as e:
            errors.extend(e.messages)
        
        logger.debug(f"Validation errors: {errors}")
        
        if errors:
            for error in errors:
                messages.error(request, error)
            return redirect(f"{reverse('login_signup')}?next={next_url}")
        
        # Create user with transaction
        with transaction.atomic():
            logger.debug("Starting user creation...")
            
            # Create user
            user = CustomUser.objects.create_user(
                username=username,
                email=email,
                password=password,
                full_name=full_name,
                phone_number=phone_number,
                bio=bio,
                last_login_ip=get_client_ip(request),
                referred_by=referrer
            )
            
            # Add date_of_birth if provided
            if date_of_birth:
                try:
                    from datetime import datetime
                    user.date_of_birth = datetime.strptime(date_of_birth, '%Y-%m-%d').date()
                    user.save()
                except ValueError:
                    pass  # Invalid date format, skip
            
            logger.debug(f"User created with ID: {user.id}")
            
            # The UserProfile will be created automatically by the post_save signal
            # along with signup bonus and referral handling
            
            # Log successful signup attempt
            LoginAttempt.objects.create(
                email=email,
                ip_address=get_client_ip(request),
                success=True,
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            # Auto-login after signup
            login(request, user)
            logger.debug("User logged in successfully")
            
            messages.success(request, f'Welcome to our platform, {user.get_short_name()}! Your account has been created successfully and you received 50 welcome tokens.')
            return redirect(next_url)
            
    except Exception as e:
        logger.error(f"Signup error: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        messages.error(request, f'An error occurred during signup: {str(e)}')
        # Log failed signup attempt
        LoginAttempt.objects.create(
            email=email if 'email' in locals() else '',
            ip_address=get_client_ip(request),
            success=False,
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        return redirect(f"{reverse('login_signup')}?next={next_url}")




User = get_user_model()

@login_required
def home(request):
    """Comprehensive home page view with all necessary data"""
    user = request.user
    
    # Get or create user profile
    try:
        profile = user.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=user)
    
    # Reset monthly downloads if needed
    profile.reset_monthly_downloads_if_needed()
    
    # User-specific data
    user_downloads = Download.objects.filter(user=user).count()
    user_uploads = Dataset.objects.filter(author=user).count()
    user_datasets = Dataset.objects.filter(author=user).order_by('-created_at')[:5]
    referrals_count = User.objects.filter(referred_by=user).count()
    
    # Recent token transactions
    recent_transactions = TokenTransaction.objects.filter(
        user=user
    ).order_by('-created_at')[:5]
    
    # Platform statistics
    total_researchers = User.objects.count()
    total_datasets = Dataset.objects.count()
    total_downloads = Dataset.objects.aggregate(Sum('downloads'))['downloads__sum'] or 0
    total_views = Dataset.objects.aggregate(Sum('views'))['views__sum'] or 0
    
    # Trending datasets (most downloaded in the last week)
    trending_datasets = Dataset.objects.select_related('author').annotate(
        recent_growth=Count('id')
    ).order_by('-downloads', '-views')[:3]
    
    # Get top categories with counts
    all_datasets = Dataset.objects.all()
    category_counts = {}
    
    for dataset in all_datasets:
        topics = dataset.get_topics_list()
        for topic in topics:
            topic_lower = topic.lower().strip()
            if topic_lower in category_counts:
                category_counts[topic_lower] += 1
            else:
                category_counts[topic_lower] = 1
    
    # Sort categories by count and get top categories
    top_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:4]
    
    # Popular search terms (based on topics)
    popular_terms = [category[0].title() for category in top_categories[:6]] if top_categories else []
    
    # Featured datasets
    featured_datasets = Dataset.objects.select_related('author').order_by('-rating', '-downloads')[:4]
    
    # File format counts
    format_counts = {
        'csv': Dataset.objects.filter(dataset_type='csv').count(),
        'excel': Dataset.objects.filter(dataset_type='excel').count(),
        'pdf': Dataset.objects.filter(dataset_type='pdf').count(),
        'txt': Dataset.objects.filter(dataset_type='txt').count(),
        'json': Dataset.objects.filter(dataset_type='json').count(),
        'yaml': Dataset.objects.filter(dataset_type='yaml').count(),
        'xml': Dataset.objects.filter(dataset_type='xml').count(),
        'zip': Dataset.objects.filter(dataset_type='zip').count(),
        'parquet': Dataset.objects.filter(dataset_type='parquet').count(),
    }
    
    context = {
        # User profile data
        'user': user,
        'profile': profile,
        'full_name': user.get_full_name(),
        'member_since': user.created_at,
        'profile_complete': bool(user.full_name and user.email),
        'page_title': f'Welcome, {user.get_short_name()}',
        
        # Token data
        'token_balance': profile.token_balance,
        'total_tokens_earned': profile.total_tokens_earned,
        'total_tokens_spent': profile.total_tokens_spent,
        'recent_transactions': recent_transactions,
        
        # User datasets and activity
        'user_datasets': user_datasets,
        'user_downloads': user_downloads,
        'user_uploads': user_uploads,
        'downloads_remaining': profile.monthly_download_limit - profile.downloads_this_month,
        
        # Referral data
        'referrals_count': referrals_count,
        'referral_code': user.referral_code,
        'is_premium': profile.is_premium_subscriber,
        
        # Platform statistics
        'total_datasets': total_datasets,
        'total_downloads': total_downloads,
        'total_views': total_views,
        'total_countries': 54,  # Static for now
        'total_researchers': total_researchers,
        
        # Content data
        'trending_datasets': trending_datasets,
        'top_categories': top_categories,
        'popular_terms': popular_terms,
        'featured_datasets': featured_datasets,
        'format_counts': format_counts,
    }
    
    return render(request, 'home.html', context)


@login_required
def logout_user(request):
    """Logout user and redirect"""
    user_name = request.user.get_short_name()
    logout(request)
    messages.success(request, f'Goodbye, {user_name}! You have been logged out successfully.')
    return redirect('default_home')


# Check if email exists (AJAX endpoint)
def check_email_exists(request):
    """Check if email already exists"""
    if request.method == 'GET':
        email = request.GET.get('email', '').strip().lower()
        exists = CustomUser.objects.filter(email=email).exists()
        return JsonResponse({'exists': exists})
    return JsonResponse({'error': 'Invalid request'})


# Check if username exists (AJAX endpoint)
def check_username_exists(request):
    """Check if username already exists"""
    if request.method == 'GET':
        username = request.GET.get('username', '').strip().lower()
        exists = CustomUser.objects.filter(username=username).exists()
        return JsonResponse({'exists': exists})
    return JsonResponse({'error': 'Invalid request'})


# Check if referral code is valid (AJAX endpoint)
def check_referral_code(request):
    """Check if referral code is valid"""
    if request.method == 'GET':
        referral_code = request.GET.get('referral_code', '').strip()
        if referral_code:
            exists = CustomUser.objects.filter(referral_code=referral_code).exists()
            return JsonResponse({'valid': exists})
        return JsonResponse({'valid': False})
    return JsonResponse({'error': 'Invalid request'})


User = get_user_model()

@login_required
def profile_view(request):
    """Displays user profile with dynamic data including token information"""
    user = request.user
    
    # Get or create user profile
    try:
        profile = user.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=user)
    
    # Reset monthly downloads if needed
    profile.reset_monthly_downloads_if_needed()
    
    # Get user's datasets
    user_datasets = Dataset.objects.filter(author=user).order_by('-created_at')
    
    # Calculate real user statistics
    total_downloads = user_datasets.aggregate(total=Sum('downloads'))['total'] or 0
    total_views = user_datasets.aggregate(total=Sum('views'))['total'] or 0
    average_rating = user_datasets.aggregate(avg=Avg('rating'))['avg'] or 0.0
    total_comments = Comment.objects.filter(dataset__author=user).count()
    
    user_stats = {
        'datasets_uploaded': user_datasets.count(),
        'total_downloads': total_downloads,
        'profile_views': total_views,
        'stars_collected': int(average_rating * user_datasets.count()),
        'total_reviews': total_comments,
        'average_rating': round(average_rating, 1),
    }
    
    # Get recent token transactions
    recent_transactions = TokenTransaction.objects.filter(
        user=user
    ).order_by('-created_at')[:10]
    
    # Get referral information
    referrals = CustomUser.objects.filter(referred_by=user).order_by('-created_at')
    referrals_count = referrals.count()
    
    # Get token purchases
    recent_purchases = TokenPurchase.objects.filter(
        user=user,
        payment_status='completed'
    ).order_by('-created_at')[:5]
    
    context = {
        'user': user,
        'profile': profile,
        'user_stats': user_stats,
        'user_datasets': user_datasets,
        'recent_transactions': recent_transactions,
        'referrals': referrals,
        'referrals_count': referrals_count,
        'recent_purchases': recent_purchases,
        'page_title': f"{user.get_full_name()}'s Profile" if user.get_full_name() else f"{user.username}'s Profile"
    }
    
    return render(request, 'accounts/profile.html', context)


@login_required
def edit_profile_view(request):
    """Edit user profile"""
    user = request.user
    
    try:
        profile = user.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=user)
    
    if request.method == 'POST':
        # Handle form submission
        try:
            with transaction.atomic():
                # Update user fields
                user.full_name = request.POST.get('full_name', user.full_name)
                user.bio = request.POST.get('bio', user.bio)
                user.phone_number = request.POST.get('phone_number', user.phone_number)
                
                # Handle date of birth
                date_of_birth = request.POST.get('date_of_birth')
                if date_of_birth:
                    from datetime import datetime
                    try:
                        user.date_of_birth = datetime.strptime(date_of_birth, '%Y-%m-%d').date()
                    except ValueError:
                        messages.error(request, 'Invalid date format.')
                        return redirect('edit_profile')
                
                # Handle profile picture upload
                if 'profile_picture' in request.FILES:
                    user.profile_picture = request.FILES['profile_picture']
                
                user.save()
                
                # Update profile fields
                profile.location = request.POST.get('location', profile.location)
                profile.organization = request.POST.get('organization', profile.organization)
                profile.job_title = request.POST.get('job_title', profile.job_title)
                profile.website = request.POST.get('website', profile.website)
                profile.linkedin_url = request.POST.get('linkedin_url', profile.linkedin_url)
                profile.github_url = request.POST.get('github_url', profile.github_url)
                profile.twitter_handle = request.POST.get('twitter_handle', profile.twitter_handle)
                
                profile.save()
                
                messages.success(request, 'Profile updated successfully!')
                return redirect('profile')
                
        except Exception as e:
            messages.error(request, f'Error updating profile: {str(e)}')
    
    context = {
        'user': user,
        'profile': profile,
        'page_title': 'Edit Profile'
    }
    
    return render(request, 'accounts/edit_profile.html', context)


def public_profile_view(request, user_id):
    """View other user's public profile"""
    try:
        profile_user = get_object_or_404(CustomUser, id=user_id)
        profile = profile_user.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=profile_user)
    
    # Get user's datasets
    user_datasets = Dataset.objects.filter(author=profile_user).order_by('-created_at')
    
    # Calculate real user statistics
    total_downloads = user_datasets.aggregate(total=Sum('downloads'))['total'] or 0
    total_views = user_datasets.aggregate(total=Sum('views'))['total'] or 0
    average_rating = user_datasets.aggregate(avg=Avg('rating'))['avg'] or 0.0
    total_comments = Comment.objects.filter(dataset__author=profile_user).count()
    
    user_stats = {
        'datasets_uploaded': user_datasets.count(),
        'total_downloads': total_downloads,
        'profile_views': total_views,
        'stars_collected': int(average_rating * user_datasets.count()),
        'total_reviews': total_comments,
        'average_rating': round(average_rating, 1),
    }
    
    context = {
        'user': profile_user,
        'profile': profile,
        'user_stats': user_stats,
        'user_datasets': user_datasets,
        'is_own_profile': request.user == profile_user if request.user.is_authenticated else False,
        'page_title': f"{profile_user.get_full_name()}'s Profile" if profile_user.get_full_name() else f"{profile_user.username}'s Profile"
    }
    
    return render(request, 'accounts/public_profile.html', context)


@login_required
def token_dashboard(request):
    """Display user's token dashboard"""
    user = request.user
    profile = user.profile
    
    # Get token transactions
    transactions = TokenTransaction.objects.filter(
        user=user
    ).order_by('-created_at')
    
    # Get token purchases
    purchases = TokenPurchase.objects.filter(
        user=user
    ).order_by('-created_at')
    
    # Get referral earnings
    referral_earnings = TokenTransaction.objects.filter(
        user=user,
        transaction_type='referral_bonus'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    context = {
        'profile': profile,
        'transactions': transactions,
        'purchases': purchases,
        'referral_earnings': referral_earnings,
        'page_title': 'Token Dashboard'
    }
    
    return render(request, 'accounts/token_dashboard.html', context)


@login_required 
def referrals_view(request):
    """Display user's referral information"""
    user = request.user
    
    # Get referred users
    referred_users = CustomUser.objects.filter(referred_by=user).order_by('-created_at')
    
    # Get referral bonuses earned
    referral_bonuses = TokenTransaction.objects.filter(
        user=user,
        transaction_type='referral_bonus'
    ).order_by('-created_at')
    
    total_referral_earnings = referral_bonuses.aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    context = {
        'referred_users': referred_users,
        'referral_bonuses': referral_bonuses,
        'total_referral_earnings': total_referral_earnings,
        'referral_code': user.referral_code,
        'referrals_count': referred_users.count(),
        'page_title': 'Referrals'
    }
    
    return render(request, 'accounts/referrals.html', context)

@login_required
def token_purchase(request):
    return render(request, 'accounts/token_purchase.html')

