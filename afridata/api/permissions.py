'''
This file defines custom permission classes that control who can access specific API endpoints and what actions they can perform (read, write, delete). It handles authorization logic like allowing only dataset owners to edit their datasets or restricting certain endpoints to authenticated users.
'''

# api/permissions.py
from rest_framework import permissions
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import APIKey

User = get_user_model()

class APIKeyAuthentication(BaseAuthentication):
    """Custom authentication using API keys"""
    
    def authenticate(self, request):
        api_key = self.get_api_key_from_request(request)
        if not api_key:
            return None
        
        try:
            key_obj = APIKey.objects.select_related('user').get(
                key=api_key, 
                is_active=True
            )
            # Update last_used timestamp
            key_obj.last_used = timezone.now()
            key_obj.save(update_fields=['last_used'])
            
            return (key_obj.user, key_obj)
        except APIKey.DoesNotExist:
            raise AuthenticationFailed('Invalid API key')
    
    def get_api_key_from_request(self, request):
        """Extract API key from request headers"""
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header:
            return None
        
        try:
            auth_type, api_key = auth_header.split(' ', 1)
            if auth_type.lower() == 'api-key':
                return api_key
        except ValueError:
            pass
        
        return None

class IsOwnerOrReadOnly(permissions.BasePermission):
    """Custom permission to only allow owners to edit their objects"""
    
    def has_object_permission(self, request, view, obj):
        # Read permissions for any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only for owner
        if hasattr(obj, 'author'):
            return obj.author == request.user
        elif hasattr(obj, 'user'):
            return obj.user == request.user
        
        return False

class IsOwner(permissions.BasePermission):
    """Permission to only allow owners to access their objects"""
    
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'author'):
            return obj.author == request.user
        elif hasattr(obj, 'user'):
            return obj.user == request.user
        return False

class IsVerifiedUser(permissions.BasePermission):
    """Permission to only allow verified users"""
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.is_verified
        )

class CanCreateDataset(permissions.BasePermission):
    """Permission to create datasets - requires authentication"""
    
    def has_permission(self, request, view):
        if request.method == 'POST':
            return request.user and request.user.is_authenticated
        return True

class RateLimitPermission(permissions.BasePermission):
    """Basic rate limiting permission"""
    
    def has_permission(self, request, view):
        # This would be implemented with a proper rate limiting system
        # For now, we'll just return True
        # In production, you'd want to use django-ratelimit or similar
        return True