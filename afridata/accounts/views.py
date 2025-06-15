# views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from .models import CustomUser, UserProfile, LoginAttempt
import re
from django.shortcuts import render
from django.http import HttpResponse

def terms(request):
    """Render the terms and conditions page"""
    return render(request, 'accounts/terms.html')


def privacy_policy(request):
    """Render the terms and conditions page"""
    return render(request, 'accounts/privacy_policy.html')


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
    email = request.POST.get('email', '').strip().lower()
    password = request.POST.get('password', '')
    remember_me = request.POST.get('remember_me', False)
    
    # Get client info for logging
    ip_address = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    
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
            
            # Redirect to next page or home
            next_page = request.POST.get('next') or request.GET.get('next')
            if next_page:
                return redirect(next_page)
            return redirect('home')
        else:
            messages.error(request, 'Your account is deactivated. Please contact support.')
    else:
        messages.error(request, 'Invalid email or password.')
        
    # Log failed attempt
    LoginAttempt.objects.create(
        email=email,
        ip_address=ip_address,
        success=False,
        user_agent=user_agent
    )
    
    return redirect('login_signup')



@csrf_protect
@require_http_methods(["POST"])
def process_signup(request):
    """Process user signup and store data in backend"""
    try:
        # Get form data
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        full_name = request.POST.get('full_name', '').strip()
        username = request.POST.get('username', '').strip().lower()
        phone_number = request.POST.get('phone_number', '').strip()
        bio = request.POST.get('bio', '').strip()
        
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
        if not username:
            errors.append('Username is required.')
        elif len(username) < 3:
            errors.append('Username must be at least 3 characters long.')
        elif CustomUser.objects.filter(username=username).exists():
            errors.append('Username already exists.')
        elif not re.match(r'^[a-zA-Z0-9_]+$', username):
            errors.append('Username can only contain letters, numbers, and underscores.')
        
        # Validate password strength
        try:
            validate_password(password)
        except ValidationError as e:
            errors.extend(e.messages)
        
        if errors:
            for error in errors:
                messages.error(request, error)
            return redirect('login_signup')
        
        # Create user with transaction
        with transaction.atomic():
            # Create user
            user = CustomUser.objects.create_user(
                username=username,
                email=email,
                password=password,
                full_name=full_name,
                phone_number=phone_number,
                bio=bio,
                last_login_ip=get_client_ip(request)
            )
            
            # Create user profile
            UserProfile.objects.create(user=user)
            
            # Log successful signup attempt
            LoginAttempt.objects.create(
                email=email,
                ip_address=get_client_ip(request),
                success=True,
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            # Auto-login after signup
            login(request, user)
            
            messages.success(request, f'Welcome to our platform, {user.get_short_name()}! Your account has been created successfully.')
            return redirect('home')
            
    except Exception as e:
        messages.error(request, 'An error occurred during signup. Please try again.')
        # Log failed signup attempt
        LoginAttempt.objects.create(
            email=email if 'email' in locals() else '',
            ip_address=get_client_ip(request),
            success=False,
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        return redirect('login_signup')



@login_required
        
def home_page(request):
    """Render authenticated user's home page"""
    user = request.user
    
    # Get user's recent activity or stats
    context = {
        'user': user,
        'full_name': user.get_full_name(),
        'member_since': user.created_at,
        'profile_complete': bool(user.full_name and user.email),
        'page_title': f'Welcome, {user.get_short_name()}',
    }
    
    return render(request, 'accounts/home.html', context)




@login_required
def logout_user(request):
    """Logout user and redirect"""
    user_name = request.user.get_short_name()
    logout(request)
    messages.success(request, f'Goodbye, {user_name}! You have been logged out successfully.')
    return redirect('login_signup')


@login_required
def profile_view(request):
    """Displays user profile"""
    user = request.user
    try:
        profile = user.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=user)
    
    context = {
        'user': user,
        'profile': profile,
        'page_title': 'My Profile'
    }
    return render(request, 'accounts/profile.html', context)
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
