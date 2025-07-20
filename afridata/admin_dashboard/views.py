# admin_dashboard/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.db.models import Count, Q, Avg, Sum
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.core.paginator import Paginator
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
import csv
from datetime import datetime, timedelta

# Import your models
from accounts.models import CustomUser, UserProfile, LoginAttempt
from api.models import APIKey, APIUsage
from community.models import Topic, Thread, Post, PostVote, UserActivity
from dataset.models import Dataset, Comment
from .models import AdminLog, DashboardSettings, SystemMetrics, AdminNotification, BulkAction


def is_superuser(user):
    """Check if user is superuser"""
    return user.is_authenticated and user.is_superuser


@user_passes_test(is_superuser)
def dashboard_home(request):
    """Main dashboard view with statistics"""
    # Get basic statistics
    total_users = CustomUser.objects.count()
    active_users = CustomUser.objects.filter(is_active=True).count()
    verified_users = CustomUser.objects.filter(is_verified=True).count()
    
    total_datasets = Dataset.objects.count()
    total_api_keys = APIKey.objects.filter(is_active=True).count()
    total_threads = Thread.objects.filter(is_active=True).count()
    total_posts = Post.objects.filter(is_active=True).count()
    
    # Recent activity
    recent_users = CustomUser.objects.order_by('-created_at')[:5]
    recent_datasets = Dataset.objects.order_by('-created_at')[:5]
    recent_threads = Thread.objects.filter(is_active=True).order_by('-created_at')[:5]
    
    # Login attempts in last 24 hours
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
    
    # Unread notifications
    unread_notifications = AdminNotification.objects.filter(is_read=False).count()
    
    context = {
        'total_users': total_users,
        'active_users': active_users,
        'verified_users': verified_users,
        'total_datasets': total_datasets,
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
    }
    
    return render(request, 'admin_dashboard/dashboard.html', context)


@user_passes_test(is_superuser)
def user_management(request):
    """User management view"""
    search_query = request.GET.get('search', '')
    filter_type = request.GET.get('filter', 'all')
    
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
    
    users = users.order_by('-created_at')
    
    paginator = Paginator(users, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'filter_type': filter_type,
        'total_users': users.count(),
    }
    
    return render(request, 'admin_dashboard/user_management.html', context)


@user_passes_test(is_superuser)
def user_detail(request, user_id):
    """Detailed view of a specific user"""
    user = get_object_or_404(CustomUser, id=user_id)
    
    # Get user's datasets
    user_datasets = Dataset.objects.filter(author=user).order_by('-created_at')
    
    # Get user's API keys
    user_api_keys = APIKey.objects.filter(user=user).order_by('-created_at')
    
    # Get user's forum activity
    user_threads = Thread.objects.filter(author=user, is_active=True).order_by('-created_at')
    user_posts = Post.objects.filter(author=user, is_active=True).order_by('-created_at')
    
    # Get recent login attempts
    login_attempts = LoginAttempt.objects.filter(email=user.email).order_by('-timestamp')[:10]
    
    context = {
        'user_obj': user,
        'user_datasets': user_datasets,
        'user_api_keys': user_api_keys,
        'user_threads': user_threads,
        'user_posts': user_posts,
        'login_attempts': login_attempts,
    }
    
    return render(request, 'admin_dashboard/user_detail.html', context)


@user_passes_test(is_superuser)
def dataset_management(request):
    """Dataset management view"""
    search_query = request.GET.get('search', '')
    dataset_type = request.GET.get('type', 'all')
    
    datasets = Dataset.objects.all().select_related('author')
    
    if search_query:
        datasets = datasets.filter(
            Q(title__icontains=search_query) |
            Q(bio__icontains=search_query) |
            Q(topics__icontains=search_query)
        )
    
    if dataset_type != 'all':
        datasets = datasets.filter(dataset_type=dataset_type)
    
    datasets = datasets.order_by('-created_at')
    
    paginator = Paginator(datasets, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get dataset type choices for filter
    dataset_types = Dataset.DATASET_TYPES
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'dataset_type': dataset_type,
        'dataset_types': dataset_types,
        'total_datasets': datasets.count(),
    }
    
    return render(request, 'admin_dashboard/dataset_management.html', context)


@user_passes_test(is_superuser)
def community_management(request):
    """Community/forum management view"""
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
    
    context = {
        'topics': topics,
        'recent_threads': recent_threads,
        'recent_posts': recent_posts,
        'active_users': active_users,
    }
    
    return render(request, 'admin_dashboard/community_management.html', context)


