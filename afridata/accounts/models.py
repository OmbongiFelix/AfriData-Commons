# accounts/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver

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
    #referral_code = models.CharField(max_length=10, null=True, blank=True)  # Remove unique=True for now
    referral_code = models.CharField(max_length=10, unique=True, blank=True, null=True, help_text="Unique referral code for the user")
    referred_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='referred_users')
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
    
    def generate_referral_code(self):
        """Generate a unique referral code"""
        import string
        import random
        
        if not self.referral_code:
            while True:
                code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
                if not CustomUser.objects.filter(referral_code=code).exists():
                    self.referral_code = code
                    self.save(update_fields=['referral_code'])
                    break
        return self.referral_code

class UserProfile(models.Model):
    """Additional profile information for users with token management"""
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile')
    website = models.URLField(blank=True)
    location = models.CharField(max_length=100, blank=True)
    organization = models.CharField(max_length=200, blank=True)
    job_title = models.CharField(max_length=100, blank=True)
    linkedin_url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)
    twitter_handle = models.CharField(max_length=50, blank=True)
    
    # Token-related fields
    token_balance = models.PositiveIntegerField(default=50, help_text="Current token balance")
    total_tokens_earned = models.PositiveIntegerField(default=50, help_text="Total tokens earned over time")
    total_tokens_spent = models.PositiveIntegerField(default=0, help_text="Total tokens spent on downloads")
    signup_bonus_awarded = models.BooleanField(default=False)
    
    # Subscription and premium features
    is_premium_subscriber = models.BooleanField(default=False)
    premium_subscription_expires = models.DateTimeField(null=True, blank=True)
    monthly_download_limit = models.PositiveIntegerField(default=50, help_text="Monthly download limit for free users")
    downloads_this_month = models.PositiveIntegerField(default=0)
    last_month_reset = models.DateField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.email}'s Profile"
    
    def can_afford(self, token_cost):
        """Check if user can afford a download"""
        return self.token_balance >= token_cost
    
    def spend_tokens(self, amount, description="Token spending"):
        """Deduct tokens from user's balance"""
        if self.can_afford(amount):
            self.token_balance -= amount
            self.total_tokens_spent += amount
            self.save(update_fields=['token_balance', 'total_tokens_spent'])
            
            # Create transaction record
            from dataset.models import TokenTransaction
            TokenTransaction.objects.create(
                user=self.user,
                transaction_type='download_cost',
                amount=-amount,
                description=description
            )
            return True
        return False
    
    def add_tokens(self, amount, transaction_type='purchase', description="Token addition", dataset=None):
        """Add tokens to user's balance"""
        self.token_balance += amount
        self.total_tokens_earned += amount
        self.save(update_fields=['token_balance', 'total_tokens_earned'])
        
        # Create transaction record
        from dataset.models import TokenTransaction
        TokenTransaction.objects.create(
            user=self.user,
            transaction_type=transaction_type,
            amount=amount,
            description=description,
            dataset=dataset
        )
    
    def reset_monthly_downloads_if_needed(self):
        """Reset monthly download counter if a new month has started"""
        from datetime import date
        current_date = date.today()
        
        if self.last_month_reset.month != current_date.month or self.last_month_reset.year != current_date.year:
            self.downloads_this_month = 0
            self.last_month_reset = current_date
            self.save(update_fields=['downloads_this_month', 'last_month_reset'])
    
    def can_download_this_month(self):
        """Check if user can download more files this month"""
        self.reset_monthly_downloads_if_needed()
        return self.downloads_this_month < self.monthly_download_limit or self.is_premium_subscriber
    
    def increment_monthly_downloads(self):
        """Increment monthly download counter"""
        self.downloads_this_month += 1
        self.save(update_fields=['downloads_this_month'])

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

class TokenPurchase(models.Model):
    """Track token purchases"""
    PACKAGE_CHOICES = [
        ('basic', '100 Tokens - $10'),
        ('standard', '500 Tokens - $40'),
        ('premium', '1200 Tokens - $80'),
        ('mega', '3000 Tokens - $150'),
    ]
    
    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='token_purchases')
    package = models.CharField(max_length=20, choices=PACKAGE_CHOICES)
    tokens_purchased = models.PositiveIntegerField()
    usd_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS, default='pending')
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.tokens_purchased} tokens (${self.usd_amount})"

# Signal to create UserProfile when CustomUser is created
@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        profile = UserProfile.objects.create(user=instance)
        
        # Award signup bonus
        if not profile.signup_bonus_awarded:
            profile.add_tokens(
                amount=50,
                transaction_type='signup_bonus',
                description='Welcome bonus for new users'
            )
            profile.signup_bonus_awarded = True
            profile.save(update_fields=['signup_bonus_awarded'])
        
        # Generate referral code
        instance.generate_referral_code()
        
        # Handle referral bonus if user was referred
        if instance.referred_by:
            from dataset.models import Referral, TokenTransaction
            
            # Create referral record
            referral, created = Referral.objects.get_or_create(
                referrer=instance.referred_by,
                referred_user=instance
            )
            
            if created and not referral.bonus_awarded:
                # Award bonus to referrer
                referrer_profile = instance.referred_by.profile
                referrer_profile.add_tokens(
                    amount=25,
                    transaction_type='referral_bonus',
                    description=f'Referral bonus for {instance.username}'
                )
                
                referral.bonus_awarded = True
                referral.save()

@receiver(post_save, sender=CustomUser)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()