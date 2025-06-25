# accounts/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.utils import timezone

class CustomUser(AbstractUser):
    """Extended User model with additional fields"""
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)
    phone_number = models.CharField(
        max_length=15, 
        blank=True, 
        validators=[RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")]
    )
    bio = models.TextField(max_length=500, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)
    
    # Override email as the username field
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'full_name']
    
    class Meta:
        db_table = 'custom_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return self.email
    
    def get_short_name(self):
        return self.full_name.split()[0] if self.full_name else self.username
    
    def get_full_name(self):
        return self.full_name if self.full_name else self.username

class UserProfile(models.Model):
    """Additional profile information for users"""
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile')
    website = models.URLField(blank=True)
    location = models.CharField(max_length=100, blank=True)
    organization = models.CharField(max_length=200, blank=True)
    job_title = models.CharField(max_length=100, blank=True)
    linkedin_url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)
    twitter_handle = models.CharField(max_length=50, blank=True)
    
    def __str__(self):
        return f"{self.user.email}'s Profile"

class LoginAttempt(models.Model):
    """Track login attempts for security"""
    email = models.EmailField()
    ip_address = models.GenericIPAddressField()
    success = models.BooleanField()
    timestamp = models.DateTimeField(auto_now_add=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        status = "Success" if self.success else "Failed"
        return f"{status} login attempt for {self.email} at {self.timestamp}"















