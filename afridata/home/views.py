# home/views.py
from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Q, Sum, Avg, Count
from django.utils import timezone
from datetime import timedelta
from dataset.models import Dataset
from django.http import HttpResponse
import json
from django.contrib.auth.decorators import login_required
from collections import Counter
from django.contrib.auth import get_user_model

User = get_user_model()

def default_home(request):
    """
    Enhanced default homepage view with dynamic data.
    Accessible to all users (no login required).
    """
    # Get overall statistics
    stats = Dataset.objects.aggregate(
        total_datasets=Count('id'),
        total_downloads=Sum('downloads'),
        total_views=Sum('views'),
        avg_rating=Avg('rating')
    )
    
    # Calculate total countries (assuming you store country info in topics or bio)
    # This is a simplified approach - you might want to add a country field to your model
    datasets_with_countries = Dataset.objects.filter(
        Q(topics__icontains='Nigeria') | Q(topics__icontains='Kenya') | 
        Q(topics__icontains='South Africa') | Q(topics__icontains='Ghana') |
        Q(topics__icontains='Egypt') | Q(topics__icontains='Ethiopia') |
        Q(topics__icontains='Uganda') | Q(topics__icontains='Tanzania') |
        Q(bio__icontains='Nigeria') | Q(bio__icontains='Kenya') | 
        Q(bio__icontains='South Africa') | Q(bio__icontains='Ghana')
    ).distinct()
    
    total_countries = 54  # Default African countries count
    total_researchers = User.objects.count()
    
    # Get trending datasets (most viewed/downloaded recently)
    one_week_ago = timezone.now() - timedelta(days=7)
    trending_datasets = Dataset.objects.select_related('author').annotate(
        popularity=Count('views') + Count('downloads')
    ).order_by('-views', '-downloads')[:3]
    
    # Get popular topics from all datasets
    all_datasets = Dataset.objects.all()
    topic_counter = Counter()
    
    for dataset in all_datasets:
        topics = dataset.get_topics_list()
        for topic in topics[:3]:  # Take first 3 topics from each dataset
            clean_topic = topic.strip().title()
            if len(clean_topic) > 3:  # Filter out very short topics
                topic_counter[clean_topic] += 1
    
    # Get top 5 topics
    top_topics = topic_counter.most_common(5)
    
    # If we don't have enough topics, add some defaults
    default_topics = [
        ('Climate Change', 150), ('Healthcare', 120), ('Economics', 98), 
        ('Agriculture', 87), ('Education', 76)
    ]
    
    if len(top_topics) < 4:
        top_topics.extend(default_topics)
    
    # Get featured datasets (highest rated and most downloaded)
    featured_datasets = Dataset.objects.select_related('author').annotate(
        combined_score=(Count('downloads') * 0.6 + Count('views') * 0.4)
    ).order_by('-rating', '-combined_score')[:3]
    
    # Get popular search terms (simplified - you might want to track actual searches)
    popular_terms = []
    if all_datasets.exists():
        # Extract some terms from dataset titles and topics
        for dataset in all_datasets[:20]:
            words = dataset.title.split()
            topics = dataset.get_topics_list()
            
            # Add relevant words from titles
            for word in words:
                if len(word) > 4 and word.lower() not in ['data', 'dataset', 'analysis']:
                    popular_terms.append(word.title())
            
            # Add topics
            for topic in topics[:2]:
                if len(topic.strip()) > 3:
                    popular_terms.append(topic.strip().title())
    
    # Remove duplicates and get top 5
    popular_terms = list(set(popular_terms))[:5]
    
    # Default terms if not enough data
    if len(popular_terms) < 5:
        default_terms = ['Nigeria GDP', 'Kenya Agriculture', 'South Africa Mining', 
                        'Egypt Tourism', 'Ethiopia Demographics']
        popular_terms.extend(default_terms)
    
    context = {
        # Statistics
        'total_datasets': stats['total_datasets'] or 0,
        'total_countries': total_countries,
        'total_downloads': stats['total_downloads'] or 0,
        'total_researchers': total_researchers,
        
        # Trending datasets
        'trending_datasets': trending_datasets,
        
        # Popular topics with search counts (simulated)
        'topic_1': top_topics[0][0] if len(top_topics) > 0 else 'Climate Change',
        'topic_1_searches': f"{top_topics[0][1] * 100:.1f}K" if len(top_topics) > 0 else '15.2K',
        'topic_2': top_topics[1][0] if len(top_topics) > 1 else 'Healthcare',
        'topic_2_searches': f"{top_topics[1][1] * 80:.1f}K" if len(top_topics) > 1 else '12.8K',
        'topic_3': top_topics[2][0] if len(top_topics) > 2 else 'Economics',
        'topic_3_searches': f"{top_topics[2][1] * 60:.1f}K" if len(top_topics) > 2 else '9.4K',
        'topic_4': top_topics[3][0] if len(top_topics) > 3 else 'Agriculture',
        'topic_4_searches': f"{top_topics[3][1] * 40:.1f}K" if len(top_topics) > 3 else '7.9K',
        
        # Popular search terms
        'term_1': popular_terms[0] if len(popular_terms) > 0 else 'Nigeria GDP',
        'term_2': popular_terms[1] if len(popular_terms) > 1 else 'Kenya Agriculture',
        'term_3': popular_terms[2] if len(popular_terms) > 2 else 'South Africa Mining',
        'term_4': popular_terms[3] if len(popular_terms) > 3 else 'Egypt Tourism',
        'term_5': popular_terms[4] if len(popular_terms) > 4 else 'Ethiopia Demographics',
        
        # Featured datasets
        'featured_datasets': featured_datasets,
        
        # Category counts (you might want to add categories to your model)
        'category_counts': {
            'healthcare': Dataset.objects.filter(
                Q(topics__icontains='health') | Q(bio__icontains='health') |
                Q(topics__icontains='medical') | Q(bio__icontains='medical')
            ).count(),
            'climate': Dataset.objects.filter(
                Q(topics__icontains='climate') | Q(bio__icontains='climate') |
                Q(topics__icontains='environment') | Q(bio__icontains='environment')
            ).count(),
            'economics': Dataset.objects.filter(
                Q(topics__icontains='economic') | Q(bio__icontains='economic') |
                Q(topics__icontains='finance') | Q(bio__icontains='finance') |
                Q(topics__icontains='gdp') | Q(bio__icontains='gdp')
            ).count(),
            'social': Dataset.objects.filter(
                Q(topics__icontains='social') | Q(bio__icontains='social') |
                Q(topics__icontains='demographic') | Q(bio__icontains='demographic')
            ).count(),
            'agriculture': Dataset.objects.filter(
                Q(topics__icontains='agriculture') | Q(bio__icontains='agriculture') |
                Q(topics__icontains='farming') | Q(bio__icontains='farming')
            ).count(),
            'education': Dataset.objects.filter(
                Q(topics__icontains='education') | Q(bio__icontains='education') |
                Q(topics__icontains='school') | Q(bio__icontains='school')
            ).count(),
            'technology': Dataset.objects.filter(
                Q(topics__icontains='technology') | Q(bio__icontains='technology') |
                Q(topics__icontains='tech') | Q(bio__icontains='tech')
            ).count(),
        },
        
        # File format counts
        'format_counts': {
            'csv': Dataset.objects.filter(dataset_type='csv').count(),
            'excel': Dataset.objects.filter(dataset_type='excel').count(),
        }
    }
    
    return render(request, 'home/index.html', context)


# Keep all your existing API functions as they are
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


def api_docs(request):
    """API documentation page"""
    return render(request, 'home/api_docs.html')


def quick_search_suggestions(request):
    """
    Get quick search suggestions based on popular topics and datasets
    """
    # Get top topics from datasets
    datasets = Dataset.objects.all()[:100]  # Limit for performance
    topic_counter = Counter()
    
    for dataset in datasets:
        topics = dataset.get_topics_list()
        for topic in topics:
            topic_counter[topic.strip().title()] += 1
    
    # Get most common topics
    suggestions = [topic for topic, count in topic_counter.most_common(10)]
    
    # Add some default suggestions if not enough data
    default_suggestions = [
        'Nigeria Economy', 'Kenya Healthcare', 'South Africa Mining',
        'Ghana Agriculture', 'Egypt Demographics', 'Ethiopia Climate'
    ]
    
    if len(suggestions) < 6:
        suggestions.extend(default_suggestions)
    
    return JsonResponse({
        'success': True,
        'suggestions': suggestions[:8]  # Return top 8 suggestions
    })