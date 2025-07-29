# admin_dashboard/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal


class AdminLog(models.Model):
    """Track admin activities"""
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('view', 'View'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('export', 'Export'),
        ('import', 'Import'),
        ('bulk_action', 'Bulk Action'),
        ('token_adjustment', 'Token Adjustment'),
        ('user_verification', 'User Verification'),
        ('premium_override', 'Premium Override'),
        ('api_key_management', 'API Key Management'),
        ('dataset_moderation', 'Dataset Moderation'),
        ('referral_management', 'Referral Management'),
    ]
    
    admin_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='admin_logs'
    )
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100, blank=True)
    object_repr = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Additional fields for enhanced tracking
    user_agent = models.TextField(blank=True)
    affected_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='admin_actions_received'
    )
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['admin_user', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
            models.Index(fields=['model_name', 'timestamp']),
            models.Index(fields=['affected_user', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.admin_user.username} - {self.action} {self.model_name} at {self.timestamp}"


class DashboardSettings(models.Model):
    """Global dashboard settings"""
    SETTING_TYPES = [
        ('string', 'String'),
        ('integer', 'Integer'),
        ('float', 'Float'),
        ('boolean', 'Boolean'),
        ('json', 'JSON'),
    ]
    
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    setting_type = models.CharField(max_length=20, choices=SETTING_TYPES, default='string')
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_settings'
    )
    
    class Meta:
        verbose_name = 'Dashboard Setting'
        verbose_name_plural = 'Dashboard Settings'
    
    def __str__(self):
        return self.key


class SystemMetrics(models.Model):
    """Store system metrics for dashboard"""
    METRIC_CATEGORIES = [
        ('users', 'Users'),
        ('datasets', 'Datasets'),
        ('tokens', 'Tokens'),
        ('downloads', 'Downloads'),
        ('api', 'API Usage'),
        ('community', 'Community'),
        ('system', 'System'),
        ('financial', 'Financial'),
    ]
    
    metric_name = models.CharField(max_length=100)
    metric_value = models.FloatField()
    metric_type = models.CharField(max_length=50)  # 'counter', 'gauge', 'histogram'
    category = models.CharField(max_length=20, choices=METRIC_CATEGORIES, default='system')
    timestamp = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['metric_name', 'timestamp']),
            models.Index(fields=['metric_type', 'timestamp']),
            models.Index(fields=['category', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.metric_name}: {self.metric_value} at {self.timestamp}"


class AdminNotification(models.Model):
    """Notifications for admin users"""
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    TYPE_CHOICES = [
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('success', 'Success'),
        ('system', 'System Alert'),
        ('security', 'Security Alert'),
        ('user_action', 'User Action Required'),
    ]
    
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='info')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    is_read = models.BooleanField(default=False)
    is_global = models.BooleanField(default=True, help_text="Show to all admin users")
    target_admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='targeted_notifications'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    action_url = models.URLField(blank=True, help_text="URL for action button")
    action_label = models.CharField(max_length=50, blank=True, help_text="Label for action button")
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_read', 'created_at']),
            models.Index(fields=['priority', 'created_at']),
        ]
    
    def __str__(self):
        return self.title
    
    def is_expired(self):
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False


