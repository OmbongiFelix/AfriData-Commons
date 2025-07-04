# api/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone
import secrets
import string

class APIKey(models.Model):
    """Model to store API keys for users"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='api_keys')
    name = models.CharField(max_length=100, help_text="Human-readable name for this API key")
    key = models.CharField(max_length=64, unique=True, editable=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_key()
        super().save(*args, **kwargs)
    
    def generate_key(self):
        """Generate a secure API key"""
        return 'ak_' + ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(40))
    
    def __str__(self):
        return f"{self.user.email} - {self.name}"

class APIUsage(models.Model):
    """Track API usage statistics"""
    api_key = models.ForeignKey(APIKey, on_delete=models.CASCADE, related_name='usage_records')
    endpoint = models.CharField(max_length=200)
    method = models.CharField(max_length=10)
    timestamp = models.DateTimeField(auto_now_add=True)
    response_code = models.IntegerField()
    response_time = models.FloatField(help_text="Response time in milliseconds")
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['api_key', 'timestamp']),
            models.Index(fields=['endpoint', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.api_key.user.email} - {self.endpoint} - {self.timestamp}"