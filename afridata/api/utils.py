# api/utils.py
import time
from django.utils import timezone
from .models import APIUsage

class APIUsageMiddleware:
    """Middleware to log API usage"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Skip if not an API request
        if not request.path.startswith('/api/'):
            return self.get_response(request)
        
        start_time = time.time()
        response = self.get_response(request)
        response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        # Log usage if user is authenticated via API key
        if hasattr(request, 'auth') and hasattr(request.auth, 'key'):
            log_api_usage(
                api_key=request.auth,
                endpoint=request.path,
                method=request.method,
                response_code=response.status_code,
                response_time=response_time,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
        
        return response
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

def log_api_usage(api_key, endpoint, method, response_code, response_time, ip_address, user_agent):
    """Log API usage to database"""
    try:
        APIUsage.objects.create(
            api_key=api_key,
            endpoint=endpoint,
            method=method,
            response_code=response_code,
            response_time=response_time,
            ip_address=ip_address,
            user_agent=user_agent
        )
    except Exception as e:
        # Log error but don't fail the request
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to log API usage: {e}")

def get_rate_limit_key(request):
    """Generate rate limit key for user"""
    if hasattr(request, 'auth') and hasattr(request.auth, 'key'):
        return f"api_key_{request.auth.key}"
    elif request.user.is_authenticated:
        return f"user_{request.user.id}"
    else:
        # Use IP address for anonymous users
        return f"ip_{request.META.get('REMOTE_ADDR')}"

def check_rate_limit(request, limit=1000, window=3600):
    """Check if request is within rate limit"""
    # This is a simple implementation
    # In production, you'd want to use Redis or similar
    key = get_rate_limit_key(request)
    
    # For now, we'll always allow requests
    # Implement proper rate limiting with Redis/Memcached
    return True

def format_api_key(key):
    """Format API key for display (show only first 8 and last 4 characters)"""
    if len(key) > 12:
        return f"{key[:8]}...{key[-4:]}"
    return key