'''
This file contains custom filter classes that allow API users to filter and search through data using query parameters like ?country=kenya or ?category=agriculture. It makes your API more powerful by enabling users to narrow down results based on specific criteria.
'''

# api/filters.py
import django_filters
from django.db.models import Q
from dataset.models import Dataset, Comment
from .models import APIUsage

class DatasetFilter(django_filters.FilterSet):
    """Filter for datasets"""
    title = django_filters.CharFilter(lookup_expr='icontains')
    author = django_filters.CharFilter(field_name='author__email', lookup_expr='icontains')
    author_username = django_filters.CharFilter(field_name='author__username', lookup_expr='icontains')
    dataset_type = django_filters.ChoiceFilter(choices=Dataset.DATASET_TYPES)
    topics = django_filters.CharFilter(method='filter_topics')
    rating_min = django_filters.NumberFilter(field_name='rating', lookup_expr='gte')
    rating_max = django_filters.NumberFilter(field_name='rating', lookup_expr='lte')
    downloads_min = django_filters.NumberFilter(field_name='downloads', lookup_expr='gte')
    downloads_max = django_filters.NumberFilter(field_name='downloads', lookup_expr='lte')
    views_min = django_filters.NumberFilter(field_name='views', lookup_expr='gte')
    views_max = django_filters.NumberFilter(field_name='views', lookup_expr='lte')
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    search = django_filters.CharFilter(method='filter_search')
    
    class Meta:
        model = Dataset
        fields = ['title', 'author', 'dataset_type', 'topics']
    
    def filter_topics(self, queryset, name, value):
        """Filter by topics (comma-separated)"""
        if value:
            topics = [topic.strip() for topic in value.split(',')]
            q_objects = Q()
            for topic in topics:
                q_objects |= Q(topics__icontains=topic)
            return queryset.filter(q_objects)
        return queryset
    
    def filter_search(self, queryset, name, value):
        """Search across multiple fields"""
        if value:
            return queryset.filter(
                Q(title__icontains=value) |
                Q(bio__icontains=value) |
                Q(topics__icontains=value) |
                Q(author__full_name__icontains=value) |
                Q(author__username__icontains=value)
            )
        return queryset

class CommentFilter(django_filters.FilterSet):
    """Filter for comments"""
    author = django_filters.CharFilter(field_name='author__email', lookup_expr='icontains')
    author_username = django_filters.CharFilter(field_name='author__username', lookup_expr='icontains')
    dataset = django_filters.NumberFilter(field_name='dataset__id')
    upvotes_min = django_filters.NumberFilter(field_name='upvotes', lookup_expr='gte')
    upvotes_max = django_filters.NumberFilter(field_name='upvotes', lookup_expr='lte')
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    content = django_filters.CharFilter(lookup_expr='icontains')
    
    class Meta:
        model = Comment
        fields = ['author', 'dataset', 'upvotes']

class APIUsageFilter(django_filters.FilterSet):
    """Filter for API usage statistics"""
    endpoint = django_filters.CharFilter(lookup_expr='icontains')
    method = django_filters.ChoiceFilter(choices=[
        ('GET', 'GET'),
        ('POST', 'POST'),
        ('PUT', 'PUT'),
        ('PATCH', 'PATCH'),
        ('DELETE', 'DELETE'),
    ])
    response_code = django_filters.NumberFilter()
    response_code_range = django_filters.CharFilter(method='filter_response_code_range')
    timestamp_after = django_filters.DateTimeFilter(field_name='timestamp', lookup_expr='gte')
    timestamp_before = django_filters.DateTimeFilter(field_name='timestamp', lookup_expr='lte')
    response_time_min = django_filters.NumberFilter(field_name='response_time', lookup_expr='gte')
    response_time_max = django_filters.NumberFilter(field_name='response_time', lookup_expr='lte')
    ip_address = django_filters.CharFilter()
    
    class Meta:
        model = APIUsage
        fields = ['endpoint', 'method', 'response_code', 'ip_address']
    
    def filter_response_code_range(self, queryset, name, value):
        """Filter by response code ranges (e.g., '2xx', '4xx', '5xx')"""
        if value:
            if value.lower() == '2xx':
                return queryset.filter(response_code__range=(200, 299))
            elif value.lower() == '3xx':
                return queryset.filter(response_code__range=(300, 399))
            elif value.lower() == '4xx':
                return queryset.filter(response_code__range=(400, 499))
            elif value.lower() == '5xx':
                return queryset.filter(response_code__range=(500, 599))
        return queryset

class PopularDatasetFilter(django_filters.FilterSet):
    """Filter for popular datasets"""
    time_range = django_filters.CharFilter(method='filter_time_range')
    limit = django_filters.NumberFilter(method='filter_limit')
    
    class Meta:
        model = Dataset
        fields = []
    
    def filter_time_range(self, queryset, name, value):
        """Filter by time range for popularity"""
        # This would be implemented based on your popularity algorithm
        # For now, we'll just return the queryset
        return queryset
    
    def filter_limit(self, queryset, name, value):
        """Limit the number of results"""
        if value:
            return queryset[:value]
        return queryset