@user_passes_test(is_superuser)
def api_management(request):
    """API keys and usage management"""
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
    
    context = {
        'total_api_keys': total_api_keys,
        'active_api_keys': active_api_keys,
        'recent_usage': recent_usage,
        'endpoint_stats': endpoint_stats,
        'daily_usage': list(daily_usage),
    }
    
    return render(request, 'admin_dashboard/api_management.html', context)


@user_passes_test(is_superuser)
def system_logs(request):
    """System logs view"""
    logs = AdminLog.objects.select_related('admin_user').order_by('-timestamp')
    
    # Filter by action
    action_filter = request.GET.get('action', 'all')
    if action_filter != 'all':
        logs = logs.filter(action=action_filter)
    
    # Filter by model
    model_filter = request.GET.get('model', 'all')
    if model_filter != 'all':
        logs = logs.filter(model_name=model_filter)
    
    # Date filter
    date_filter = request.GET.get('date', 'all')
    if date_filter == 'today':
        logs = logs.filter(timestamp__date=timezone.now().date())
    elif date_filter == 'week':
        logs = logs.filter(timestamp__gte=timezone.now() - timedelta(days=7))
    elif date_filter == 'month':
        logs = logs.filter(timestamp__gte=timezone.now() - timedelta(days=30))
    
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get unique actions and models for filters
    actions = AdminLog.objects.values_list('action', flat=True).distinct()
    models = AdminLog.objects.values_list('model_name', flat=True).distinct()
    
    context = {
        'page_obj': page_obj,
        'actions': actions,
        'models': models,
        'action_filter': action_filter,
        'model_filter': model_filter,
        'date_filter': date_filter,
    }
    
    return render(request, 'admin_dashboard/system_logs.html', context)


@user_passes_test(is_superuser)
@require_http_methods(["POST"])
def toggle_user_status(request, user_id):
    """Toggle user active status"""
    user = get_object_or_404(CustomUser, id=user_id)
    user.is_active = not user.is_active
    user.save()
    
    # Log the action
    AdminLog.objects.create(
        admin_user=request.user,
        action='update',
        model_name='CustomUser',
        object_id=str(user.id),
        object_repr=str(user),
        description=f"Toggled active status to {user.is_active}",
        ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1')
    )
    
    status = "activated" if user.is_active else "deactivated"
    messages.success(request, f"User {user.email} has been {status}.")
    
    return redirect('admin_dashboard:user_detail', user_id=user_id)


@user_passes_test(is_superuser)
def export_data(request):
    """Export data as CSV"""
    data_type = request.GET.get('type', 'users')
    
    response = HttpResponse(content_type='text/csv')
    
    if data_type == 'users':
        response['Content-Disposition'] = 'attachment; filename="users_export.csv"'
        writer = csv.writer(response)
        writer.writerow(['ID', 'Email', 'Full Name', 'Is Active', 'Is Verified', 'Created At'])
        
        for user in CustomUser.objects.all():
            writer.writerow([
                user.id, user.email, user.full_name, 
                user.is_active, user.is_verified, user.created_at
            ])
    
    elif data_type == 'datasets':
        response['Content-Disposition'] = 'attachment; filename="datasets_export.csv"'
        writer = csv.writer(response)
        writer.writerow(['ID', 'Title', 'Author', 'Type', 'Rating', 'Downloads', 'Created At'])
        
        for dataset in Dataset.objects.select_related('author'):
            writer.writerow([
                dataset.id, dataset.title, dataset.author.email,
                dataset.dataset_type, dataset.rating, dataset.downloads, dataset.created_at
            ])
    
    return response


@user_passes_test(is_superuser)
def analytics_api(request):
    """API endpoint for dashboard analytics"""
    metric_type = request.GET.get('type', 'users')
    
    if metric_type == 'users':
        # User registration over time (last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        daily_registrations = CustomUser.objects.filter(
            created_at__gte=thirty_days_ago
        ).extra(
            select={'day': 'date(created_at)'}
        ).values('day').annotate(count=Count('id')).order_by('day')
        
        return JsonResponse({'data': list(daily_registrations)})
    
    elif metric_type == 'api_usage':
        # API usage over time (last 7 days)
        seven_days_ago = timezone.now() - timedelta(days=7)
        daily_api_usage = APIUsage.objects.filter(
            timestamp__gte=seven_days_ago
        ).extra(
            select={'day': 'date(timestamp)'}
        ).values('day').annotate(count=Count('id')).order_by('day')
        
        return JsonResponse({'data': list(daily_api_usage)})
    
    return JsonResponse({'error': 'Invalid metric type'})