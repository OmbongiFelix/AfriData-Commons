# home/views.py
from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from dataset.models import Dataset
from django.http import HttpResponse
import json


def default_home(request):
    """Default homepage view"""
    return render(request, 'home/index.html')

def search_datasets(request):
    """
    Search datasets based on user query.
    Searches in title, bio, topics, and author username.
    """
    query = request.GET.get('q', '').strip()
    
    if not query:
        return JsonResponse({
            'success': False,
            'message': 'Search query is required',
            'datasets': []
        })
    
    # Search across multiple fields
    datasets = Dataset.objects.filter(
        Q(title__icontains=query) |
        Q(bio__icontains=query) |
        Q(topics__icontains=query) |
        Q(author__username__icontains=query)
    ).select_related('author').order_by('-created_at')
    
    # Format results
    results = []
    for dataset in datasets:
        # Get first 30 words of bio
        bio_words = dataset.bio.split()[:30]
        short_bio = ' '.join(bio_words) + ('...' if len(dataset.bio.split()) > 30 else '')
        
        results.append({
            'id': dataset.id,
            'title': dataset.title,
            'author': dataset.author.username,
            'short_bio': short_bio,
            'dataset_type': dataset.get_dataset_type_display(),
            'views': dataset.views,
            'downloads': dataset.downloads,
            'rating': dataset.rating,
            'created_at': dataset.created_at.strftime('%Y-%m-%d'),
            'topics': dataset.get_topics_list()
        })
    
    return JsonResponse({
        'success': True,
        'count': len(results),
        'datasets': results
    })

def trending_datasets(request):
    """
    Fetch most viewed or downloaded datasets in the past hour.
    Returns at least 7 datasets with their key attributes.
    """
    # Calculate time one hour ago
    one_hour_ago = timezone.now() - timedelta(hours=1)
    
    # Get datasets updated in the past hour, ordered by views + downloads
    trending = Dataset.objects.filter(
        updated_at__gte=one_hour_ago
    ).select_related('author').extra(
        select={'popularity': 'views + downloads'}
    ).order_by('-popularity', '-views', '-downloads')
    
    # If we don't have enough from the past hour, get top datasets overall
    if trending.count() < 7:
        trending = Dataset.objects.select_related('author').extra(
            select={'popularity': 'views + downloads'}
        ).order_by('-popularity', '-views', '-downloads')
    
    # Take at least 7 datasets
    trending = trending[:max(7, trending.count())]
    
    results = []
    for dataset in trending:
        # Get first 30 words of bio
        bio_words = dataset.bio.split()[:30]
        short_bio = ' '.join(bio_words) + ('...' if len(dataset.bio.split()) > 30 else '')
        
        results.append({
            'id': dataset.id,
            'title': dataset.title,
            'author': dataset.author.username,
            'short_bio': short_bio,
            'dataset_type': dataset.get_dataset_type_display(),
            'views': dataset.views,
            'downloads': dataset.downloads,
            'rating': dataset.rating,
            'created_at': dataset.created_at.strftime('%Y-%m-%d'),
            'popularity_score': dataset.views + dataset.downloads
        })
    
    return JsonResponse({
        'success': True,
        'count': len(results),
        'datasets': results,
        'timeframe': 'past_hour_or_trending'
    })

def filter_datasets(request):
    """
    Filter datasets based on criteria: most_downloaded, most_recent, 
    highest_rating, or most_relevant.
    Returns at least 15 datasets with detailed attributes.
    """
    filter_type = request.GET.get('filter', 'most_recent').lower()
    limit = max(15, int(request.GET.get('limit', 15)))
    
    # Base queryset
    datasets = Dataset.objects.select_related('author')
    
    # Apply filtering based on type
    if filter_type == 'most_downloaded':
        datasets = datasets.order_by('-downloads', '-views')
    elif filter_type == 'most_recent':
        datasets = datasets.order_by('-created_at', '-updated_at')
    elif filter_type == 'highest_rating':
        datasets = datasets.order_by('-rating', '-views', '-downloads')
    elif filter_type == 'most_relevant':
        # Most relevant = combination of rating, views, downloads, and recency
        datasets = datasets.extra(
            select={
                'relevance_score': '''
                    (rating * 0.3) + 
                    (LEAST(views, 1000) * 0.0003) + 
                    (LEAST(downloads, 1000) * 0.0005) + 
                    (CASE 
                        WHEN created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY) THEN 0.2
                        WHEN created_at >= DATE_SUB(NOW(), INTERVAL 90 DAY) THEN 0.1
                        ELSE 0 
                    END)
                '''
            }
        ).order_by('-relevance_score', '-rating', '-views')
    else:
        # Default to most recent
        datasets = datasets.order_by('-created_at')
    
    # Limit results
    datasets = datasets[:limit]
    
    results = []
    for dataset in datasets:
        # Get first 60 words of bio
        bio_words = dataset.bio.split()[:60]
        bio_excerpt = ' '.join(bio_words) + ('...' if len(dataset.bio.split()) > 60 else '')
        
        result = {
            'id': dataset.id,
            'title': dataset.title,
            'author': dataset.author.username,
            'bio': bio_excerpt,
            'dataset_type': dataset.get_dataset_type_display(),
            'type_code': dataset.dataset_type,
            'downloads': dataset.downloads,
            'views': dataset.views,
            'rating': dataset.rating,
            'created_at': dataset.created_at.strftime('%Y-%m-%d %H:%M'),
            'updated_at': dataset.updated_at.strftime('%Y-%m-%d %H:%M'),
            'topics': dataset.get_topics_list(),
            'file_url': dataset.file.url if dataset.file else None
        }
        
        # Add relevance score if it was calculated
        if filter_type == 'most_relevant' and hasattr(dataset, 'relevance_score'):
            result['relevance_score'] = round(dataset.relevance_score, 2)
        
        results.append(result)
    
    return JsonResponse({
        'success': True,
        'filter_type': filter_type,
        'count': len(results),
        'datasets': results
    })

def dataset_stats(request):
    """
    Get overall dataset statistics for the homepage.
    """
    from django.db.models import Sum, Avg, Count
    
    stats = Dataset.objects.aggregate(
        total_datasets=Count('id'),
        total_downloads=Sum('downloads'),
        total_views=Sum('views'),
        avg_rating=Avg('rating')
    )
    
    # Get recent activity (datasets created in last 7 days)
    week_ago = timezone.now() - timedelta(days=7)
    recent_count = Dataset.objects.filter(created_at__gte=week_ago).count()
    
    return JsonResponse({
        'success': True,
        'stats': {
            'total_datasets': stats['total_datasets'] or 0,
            'total_downloads': stats['total_downloads'] or 0,
            'total_views': stats['total_views'] or 0,
            'average_rating': round(stats['avg_rating'] or 0, 2),
            'recent_datasets': recent_count
        }
    })

# Alternative class-based views if you prefer
from django.views.generic import TemplateView
from django.views import View

class HomeView(TemplateView):
    """Class-based view for homepage"""
    template_name = 'home/index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add any context data for the template
        context['page_title'] = 'Dataset Hub - Home'
        return context

class DatasetSearchView(View):
    """Class-based view for dataset searching"""
    
    def get(self, request):
        return search_datasets(request)

class TrendingDatasetsView(View):
    """Class-based view for trending datasets"""
    
    def get(self, request):
        return trending_datasets(request)

class FilterDatasetsView(View):
    """Class-based view for filtering datasets"""
    
    def get(self, request):
        return filter_datasets(request)