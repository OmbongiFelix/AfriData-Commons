# admin_dashboard/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.db.models import Count, Q, Avg, Sum, F, Max
from django.http import JsonResponse, HttpResponse, Http404
from django.utils import timezone
from django.core.paginator import Paginator
from django.views.decorators.http import require_http_methods, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.core.exceptions import ValidationError
import json
import csv
from datetime import datetime, timedelta
from decimal import Decimal

# Import your models
from accounts.models import CustomUser, UserProfile, LoginAttempt
from api.models import APIKey, APIUsage
from community.models import Topic, Thread, Post, PostVote, UserActivity
from dataset.models import Dataset, Comment
from .models import (
    AdminLog, DashboardSettings, SystemMetrics, AdminNotification, 
    BulkAction, TokenAdjustment, UserModerationAction, 
    DatasetModerationQueue, AdminReport
)


def is_superuser(user):
    """Check if user is superuser"""
    return user.is_authenticated and user.is_superuser


def log_admin_action(user, action, model_name, obj=None, description="", affected_user=None, request=None):
    """Helper function to log admin actions"""
    ip_address = '127.0.0.1'
    user_agent = ''
    
    if request:
        ip_address = request.META.get('REMOTE_ADDR', '127.0.0.1')
        user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    AdminLog.objects.create(
        admin_user=user,
        action=action,
        model_name=model_name,
        object_id=str(obj.id) if obj else '',
        object_repr=str(obj) if obj else '',
        description=description,
        ip_address=ip_address,
        user_agent=user_agent,
        affected_user=affected_user
    )


@user_passes_test(is_superuser)
def dashboard_home(request):
    """Enhanced main dashboard view with comprehensive statistics"""
    # Basic statistics
    total_users = CustomUser.objects.count()
    active_users = CustomUser.objects.filter(is_active=True).count()
    verified_users = CustomUser.objects.filter(is_verified=True).count()
    
    total_datasets = Dataset.objects.count()
    pending_datasets = DatasetModerationQueue.objects.filter(status='pending').count()
    total_api_keys = APIKey.objects.filter(is_active=True).count()
    total_threads = Thread.objects.filter(is_active=True).count()
    total_posts = Post.objects.filter(is_active=True).count()
    
    # Recent activity
    recent_users = CustomUser.objects.order_by('-created_at')[:5]
    recent_datasets = Dataset.objects.order_by('-created_at')[:5]
    recent_threads = Thread.objects.filter(is_active=True).order_by('-created_at')[:5]
    
    # Security metrics
    yesterday = timezone.now() - timedelta(days=1)
    recent_login_attempts = LoginAttempt.objects.filter(timestamp__gte=yesterday).count()
    failed_login_attempts = LoginAttempt.objects.filter(
        timestamp__gte=yesterday, 
        success=False
    ).count()
    
    # API usage statistics
    api_usage_today = APIUsage.objects.filter(
        timestamp__date=timezone.now().date()
    ).count()
    
    # Top rated datasets
    top_datasets = Dataset.objects.order_by('-rating')[:5]
    
    # Notifications and pending actions
    unread_notifications = AdminNotification.objects.filter(
        is_read=False,
        expires_at__gt=timezone.now()
    ).count()
    
    pending_bulk_actions = BulkAction.objects.filter(
        status__in=['pending', 'processing']
    ).count()
    
    active_moderation_actions = UserModerationAction.objects.filter(
        is_active=True
    ).count()
    
    # Recent system metrics
    recent_metrics = SystemMetrics.objects.order_by('-timestamp')[:10]
    
    # Growth metrics (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    new_users_30d = CustomUser.objects.filter(created_at__gte=thirty_days_ago).count()
    new_datasets_30d = Dataset.objects.filter(created_at__gte=thirty_days_ago).count()
    
    # Token adjustment statistics
    total_token_adjustments = TokenAdjustment.objects.filter(
        created_at__gte=thirty_days_ago
    ).aggregate(
        total_adjustments=Count('id'),
        total_amount=Sum('amount')
    )
    
    context = {
        'total_users': total_users,
        'active_users': active_users,
        'verified_users': verified_users,
        'total_datasets': total_datasets,
        'pending_datasets': pending_datasets,
        'total_api_keys': total_api_keys,
        'total_threads': total_threads,
        'total_posts': total_posts,
        'recent_users': recent_users,
        'recent_datasets': recent_datasets,
        'recent_threads': recent_threads,
        'recent_login_attempts': recent_login_attempts,
        'failed_login_attempts': failed_login_attempts,
        'api_usage_today': api_usage_today,
        'top_datasets': top_datasets,
        'unread_notifications': unread_notifications,
        'pending_bulk_actions': pending_bulk_actions,
        'active_moderation_actions': active_moderation_actions,
        'recent_metrics': recent_metrics,
        'new_users_30d': new_users_30d,
        'new_datasets_30d': new_datasets_30d,
        'token_adjustments_30d': total_token_adjustments,
    }
    
    log_admin_action(request.user, 'view', 'Dashboard', description="Accessed main dashboard", request=request)
    
    return render(request, 'admin_dashboard/dashboard.html', context)


