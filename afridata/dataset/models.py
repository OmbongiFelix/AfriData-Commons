# dataset/models.py
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import os

class Dataset(models.Model):
    DATASET_TYPES = [
        ('csv', 'CSV'),
        ('excel', 'Excel'),
        ('pdf', 'PDF'),
        ('txt', 'Text'),
        ('json', 'JSON'),
        ('xml', 'XML'),
        ('zip', 'ZIP Archive'),
        ('yaml', 'YAML'),
        ('parquet', 'Parquet'),
    ]
    
    QUALITY_TIERS = [
        ('basic', 'Basic'),
        ('standard', 'Standard'),
        ('premium', 'Premium'),
    ]
    
    title = models.CharField(max_length=255)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='authored_datasets')
    file = models.FileField(upload_to='datasets/')
    dataset_type = models.CharField(max_length=20, choices=DATASET_TYPES)
    bio = models.TextField()
    topics = models.CharField(max_length=500, help_text="Comma-separated topics")
    rating = models.FloatField(default=0.0, validators=[MinValueValidator(0.0), MaxValueValidator(5.0)])
    downloads = models.PositiveIntegerField(default=0)
    views = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Token and Premium features
    is_premium = models.BooleanField(default=False)
    token_cost = models.PositiveIntegerField(default=0, help_text="Cost in tokens to download")
    premium_price_usd = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Premium price in USD")
    premium_token_discount = models.PositiveIntegerField(default=0, help_text="Token discount for premium datasets")
    quality_tier = models.CharField(max_length=10, choices=QUALITY_TIERS, default='basic')
    file_size_mb = models.FloatField(default=0.0, help_text="File size in MB")
    has_documentation = models.BooleanField(default=False)
    metadata_quality_score = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    def __str__(self):
        return self.title
    
    def get_topics_list(self):
        return [topic.strip() for topic in self.topics.split(',') if topic.strip()]
    
    def calculate_token_cost(self):
        """Calculate token cost based on file size"""
        if not self.file:
            return 0
            
        # Get file size in MB
        file_size = self.file.size / (1024 * 1024)
        self.file_size_mb = file_size
        
        if file_size < 10:
            return 5
        elif file_size < 50:
            return 25
        elif file_size < 125:
            return 75
        elif file_size < 350:
            return 200
        elif file_size < 560:
            return 400
        elif file_size < 1024:  # 1GB
            return 700
        elif file_size < 1536:  # 1.5GB
            return 1200
        else:
            return 1500  # For files larger than 1.5GB
    
    def get_upload_bonus_tokens(self):
        """Calculate bonus tokens for uploading (60% of download cost)"""
        base_tokens = self.calculate_token_cost()
        upload_bonus = int(base_tokens * 0.6)
        
        # Quality bonuses
        quality_bonus = 0
        if self.has_documentation:
            quality_bonus += 10
        if self.metadata_quality_score >= 80:
            quality_bonus += 20
        elif self.metadata_quality_score >= 60:
            quality_bonus += 10
            
        return upload_bonus + quality_bonus
    
    def can_user_download(self, user):
        """Check if user can download this dataset"""
        if not self.is_premium:
            return user.profile.token_balance >= self.token_cost
        return True  # Premium datasets have separate payment logic
    
    def save(self, *args, **kwargs):
        # Auto-calculate token cost on save
        if self.file and not self.token_cost:
            self.token_cost = self.calculate_token_cost()
        super().save(*args, **kwargs)

class Comment(models.Model):
    id = models.AutoField(primary_key=True)
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='authored_comments')
    content = models.TextField()
    upvotes = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-upvotes', '-created_at']
    
    def __str__(self):
        return f"Comment by {self.author.username} on {self.dataset.title}"

class TokenTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('signup_bonus', 'Signup Bonus'),
        ('upload_bonus', 'Upload Bonus'),
        ('download_cost', 'Download Cost'),
        ('purchase', 'Token Purchase'),
        ('referral_bonus', 'Referral Bonus'),
        ('quality_bonus', 'Quality Bonus'),
        ('refund', 'Refund'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='token_transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.IntegerField(help_text="Positive for credits, negative for debits")
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, null=True, blank=True, related_name='token_transactions')
    description = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username}: {self.amount} tokens ({self.transaction_type})"

class PremiumPurchase(models.Model):
    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_METHODS = [
        ('usd_only', 'USD Only'),
        ('tokens_only', 'Tokens Only'),
        ('hybrid', 'USD + Tokens'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='premium_purchases')
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name='premium_purchases')
    payment_method = models.CharField(max_length=15, choices=PAYMENT_METHODS)
    usd_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    tokens_used = models.PositiveIntegerField(default=0)
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS, default='pending')
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ('user', 'dataset')
    
    def __str__(self):
        return f"{self.user.username} - {self.dataset.title} (${self.usd_amount} + {self.tokens_used} tokens)"

class Download(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='downloads')
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name='download_records')
    tokens_spent = models.PositiveIntegerField(default=0)
    is_premium_download = models.BooleanField(default=False)
    premium_purchase = models.ForeignKey(PremiumPurchase, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'dataset')
    
    def __str__(self):
        return f"{self.user.username} downloaded {self.dataset.title}"

class Referral(models.Model):
    referrer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='referrals_made')
    referred_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='referrals_received')
    bonus_awarded = models.BooleanField(default=False)
    bonus_amount = models.PositiveIntegerField(default=25)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('referrer', 'referred_user')
    
    def __str__(self):
        return f"{self.referrer.username} referred {self.referred_user.username}"