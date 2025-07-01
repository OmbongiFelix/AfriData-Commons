# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import CustomUser, UserProfile, LoginAttempt


class UserProfileInline(admin.StackedInline):
    """Inline admin for UserProfile"""
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile Information'
    fields = (
        ('website', 'location'),
        ('organization', 'job_title'),
        ('linkedin_url', 'github_url'),
        'twitter_handle'
    )


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Enhanced admin interface for CustomUser"""
    inlines = (UserProfileInline,)
    
    # Fields to display in the user list
    list_display = (
        'email', 'full_name', 'username', 'is_verified', 
        'is_active', 'is_staff', 'date_joined', 'last_login',
        'profile_picture_preview'
    )
    
    # Fields that can be searched
    search_fields = ('email', 'full_name', 'username', 'phone_number')
    
    # Filters in the right sidebar
    list_filter = (
        'is_active', 'is_staff', 'is_superuser', 'is_verified',
        'date_joined', 'last_login'
    )
    
    # Fields that are clickable links to the detail page
    list_display_links = ('email', 'full_name')
    
    # Number of items per page
    list_per_page = 25
    
    # Default ordering
    ordering = ('-date_joined',)
    
    # Make email and full_name editable directly from the list view
    list_editable = ('is_verified',)
    
    # Fields layout in the detail/edit form
    fieldsets = (
        ('Authentication', {
            'fields': ('email', 'username', 'password')
        }),
        ('Personal Information', {
            'fields': ('full_name', 'phone_number', 'bio', 'date_of_birth', 'profile_picture')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'is_verified', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('Important Dates', {
            'fields': ('last_login', 'date_joined', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('Security', {
            'fields': ('last_login_ip',),
            'classes': ('collapse',)
        })
    )
    
    # Fields for adding a new user
    add_fieldsets = (
        ('Required Information', {
            'classes': ('wide',),
            'fields': ('email', 'username', 'full_name', 'password1', 'password2'),
        }),
        ('Optional Information', {
            'classes': ('wide', 'collapse'),
            'fields': ('phone_number', 'bio', 'date_of_birth', 'profile_picture'),
        }),
        ('Permissions', {
            'classes': ('wide', 'collapse'),
            'fields': ('is_active', 'is_staff', 'is_verified'),
        }),
    )
    
    # Read-only fields
    readonly_fields = ('date_joined', 'last_login', 'created_at', 'updated_at', 'last_login_ip')
    
    # Custom methods for list display
    def profile_picture_preview(self, obj):
        """Display a small preview of the profile picture"""
        if obj.profile_picture:
            return format_html(
                '<img src="{}" width="30" height="30" style="border-radius: 50%;" />',
                obj.profile_picture.url
            )
        return "No Image"
    profile_picture_preview.short_description = "Profile Picture"
    
    # Actions
    actions = ['make_verified', 'make_unverified', 'deactivate_users']
    
    def make_verified(self, request, queryset):
        """Mark selected users as verified"""
        updated = queryset.update(is_verified=True)
        self.message_user(request, f'{updated} users marked as verified.')
    make_verified.short_description = "Mark selected users as verified"
    
    def make_unverified(self, request, queryset):
        """Mark selected users as unverified"""
        updated = queryset.update(is_verified=False)
        self.message_user(request, f'{updated} users marked as unverified.')
    make_unverified.short_description = "Mark selected users as unverified"
    
    def deactivate_users(self, request, queryset):
        """Deactivate selected users"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} users deactivated.')
    deactivate_users.short_description = "Deactivate selected users"


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin interface for UserProfile"""
    list_display = ('user_email', 'organization', 'job_title', 'location', 'website')
    search_fields = ('user__email', 'user__full_name', 'organization', 'job_title', 'location')
    list_filter = ('organization', 'location')
    
    # Custom field to show user email instead of object representation
    def user_email(self, obj):
        """Display user email with link to user admin"""
        url = reverse('admin:accounts_customuser_change', args=[obj.user.pk])
        return format_html('<a href="{}">{}</a>', url, obj.user.email)
    user_email.short_description = 'User Email'
    user_email.admin_order_field = 'user__email'
    
    # Group fields logically
    fieldsets = (
        ('Professional Information', {
            'fields': ('organization', 'job_title', 'location')
        }),
        ('Online Presence', {
            'fields': ('website', 'linkedin_url', 'github_url', 'twitter_handle')
        })
    )


@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    """Admin interface for LoginAttempt"""
    list_display = ('email', 'ip_address', 'success_status', 'timestamp', 'truncated_user_agent')
    list_filter = ('success', 'timestamp')
    search_fields = ('email', 'ip_address')
    readonly_fields = ('email', 'ip_address', 'success', 'timestamp', 'user_agent')
    
    # Don't allow adding new login attempts from admin
    def has_add_permission(self, request):
        return False
    
    # Don't allow editing login attempts
    def has_change_permission(self, request, obj=None):
        return False
    
    # Custom display methods
    def success_status(self, obj):
        """Display success status with colored icons"""
        if obj.success:
            return format_html(
                '<span style="color: green;">✓ Success</span>'
            )
        else:
            return format_html(
                '<span style="color: red;">✗ Failed</span>'
            )
    success_status.short_description = 'Status'
    success_status.admin_order_field = 'success'
    
    def truncated_user_agent(self, obj):
        """Display truncated user agent string"""
        if obj.user_agent:
            return obj.user_agent[:50] + '...' if len(obj.user_agent) > 50 else obj.user_agent
        return 'Unknown'
    truncated_user_agent.short_description = 'User Agent'
    
    # Custom actions
    actions = ['delete_failed_attempts']
    
    def delete_failed_attempts(self, request, queryset):
        """Delete all failed login attempts"""
        failed_attempts = queryset.filter(success=False)
        count = failed_attempts.count()
        failed_attempts.delete()
        self.message_user(request, f'{count} failed login attempts deleted.')
    delete_failed_attempts.short_description = "Delete failed login attempts"


# Customize admin site headers
admin.site.site_header = "User Management Admin"
admin.site.site_title = "User Admin"
admin.site.index_title = "Welcome to User Management Administration"