@user_passes_test(is_superuser)
def user_management(request):
    """Enhanced user management view"""
    search_query = request.GET.get('search', '')
    filter_type = request.GET.get('filter', 'all')
    sort_by = request.GET.get('sort', '-created_at')
    
    users = CustomUser.objects.all()
    
    if search_query:
        users = users.filter(
            Q(email__icontains=search_query) |
            Q(full_name__icontains=search_query) |
            Q(username__icontains=search_query)
        )
    
    if filter_type == 'active':
        users = users.filter(is_active=True)
    elif filter_type == 'inactive':
        users = users.filter(is_active=False)
    elif filter_type == 'verified':
        users = users.filter(is_verified=True)
    elif filter_type == 'unverified':
        users = users.filter(is_verified=False)
    elif filter_type == 'moderated':
        users = users.filter(moderation_actions_received__is_active=True).distinct()
    elif filter_type == 'premium':
        users = users.filter(userprofile__is_premium=True)
    
    # Apply sorting
    if sort_by in ['-created_at', 'created_at', 'email', '-email', 'full_name', '-full_name']:
        users = users.order_by(sort_by)
    else:
        users = users.order_by('-created_at')
    
    # Annotate with additional info
    users = users.annotate(
        dataset_count=Count('authored_datasets'),
        api_key_count=Count('api_keys'),
        moderation_count=Count('moderation_actions_received', filter=Q(moderation_actions_received__is_active=True))
    )
    
    paginator = Paginator(users, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'filter_type': filter_type,
        'sort_by': sort_by,
        'total_users': users.count(),
    }
    
    return render(request, 'admin_dashboard/user_management.html', context)


@user_passes_test(is_superuser)
def user_detail(request, user_id):
    """Enhanced detailed view of a specific user"""
    user = get_object_or_404(CustomUser, id=user_id)
    
    # Get user's datasets
    user_datasets = Dataset.objects.filter(author=user).order_by('-created_at')[:10]
    
    # Get user's API keys
    user_api_keys = APIKey.objects.filter(user=user).order_by('-created_at')[:10]
    
    # Get user's forum activity
    user_threads = Thread.objects.filter(author=user, is_active=True).order_by('-created_at')[:10]
    user_posts = Post.objects.filter(author=user, is_active=True).order_by('-created_at')[:10]
    
    # Get recent login attempts
    login_attempts = LoginAttempt.objects.filter(email=user.email).order_by('-timestamp')[:10]
    
    # Get token adjustments for this user
    token_adjustments = TokenAdjustment.objects.filter(target_user=user).order_by('-created_at')[:10]
    
    # Get moderation actions
    moderation_actions = UserModerationAction.objects.filter(target_user=user).order_by('-created_at')[:10]
    
    # Get admin logs related to this user
    admin_logs = AdminLog.objects.filter(affected_user=user).order_by('-timestamp')[:10]
    
    # Calculate user statistics
    total_token_adjustments = TokenAdjustment.objects.filter(target_user=user).aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    context = {
        'user_obj': user,
        'user_datasets': user_datasets,
        'user_api_keys': user_api_keys,
        'user_threads': user_threads,
        'user_posts': user_posts,
        'login_attempts': login_attempts,
        'token_adjustments': token_adjustments,
        'moderation_actions': moderation_actions,
        'admin_logs': admin_logs,
        'total_token_adjustments': total_token_adjustments,
    }
    
    log_admin_action(request.user, 'view', 'CustomUser', user, f"Viewed user details for {user.email}", user, request)
    
    return render(request, 'admin_dashboard/user_detail.html', context)


@user_passes_test(is_superuser)
def dataset_management(request):
    """Enhanced dataset management view"""
    search_query = request.GET.get('search', '')
    dataset_type = request.GET.get('type', 'all')
    moderation_status = request.GET.get('moderation', 'all')
    
    datasets = Dataset.objects.all().select_related('author')
    
    if search_query:
        datasets = datasets.filter(
            Q(title__icontains=search_query) |
            Q(bio__icontains=search_query) |
            Q(topics__icontains=search_query)
        )
    
    if dataset_type != 'all':
        datasets = datasets.filter(dataset_type=dataset_type)
    
    if moderation_status == 'pending':
        datasets = datasets.filter(moderation_queue__status='pending')
    elif moderation_status == 'approved':
        datasets = datasets.filter(moderation_queue__status='approved')
    elif moderation_status == 'rejected':
        datasets = datasets.filter(moderation_queue__status='rejected')
    
    datasets = datasets.order_by('-created_at')
    
    paginator = Paginator(datasets, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get dataset type choices for filter
    dataset_types = Dataset.DATASET_TYPES
    
    # Get moderation queue statistics
    moderation_stats = DatasetModerationQueue.objects.values('status').annotate(
        count=Count('id')
    )
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'dataset_type': dataset_type,
        'moderation_status': moderation_status,
        'dataset_types': dataset_types,
        'moderation_stats': moderation_stats,
        'total_datasets': datasets.count(),
    }
    
    return render(request, 'admin_dashboard/dataset_management.html', context)


