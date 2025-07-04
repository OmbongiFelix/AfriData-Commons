# api/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import APIKey, APIUsage

@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'formatted_key', 'is_active', 'created_at', 'last_used')
    list_filter = ('is_active', 'created_at', 'last_used')
    search_fields = ('user__email', 'user__username', 'name')
    readonly_fields = ('key', 'created_at', 'last_used')
    ordering = ('-created_at',)
    
    def formatted_key(self, obj):
        """Display formatted API key"""
        if obj.key:
            return format_html(
                '<code>{}</code>',
                f"{obj.key[:8]}...{obj.key[-4:]}"
            )
        return '-'
    formatted_key.short_description = 'API Key'
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing existing object
            return self.readonly_fields + ('user',)
        return self.readonly_fields

@admin.register(APIUsage)
class APIUsageAdmin(admin.ModelAdmin):
    list_display = ('api_key_user', 'endpoint', 'method', 'response_code', 
                   'response_time', 'timestamp', 'ip_address')
    list_filter = ('method', 'response_code', 'timestamp', 'endpoint')
    search_fields = ('api_key__user__email', 'endpoint', 'ip_address')
    readonly_fields = ('api_key', 'endpoint', 'method', 'timestamp', 
                      'response_code', 'response_time', 'ip_address', 'user_agent')
    ordering = ('-timestamp',)
    date_hierarchy = 'timestamp'
    
    def api_key_user(self, obj):
        """Display user email from API key"""
        return obj.api_key.user.email
    api_key_user.short_description = 'User'
    api_key_user.admin_order_field = 'api_key__user__email'
    
    def has_add_permission(self, request):
        """Don't allow manual addition of usage records"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Don't allow editing of usage records"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Allow deletion for cleanup"""
        return True

# Custom admin actions
def revoke_api_keys(modeladmin, request, queryset):
    """Revoke selected API keys"""
    updated = queryset.update(is_active=False)
    modeladmin.message_user(
        request,
        f"{updated} API key(s) were successfully revoked."
    )
revoke_api_keys.short_description = "Revoke selected API keys"

def activate_api_keys(modeladmin, request, queryset):
    """Activate selected API keys"""
    updated = queryset.update(is_active=True)
    modeladmin.message_user(
        request,
        f"{updated} API key(s) were successfully activated."
    )
activate_api_keys.short_description = "Activate selected API keys"

# Add actions to APIKeyAdmin
APIKeyAdmin.actions = [revoke_api_keys, activate_api_keys]