class BulkAction(models.Model):
    """Track bulk actions performed in admin"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    ACTION_TYPES = [
        ('user_bulk_update', 'User Bulk Update'),
        ('dataset_bulk_update', 'Dataset Bulk Update'),
        ('token_bulk_adjustment', 'Token Bulk Adjustment'),
        ('user_verification', 'User Verification'),
        ('dataset_moderation', 'Dataset Moderation'),
        ('api_key_management', 'API Key Management'),
        ('data_export', 'Data Export'),
        ('data_import', 'Data Import'),
        ('cleanup_operation', 'Cleanup Operation'),
    ]
    
    admin_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='bulk_actions'
    )
    action_name = models.CharField(max_length=100)
    action_type = models.CharField(max_length=30, choices=ACTION_TYPES, default='user_bulk_update')
    model_name = models.CharField(max_length=100)
    total_items = models.PositiveIntegerField()
    processed_items = models.PositiveIntegerField(default=0)
    failed_items = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True)
    success_message = models.TextField(blank=True)
    parameters = models.JSONField(default=dict, blank=True, help_text="Action parameters")
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['status', 'started_at']),
            models.Index(fields=['action_type', 'started_at']),
        ]
    
    def __str__(self):
        return f"{self.action_name} on {self.model_name} by {self.admin_user.username}"
    
    def progress_percentage(self):
        if self.total_items == 0:
            return 0
        return (self.processed_items / self.total_items) * 100


class TokenAdjustment(models.Model):
    """Track manual token adjustments by admins"""
    ADJUSTMENT_TYPES = [
        ('bonus', 'Bonus Award'),
        ('penalty', 'Penalty Deduction'),
        ('correction', 'Correction'),
        ('refund', 'Refund'),
        ('compensation', 'Compensation'),
    ]
    
    admin_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='token_adjustments_made'
    )
    target_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='token_adjustments_received'
    )
    adjustment_type = models.CharField(max_length=20, choices=ADJUSTMENT_TYPES)
    amount = models.IntegerField(help_text="Positive for additions, negative for deductions")
    reason = models.TextField()
    reference_dataset = models.ForeignKey(
        'dataset.Dataset',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='admin_adjustments'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['target_user', 'created_at']),
            models.Index(fields=['adjustment_type', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.admin_user.username} adjusted {self.target_user.username} by {self.amount} tokens"


class UserModerationAction(models.Model):
    """Track user moderation actions"""
    ACTION_TYPES = [
        ('warning', 'Warning'),
        ('suspension', 'Temporary Suspension'),
        ('ban', 'Permanent Ban'),
        ('verification_override', 'Verification Override'),
        ('premium_override', 'Premium Override'),
        ('profile_restriction', 'Profile Restriction'),
        ('api_restriction', 'API Restriction'),
    ]
    
    admin_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='moderation_actions_taken'
    )
    target_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='moderation_actions_received'
    )
    action_type = models.CharField(max_length=30, choices=ACTION_TYPES)
    reason = models.TextField()
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_moderation_actions'
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['target_user', 'is_active']),
            models.Index(fields=['action_type', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.action_type} for {self.target_user.username} by {self.admin_user.username}"
    
    def is_expired(self):
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False


class DatasetModerationQueue(models.Model):
    """Queue for datasets requiring moderation"""
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('needs_changes', 'Needs Changes'),
    ]
    
    dataset = models.OneToOneField(
        'dataset.Dataset',
        on_delete=models.CASCADE,
        related_name='moderation_queue'
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='moderated_datasets'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reviewer_notes = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    priority = models.IntegerField(default=0, help_text="Higher numbers = higher priority")
    
    class Meta:
        ordering = ['-priority', 'submitted_at']
        indexes = [
            models.Index(fields=['status', 'submitted_at']),
            models.Index(fields=['priority', 'submitted_at']),
        ]
    
    def __str__(self):
        return f"Moderation for {self.dataset.title} - {self.status}"


class AdminReport(models.Model):
    """Store generated admin reports"""
    REPORT_TYPES = [
        ('user_analytics', 'User Analytics'),
        ('dataset_analytics', 'Dataset Analytics'),
        ('token_analytics', 'Token Analytics'),
        ('financial_report', 'Financial Report'),
        ('system_health', 'System Health'),
        ('security_audit', 'Security Audit'),
        ('api_usage', 'API Usage Report'),
        ('community_activity', 'Community Activity'),
    ]
    
    FORMATS = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV'),
        ('json', 'JSON'),
    ]
    
    name = models.CharField(max_length=255)
    report_type = models.CharField(max_length=30, choices=REPORT_TYPES)
    format = models.CharField(max_length=10, choices=FORMATS, default='pdf')
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='generated_reports'
    )
    file = models.FileField(upload_to='admin_reports/', blank=True, null=True)
    parameters = models.JSONField(default=dict, blank=True)
    date_from = models.DateTimeField()
    date_to = models.DateTimeField()
    generated_at = models.DateTimeField(auto_now_add=True)
    file_size = models.PositiveIntegerField(default=0, help_text="File size in bytes")
    download_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['-generated_at']
        indexes = [
            models.Index(fields=['report_type', 'generated_at']),
            models.Index(fields=['generated_by', 'generated_at']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.report_type} ({self.generated_at.date()})"