@user_passes_test(is_superuser)
def moderation_queue(request):
    """Dataset moderation queue management"""
    status_filter = request.GET.get('status', 'pending')
    
    queue_items = DatasetModerationQueue.objects.select_related(
        'dataset', 'dataset__author', 'reviewed_by'
    )
    
    if status_filter != 'all':
        queue_items = queue_items.filter(status=status_filter)
    
    queue_items = queue_items.order_by('-priority', 'submitted_at')
    
    paginator = Paginator(queue_items, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'status_choices': DatasetModerationQueue.STATUS_CHOICES,
    }
    
    return render(request, 'admin_dashboard/moderation_queue.html', context)


@user_passes_test(is_superuser)
@require_POST
def moderate_dataset(request, queue_id):
    """Handle dataset moderation action"""
    queue_item = get_object_or_404(DatasetModerationQueue, id=queue_id)
    
    new_status = request.POST.get('status')
    reviewer_notes = request.POST.get('reviewer_notes', '')
    
    if new_status not in ['approved', 'rejected', 'needs_changes']:
        messages.error(request, "Invalid moderation status.")
        return redirect('admin_dashboard:moderation_queue')
    
    with transaction.atomic():
        queue_item.status = new_status
        queue_item.reviewer_notes = reviewer_notes
        queue_item.reviewed_by = request.user
        queue_item.reviewed_at = timezone.now()
        queue_item.save()
        
        # Update dataset status based on moderation
        if new_status == 'approved':
            queue_item.dataset.is_published = True
            queue_item.dataset.save()
        elif new_status == 'rejected':
            queue_item.dataset.is_published = False
            queue_item.dataset.save()
    
    log_admin_action(
        request.user, 'dataset_moderation', 'DatasetModerationQueue', 
        queue_item, f"Moderated dataset: {new_status}", 
        queue_item.dataset.author, request
    )
    
    messages.success(request, f"Dataset moderation updated to {new_status}.")
    return redirect('admin_dashboard:moderation_queue')


@user_passes_test(is_superuser)
def token_management(request):
    """Token adjustment management view"""
    adjustments = TokenAdjustment.objects.select_related(
        'admin_user', 'target_user', 'reference_dataset'
    ).order_by('-created_at')
    
    # Filter by adjustment type
    adjustment_type = request.GET.get('type', 'all')
    if adjustment_type != 'all':
        adjustments = adjustments.filter(adjustment_type=adjustment_type)
    
    # Filter by date range
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if date_from:
        adjustments = adjustments.filter(created_at__date__gte=date_from)
    if date_to:
        adjustments = adjustments.filter(created_at__date__lte=date_to)
    
    paginator = Paginator(adjustments, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Calculate statistics
    stats = TokenAdjustment.objects.aggregate(
        total_adjustments=Count('id'),
        total_amount=Sum('amount'),
        positive_adjustments=Sum('amount', filter=Q(amount__gt=0)),
        negative_adjustments=Sum('amount', filter=Q(amount__lt=0))
    )
    
    context = {
        'page_obj': page_obj,
        'adjustment_type': adjustment_type,
        'adjustment_types': TokenAdjustment.ADJUSTMENT_TYPES,
        'date_from': date_from,
        'date_to': date_to,
        'stats': stats,
    }
    
    return render(request, 'admin_dashboard/token_management.html', context)


@user_passes_test(is_superuser)
@require_POST
def adjust_user_tokens(request, user_id):
    """Adjust tokens for a specific user"""
    user = get_object_or_404(CustomUser, id=user_id)
    
    try:
        adjustment_type = request.POST.get('adjustment_type')
        amount = int(request.POST.get('amount', 0))
        reason = request.POST.get('reason', '')
        
        if not reason:
            messages.error(request, "Reason is required for token adjustments.")
            return redirect('admin_dashboard:user_detail', user_id=user_id)
        
        with transaction.atomic():
            # Create token adjustment record
            adjustment = TokenAdjustment.objects.create(
                admin_user=request.user,
                target_user=user,
                adjustment_type=adjustment_type,
                amount=amount,
                reason=reason
            )
            
            # Update user's token balance (assuming token field exists in user profile)
            if hasattr(user, 'userprofile'):
                profile = user.userprofile
                profile.tokens = F('tokens') + amount
                profile.save()
        
        log_admin_action(
            request.user, 'token_adjustment', 'TokenAdjustment',
            adjustment, f"Adjusted tokens by {amount} for {user.email}",
            user, request
        )
        
        messages.success(request, f"Successfully adjusted {user.email}'s tokens by {amount}.")
        
    except (ValueError, ValidationError) as e:
        messages.error(request, f"Error adjusting tokens: {str(e)}")
    
    return redirect('admin_dashboard:user_detail', user_id=user_id)


@user_passes_test(is_superuser)
def user_moderation(request):
    """User moderation actions management"""
    actions = UserModerationAction.objects.select_related(
        'admin_user', 'target_user', 'resolved_by'
    ).order_by('-created_at')
    
    # Filter by action type
    action_type = request.GET.get('type', 'all')
    if action_type != 'all':
        actions = actions.filter(action_type=action_type)
    
    # Filter by active status
    is_active = request.GET.get('active', 'all')
    if is_active == 'true':
        actions = actions.filter(is_active=True)
    elif is_active == 'false':
        actions = actions.filter(is_active=False)
    
    paginator = Paginator(actions, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'action_type': action_type,
        'action_types': UserModerationAction.ACTION_TYPES,
        'is_active': is_active,
    }
    
    return render(request, 'admin_dashboard/user_moderation.html', context)


@user_passes_test(is_superuser)
@require_POST
def moderate_user(request, user_id):
    """Apply moderation action to a user"""
    user = get_object_or_404(CustomUser, id=user_id)
    
    action_type = request.POST.get('action_type')
    reason = request.POST.get('reason', '')
    expires_at = request.POST.get('expires_at')
    
    if not reason:
        messages.error(request, "Reason is required for moderation actions.")
        return redirect('admin_dashboard:user_detail', user_id=user_id)
    
    try:
        with transaction.atomic():
            moderation_action = UserModerationAction.objects.create(
                admin_user=request.user,
                target_user=user,
                action_type=action_type,
                reason=reason,
                expires_at=expires_at if expires_at else None
            )
            
            # Apply the moderation action
            if action_type == 'suspension':
                user.is_active = False
                user.save()
            elif action_type == 'ban':
                user.is_active = False
                user.save()
        
        log_admin_action(
            request.user, 'user_moderation', 'UserModerationAction',
            moderation_action, f"Applied {action_type} to {user.email}",
            user, request
        )
        
        messages.success(request, f"Successfully applied {action_type} to {user.email}.")
        
    except ValidationError as e:
        messages.error(request, f"Error applying moderation: {str(e)}")
    
    return redirect('admin_dashboard:user_detail', user_id=user_id)


@user_passes_test(is_superuser)
def bulk_actions(request):
    """Bulk actions management"""
    actions = BulkAction.objects.select_related('admin_user').order_by('-started_at')
    
    # Filter by status
    status_filter = request.GET.get('status', 'all')
    if status_filter != 'all':
        actions = actions.filter(status=status_filter)
    
    paginator = Paginator(actions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'status_choices': BulkAction.STATUS_CHOICES,
    }
    
    return render(request, 'admin_dashboard/bulk_actions.html', context)


@user_passes_test(is_superuser)
def notifications(request):
    """Admin notifications management"""
    notifications = AdminNotification.objects.order_by('-created_at')
    
    # Filter by read status
    read_status = request.GET.get('read', 'all')
    if read_status == 'unread':
        notifications = notifications.filter(is_read=False)
    elif read_status == 'read':
        notifications = notifications.filter(is_read=True)
    
    # Filter by priority
    priority_filter = request.GET.get('priority', 'all')
    if priority_filter != 'all':
        notifications = notifications.filter(priority=priority_filter)
    
    paginator = Paginator(notifications, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'read_status': read_status,
        'priority_filter': priority_filter,
        'priority_choices': AdminNotification.PRIORITY_CHOICES,
    }
    
    return render(request, 'admin_dashboard/notifications.html', context)


@user_passes_test(is_superuser)
@require_POST
def mark_notification_read(request, notification_id):
    """Mark notification as read"""
    notification = get_object_or_404(AdminNotification, id=notification_id)
    notification.is_read = True
    notification.save()
    
    return JsonResponse({'status': 'success'})


@user_passes_test(is_superuser)
def system_settings(request):
    """System settings management"""
    if request.method == 'POST':
        key = request.POST.get('key')
        value = request.POST.get('value')
        setting_type = request.POST.get('setting_type', 'string')
        description = request.POST.get('description', '')
        
        try:
            setting, created = DashboardSettings.objects.get_or_create(
                key=key,
                defaults={
                    'value': value,
                    'setting_type': setting_type,
                    'description': description,
                    'updated_by': request.user
                }
            )
            
            if not created:
                setting.value = value
                setting.setting_type = setting_type
                setting.description = description
                setting.updated_by = request.user
                setting.save()
            
            log_admin_action(
                request.user, 'update', 'DashboardSettings',
                setting, f"Updated setting {key}",
                request=request
            )
            
            messages.success(request, f"Setting '{key}' updated successfully.")
            
        except Exception as e:
            messages.error(request, f"Error updating setting: {str(e)}")
        
        return redirect('admin_dashboard:system_settings')
    
    settings = DashboardSettings.objects.filter(is_active=True).order_by('key')
    # Add these to your view
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'delete':
            key = request.POST.get('key')
            DashboardSettings.objects.filter(key=key).delete()
            messages.success(request, f"Setting '{key}' deleted successfully.")
            
        elif action == 'import':
            # Handle file import logic
            pass
            
        elif action == 'reset':
            # Handle reset to defaults
            DashboardSettings.objects.all().delete()
            messages.success(request, "All settings reset to defaults.")
    
    context = {
        'settings': settings,
        'setting_types': DashboardSettings.SETTING_TYPES,
    }
    
    return render(request, 'admin_dashboard/settings.html', context)


@user_passes_test(is_superuser)
def system_metrics(request):
    """System metrics dashboard"""
    # Get recent metrics
    metrics = SystemMetrics.objects.order_by('-timestamp')[:100]
    
    # Group by category
    metrics_by_category = {}
    for metric in metrics:
        if metric.category not in metrics_by_category:
            metrics_by_category[metric.category] = []
        metrics_by_category[metric.category].append(metric)
    
    # Get metric statistics
    metric_stats = SystemMetrics.objects.values('metric_name').annotate(
        count=Count('id'),
        avg_value=Avg('metric_value'),
        latest_value=Max('metric_value')
    ).order_by('-count')[:20]
    
    context = {
        'metrics_by_category': metrics_by_category,
        'metric_stats': metric_stats,
        'categories': SystemMetrics.METRIC_CATEGORIES,
    }
    
    return render(request, 'admin_dashboard/system_metrics.html', context)


@user_passes_test(is_superuser)
def community_management(request):
    """Enhanced community/forum management view"""
    # Get topics with thread and post counts
    topics = Topic.objects.all().annotate(
        thread_count=Count('threads', filter=Q(threads__is_active=True)),
        post_count=Count('threads__posts', filter=Q(threads__posts__is_active=True))
    )
    
    # Recent threads
    recent_threads = Thread.objects.filter(is_active=True).select_related('author', 'topic').order_by('-created_at')[:10]
    
    # Recent posts
    recent_posts = Post.objects.filter(is_active=True).select_related('author', 'thread').order_by('-created_at')[:10]
    
    # Most active users
    active_users = UserActivity.objects.select_related('user').order_by('-post_count')[:10]
    
    # Community statistics
    community_stats = {
        'total_topics': topics.count(),
        'total_threads': Thread.objects.filter(is_active=True).count(),
        'total_posts': Post.objects.filter(is_active=True).count(),
        'total_votes': PostVote.objects.count(),
    }
    
    context = {
        'topics': topics,
        'recent_threads': recent_threads,
        'recent_posts': recent_posts,
        'active_users': active_users,
        'community_stats': community_stats,
    }
    
    return render(request, 'admin_dashboard/community_management.html', context)


@user_passes_test(is_superuser)
def api_management(request):
    """Enhanced API keys and usage management"""
    # API Keys statistics
    total_api_keys = APIKey.objects.count()
    active_api_keys = APIKey.objects.filter(is_active=True).count()
    
    # Recent API usage
    recent_usage = APIUsage.objects.select_related('api_key__user').order_by('-timestamp')[:20]
    
    # Usage statistics by endpoint
    endpoint_stats = APIUsage.objects.values('endpoint').annotate(
        count=Count('id'),
        avg_response_time=Avg('response_time')
    ).order_by('-count')[:10]
    
    # Usage by date (last 7 days)
    seven_days_ago = timezone.now() - timedelta(days=7)
    daily_usage = APIUsage.objects.filter(timestamp__gte=seven_days_ago).extra(
        select={'day': 'date(timestamp)'}
    ).values('day').annotate(count=Count('id')).order_by('day')
    
    # API error statistics
    error_stats = APIUsage.objects.filter(
        timestamp__gte=seven_days_ago,
        status_code__gte=400
    ).values('status_code').annotate(
        count=Count('id')
    ).order_by('-count')
    
    context = {
        'total_api_keys': total_api_keys,
        'active_api_keys': active_api_keys,
        'recent_usage': recent_usage,
        'endpoint_stats': endpoint_stats,
        'daily_usage': list(daily_usage),
        'error_stats': error_stats,
    }
    
    return render(request, 'admin_dashboard/api_management.html', context)


@user_passes_test(is_superuser)
def system_logs(request):
    """Enhanced system logs view"""
    logs = AdminLog.objects.select_related('admin_user', 'affected_user').order_by('-timestamp')
    
    # Filter by action
    action_filter = request.GET.get('action', 'all')
    if action_filter != 'all':
        logs = logs.filter(action=action_filter)
    
    # Filter by model
    model_filter = request.GET.get('model', 'all')
    if model_filter != 'all':
        logs = logs.filter(model_name=model_filter)
    
    # Filter by admin user
    admin_filter = request.GET.get('admin', 'all')
    if admin_filter != 'all':
        logs = logs.filter(admin_user_id=admin_filter)
    
    # Date filter
    date_filter = request.GET.get('date', 'all')
    if date_filter == 'today':
        logs = logs.filter(timestamp__date=timezone.now().date())
    elif date_filter == 'week':
        logs = logs.filter(timestamp__gte=timezone.now() - timedelta(days=7))
    elif date_filter == 'month':
        logs = logs.filter(timestamp__gte=timezone.now() - timedelta(days=30))
    
    # Search by IP address or description
    search_query = request.GET.get('search', '')
    if search_query:
        logs = logs.filter(
            Q(ip_address__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(object_repr__icontains=search_query)
        )
    
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get unique values for filters
    actions = AdminLog.objects.values_list('action', flat=True).distinct()
    models = AdminLog.objects.values_list('model_name', flat=True).distinct()
    admin_users = CustomUser.objects.filter(
        is_superuser=True
    ).values('id', 'email')
    
    context = {
        'page_obj': page_obj,
        'actions': actions,
        'models': models,
        'admin_users': admin_users,
        'action_filter': action_filter,
        'model_filter': model_filter,
        'admin_filter': admin_filter,
        'date_filter': date_filter,
        'search_query': search_query,
    }
    
    return render(request, 'admin_dashboard/system_logs.html', context)


@user_passes_test(is_superuser)
def reports(request):
    """Admin reports management"""
    reports = AdminReport.objects.select_related('generated_by').order_by('-generated_at')
    
    # Filter by report type
    report_type = request.GET.get('type', 'all')
    if report_type != 'all':
        reports = reports.filter(report_type=report_type)
    
    paginator = Paginator(reports, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'report_type': report_type,
        'report_types': AdminReport.REPORT_TYPES,
    }
    
    return render(request, 'admin_dashboard/reports.html', context)


@user_passes_test(is_superuser)
@require_POST
def generate_report(request):
    """Generate a new admin report"""
    report_type = request.POST.get('report_type')
    report_format = request.POST.get('format', 'pdf')
    date_from = request.POST.get('date_from')
    date_to = request.POST.get('date_to')
    
    if not all([report_type, date_from, date_to]):
        messages.error(request, "All fields are required to generate a report.")
        return redirect('admin_dashboard:reports')
    
    try:
        # Create report record
        report = AdminReport.objects.create(
            name=f"{report_type.replace('_', ' ').title()} Report - {timezone.now().strftime('%Y-%m-%d')}",
            report_type=report_type,
            format=report_format,
            generated_by=request.user,
            date_from=date_from,
            date_to=date_to,
            parameters={
                'generated_at': timezone.now().isoformat(),
                'filters': dict(request.POST)
            }
        )
        
        # TODO: Implement actual report generation logic here
        # This would typically involve creating a background task
        # to generate the report file and update the report object
        
        log_admin_action(
            request.user, 'create', 'AdminReport',
            report, f"Generated {report_type} report",
            request=request
        )
        
        messages.success(request, "Report generation started. You'll be notified when it's ready.")
        
    except Exception as e:
        messages.error(request, f"Error generating report: {str(e)}")
    
    return redirect('admin_dashboard:reports')


@user_passes_test(is_superuser)
@require_http_methods(["POST"])
def toggle_user_status(request, user_id):
    """Enhanced toggle user active status"""
    user = get_object_or_404(CustomUser, id=user_id)
    old_status = user.is_active
    user.is_active = not user.is_active
    user.save()
    
    # Create moderation action record
    UserModerationAction.objects.create(
        admin_user=request.user,
        target_user=user,
        action_type='suspension' if not user.is_active else 'warning',
        reason=f"Account {'deactivated' if not user.is_active else 'activated'} by admin",
        is_active=not user.is_active
    )
    
    log_admin_action(
        request.user, 'update', 'CustomUser', user,
        f"Toggled active status from {old_status} to {user.is_active}",
        user, request
    )
    
    status = "activated" if user.is_active else "deactivated"
    messages.success(request, f"User {user.email} has been {status}.")
    
    return redirect('admin_dashboard:user_detail', user_id=user_id)


@user_passes_test(is_superuser)
@require_POST
def verify_user(request, user_id):
    """Verify a user account"""
    user = get_object_or_404(CustomUser, id=user_id)
    user.is_verified = True
    user.save()
    
    log_admin_action(
        request.user, 'user_verification', 'CustomUser', user,
        f"Manually verified user {user.email}",
        user, request
    )
    
    # Create notification for user verification
    AdminNotification.objects.create(
        title="User Verified",
        message=f"User {user.email} has been manually verified.",
        notification_type='success',
        priority='low'
    )
    
    messages.success(request, f"User {user.email} has been verified.")
    return redirect('admin_dashboard:user_detail', user_id=user_id)


@user_passes_test(is_superuser)
def export_data(request):
    """Enhanced export data as CSV"""
    data_type = request.GET.get('type', 'users')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    response = HttpResponse(content_type='text/csv')
    
    if data_type == 'users':
        response['Content-Disposition'] = 'attachment; filename="users_export.csv"'
        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Email', 'Full Name', 'Username', 'Is Active', 
            'Is Verified', 'Is Premium', 'Created At', 'Last Login'
        ])
        
        users = CustomUser.objects.all()
        if date_from:
            users = users.filter(created_at__date__gte=date_from)
        if date_to:
            users = users.filter(created_at__date__lte=date_to)
        
        for user in users:
            writer.writerow([
                user.id, user.email, user.full_name, user.username,
                user.is_active, user.is_verified, 
                getattr(user.userprofile, 'is_premium', False) if hasattr(user, 'userprofile') else False,
                user.created_at, user.last_login
            ])
    
    elif data_type == 'datasets':
        response['Content-Disposition'] = 'attachment; filename="datasets_export.csv"'
        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Title', 'Author', 'Type', 'Rating', 'Downloads', 
            'Is Published', 'Created At', 'Updated At'
        ])
        
        datasets = Dataset.objects.select_related('author')
        if date_from:
            datasets = datasets.filter(created_at__date__gte=date_from)
        if date_to:
            datasets = datasets.filter(created_at__date__lte=date_to)
        
        for dataset in datasets:
            writer.writerow([
                dataset.id, dataset.title, dataset.author.email,
                dataset.dataset_type, dataset.rating, dataset.downloads,
                getattr(dataset, 'is_published', True), 
                dataset.created_at, dataset.updated_at
            ])
    
    elif data_type == 'admin_logs':
        response['Content-Disposition'] = 'attachment; filename="admin_logs_export.csv"'
        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Admin User', 'Action', 'Model', 'Object ID', 
            'Description', 'IP Address', 'Timestamp', 'Affected User'
        ])
        
        logs = AdminLog.objects.select_related('admin_user', 'affected_user')
        if date_from:
            logs = logs.filter(timestamp__date__gte=date_from)
        if date_to:
            logs = logs.filter(timestamp__date__lte=date_to)
        
        for log in logs:
            writer.writerow([
                log.id, log.admin_user.email, log.action, log.model_name,
                log.object_id, log.description, log.ip_address, log.timestamp,
                log.affected_user.email if log.affected_user else ''
            ])
    
    elif data_type == 'token_adjustments':
        response['Content-Disposition'] = 'attachment; filename="token_adjustments_export.csv"'
        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Admin User', 'Target User', 'Adjustment Type', 
            'Amount', 'Reason', 'Created At'
        ])
        
        adjustments = TokenAdjustment.objects.select_related('admin_user', 'target_user')
        if date_from:
            adjustments = adjustments.filter(created_at__date__gte=date_from)
        if date_to:
            adjustments = adjustments.filter(created_at__date__lte=date_to)
        
        for adjustment in adjustments:
            writer.writerow([
                adjustment.id, adjustment.admin_user.email, adjustment.target_user.email,
                adjustment.adjustment_type, adjustment.amount, adjustment.reason,
                adjustment.created_at
            ])
    
    # Log the export action
    log_admin_action(
        request.user, 'export', f'{data_type.title()}Export',
        description=f"Exported {data_type} data",
        request=request
    )
    
    return response


@user_passes_test(is_superuser)
def analytics_api(request):
    """Enhanced API endpoint for dashboard analytics"""
    metric_type = request.GET.get('type', 'users')
    days = int(request.GET.get('days', 30))
    
    start_date = timezone.now() - timedelta(days=days)
    
    if metric_type == 'users':
        # User registration over time
        daily_registrations = CustomUser.objects.filter(
            created_at__gte=start_date
        ).extra(
            select={'day': 'date(created_at)'}
        ).values('day').annotate(count=Count('id')).order_by('day')
        
        return JsonResponse({
            'data': list(daily_registrations),
            'total': CustomUser.objects.filter(created_at__gte=start_date).count()
        })
    
    elif metric_type == 'api_usage':
        # API usage over time
        daily_api_usage = APIUsage.objects.filter(
            timestamp__gte=start_date
        ).extra(
            select={'day': 'date(timestamp)'}
        ).values('day').annotate(count=Count('id')).order_by('day')
        
        return JsonResponse({
            'data': list(daily_api_usage),
            'total': APIUsage.objects.filter(timestamp__gte=start_date).count()
        })
    
    elif metric_type == 'datasets':
        # Dataset creation over time
        daily_datasets = Dataset.objects.filter(
            created_at__gte=start_date
        ).extra(
            select={'day': 'date(created_at)'}
        ).values('day').annotate(count=Count('id')).order_by('day')
        
        return JsonResponse({
            'data': list(daily_datasets),
            'total': Dataset.objects.filter(created_at__gte=start_date).count()
        })
    
    elif metric_type == 'community':
        # Community activity over time
        daily_posts = Post.objects.filter(
            created_at__gte=start_date,
            is_active=True
        ).extra(
            select={'day': 'date(created_at)'}
        ).values('day').annotate(count=Count('id')).order_by('day')
        
        return JsonResponse({
            'data': list(daily_posts),
            'total': Post.objects.filter(created_at__gte=start_date, is_active=True).count()
        })
    
    elif metric_type == 'moderation':
        # Moderation actions over time
        daily_moderation = UserModerationAction.objects.filter(
            created_at__gte=start_date
        ).extra(
            select={'day': 'date(created_at)'}
        ).values('day').annotate(count=Count('id')).order_by('day')
        
        return JsonResponse({
            'data': list(daily_moderation),
            'total': UserModerationAction.objects.filter(created_at__gte=start_date).count()
        })
    
    elif metric_type == 'tokens':
        # Token adjustments over time
        daily_tokens = TokenAdjustment.objects.filter(
            created_at__gte=start_date
        ).extra(
            select={'day': 'date(created_at)'}
        ).values('day').annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        ).order_by('day')
        
        return JsonResponse({
            'data': list(daily_tokens),
            'total_adjustments': TokenAdjustment.objects.filter(created_at__gte=start_date).count(),
            'total_amount': TokenAdjustment.objects.filter(created_at__gte=start_date).aggregate(
                total=Sum('amount')
            )['total'] or 0
        })
    
    return JsonResponse({'error': 'Invalid metric type'})


@user_passes_test(is_superuser)
def dashboard_stats_api(request):
    """API endpoint for real-time dashboard statistics"""
    stats = {
        'users': {
            'total': CustomUser.objects.count(),
            'active': CustomUser.objects.filter(is_active=True).count(),
            'verified': CustomUser.objects.filter(is_verified=True).count(),
            'new_today': CustomUser.objects.filter(
                created_at__date=timezone.now().date()
            ).count()
        },
        'datasets': {
            'total': Dataset.objects.count(),
            'pending_moderation': DatasetModerationQueue.objects.filter(
                status='pending'
            ).count(),
            'approved_today': DatasetModerationQueue.objects.filter(
                status='approved',
                reviewed_at__date=timezone.now().date()
            ).count()
        },
        'community': {
            'total_threads': Thread.objects.filter(is_active=True).count(),
            'total_posts': Post.objects.filter(is_active=True).count(),
            'new_posts_today': Post.objects.filter(
                created_at__date=timezone.now().date(),
                is_active=True
            ).count()
        },
        'api': {
            'total_keys': APIKey.objects.filter(is_active=True).count(),
            'requests_today': APIUsage.objects.filter(
                timestamp__date=timezone.now().date()
            ).count()
        },
        'moderation': {
            'active_actions': UserModerationAction.objects.filter(
                is_active=True
            ).count(),
            'pending_bulk_actions': BulkAction.objects.filter(
                status__in=['pending', 'processing']
            ).count()
        },
        'notifications': {
            'unread': AdminNotification.objects.filter(
                is_read=False
            ).count(),
            'urgent': AdminNotification.objects.filter(
                is_read=False,
                priority='urgent'
            ).count()
        }
    }
    
    return JsonResponse(stats)


@user_passes_test(is_superuser)
@require_POST
def create_notification(request):
    """Create a new admin notification"""
    title = request.POST.get('title')
    message = request.POST.get('message')
    notification_type = request.POST.get('notification_type', 'info')
    priority = request.POST.get('priority', 'medium')
    is_global = request.POST.get('is_global') == 'on'
    expires_at = request.POST.get('expires_at')
    
    try:
        notification = AdminNotification.objects.create(
            title=title,
            message=message,
            notification_type=notification_type,
            priority=priority,
            is_global=is_global,
            expires_at=expires_at if expires_at else None
        )
        
        log_admin_action(
            request.user, 'create', 'AdminNotification',
            notification, f"Created notification: {title}",
            request=request
        )
        
        messages.success(request, "Notification created successfully.")
        
    except Exception as e:
        messages.error(request, f"Error creating notification: {str(e)}")
    
    return redirect('admin_dashboard:notifications')