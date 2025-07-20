#api/views.py
#Handle API logic
from rest_framework import viewsets, generics, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.authentication import SessionAuthentication
from django.contrib.auth import authenticate, login
from django.db.models import Count, Q, Avg
from django.utils import timezone
from datetime import timedelta
from django.db.models.functions import TruncDate
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from dataset.models import Dataset, Comment
from .models import APIKey, APIUsage
from .serializers import (
    DatasetSerializer, DatasetCreateSerializer, DatasetUpdateSerializer,
    CommentSerializer, UserSerializer, APIKeySerializer, APIKeyCreateSerializer,
    APIUsageSerializer, APIUsageStatsSerializer, LoginSerializer, RegisterSerializer
)
from .permissions import (
    APIKeyAuthentication, IsOwnerOrReadOnly, IsOwner, 
    CanCreateDataset, RateLimitPermission
)
from .pagination import (
    StandardResultsSetPagination, LargeResultsSetPagination, 
    APIKeyPagination, UsagePagination
)
from .filters import DatasetFilter, CommentFilter, APIUsageFilter
from .utils import log_api_usage

class DatasetViewSet(viewsets.ModelViewSet):
    """ViewSet for datasets"""
    queryset = Dataset.objects.all().select_related('author').prefetch_related('comments')
    serializer_class = DatasetSerializer
    authentication_classes = [APIKeyAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly, CanCreateDataset, IsOwnerOrReadOnly]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = DatasetFilter
    search_fields = ['title', 'bio', 'topics', 'author__full_name']
    ordering_fields = ['created_at', 'updated_at', 'downloads', 'views', 'rating']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return DatasetCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return DatasetUpdateSerializer
        return DatasetSerializer
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # Increment views count
        instance.views += 1
        instance.save(update_fields=['views'])
        return super().retrieve(request, *args, **kwargs)
    
    @action(detail=False, methods=['get'])
    def popular(self, request):
        """Get popular datasets"""
        # Get datasets with high downloads and views
        popular_datasets = self.queryset.annotate(
            popularity_score=Count('downloads') + Count('views')
        ).order_by('-popularity_score')[:20]
        
        serializer = self.get_serializer(popular_datasets, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def trending(self, request):
        """Get trending datasets (popular in last 7 days)"""
        week_ago = timezone.now() - timedelta(days=7)
        trending_datasets = self.queryset.filter(
            created_at__gte=week_ago
        ).order_by('-downloads', '-views')[:10]
        
        serializer = self.get_serializer(trending_datasets, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def download(self, request, pk=None):
        """Track dataset download"""
        dataset = self.get_object()
        dataset.downloads += 1
        dataset.save(update_fields=['downloads'])
        
        return Response({
            'message': 'Download tracked',
            'download_url': dataset.file.url if dataset.file else None
        })

class CommentViewSet(viewsets.ModelViewSet):
    """ViewSet for comments"""
    queryset = Comment.objects.all().select_related('author', 'dataset')
    serializer_class = CommentSerializer
    authentication_classes = [APIKeyAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = CommentFilter
    ordering_fields = ['created_at', 'upvotes']
    ordering = ['-upvotes', '-created_at']
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
    
    @action(detail=True, methods=['post'])
    def upvote(self, request, pk=None):
        """Upvote a comment"""
        comment = self.get_object()
        comment.upvotes += 1
        comment.save(update_fields=['upvotes'])
        
        return Response({
            'message': 'Comment upvoted',
            'upvotes': comment.upvotes
        })

class UserProfileView(generics.RetrieveUpdateAPIView):
    """View for user profile"""
    serializer_class = UserSerializer
    authentication_classes = [APIKeyAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user

class APIKeyViewSet(viewsets.ModelViewSet):
    """ViewSet for API key management"""
    serializer_class = APIKeySerializer
    authentication_classes = [SessionAuthentication]  # Only session auth for API key management
    permission_classes = [IsAuthenticated, IsOwner]
    pagination_class = APIKeyPagination
    
    def get_queryset(self):
        return APIKey.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return APIKeyCreateSerializer
        return APIKeySerializer
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def revoke(self, request, pk=None):
        """Revoke an API key"""
        api_key = self.get_object()
        api_key.is_active = False
        api_key.save(update_fields=['is_active'])
        
        return Response({'message': 'API key revoked'})

class APIUsageStatsView(generics.RetrieveAPIView):
    """View for API usage statistics"""
    serializer_class = APIUsageStatsSerializer
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        user = self.request.user
        now = timezone.now()
        today = now.date()
        month_start = today.replace(day=1)
        
        # Get user's API keys
        user_api_keys = APIKey.objects.filter(user=user)
        
        # Get usage stats
        usage_queryset = APIUsage.objects.filter(api_key__in=user_api_keys)
        
        total_requests = usage_queryset.count()
        requests_today = usage_queryset.filter(timestamp__date=today).count()
        requests_this_month = usage_queryset.filter(timestamp__date__gte=month_start).count()
        
        # Error rate
        error_requests = usage_queryset.filter(response_code__gte=400).count()
        error_rate = (error_requests / total_requests * 100) if total_requests > 0 else 0
        
        # Popular endpoint
        popular_endpoint_data = usage_queryset.values('endpoint').annotate(
            count=Count('id')
        ).order_by('-count').first()
        
        popular_endpoint = popular_endpoint_data['endpoint'] if popular_endpoint_data else ''
        popular_endpoint_percentage = (
            popular_endpoint_data['count'] / total_requests * 100 
            if popular_endpoint_data and total_requests > 0 else 0
        )
        
        # Daily usage for last 30 days
        thirty_days_ago = now - timedelta(days=30)
        daily_usage = usage_queryset.filter(
            timestamp__gte=thirty_days_ago
        ).annotate(
            date=TruncDate('timestamp')
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date')
        
        return {
            'total_requests': total_requests,
            'requests_today': requests_today,
            'requests_this_month': requests_this_month,
            'error_rate': round(error_rate, 2),
            'popular_endpoint': popular_endpoint,
            'popular_endpoint_percentage': round(popular_endpoint_percentage, 2),
            'daily_usage': list(daily_usage)
        }

class APIUsageViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for API usage records"""
    serializer_class = APIUsageSerializer
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    pagination_class = UsagePagination
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = APIUsageFilter
    ordering_fields = ['timestamp', 'response_time', 'response_code']
    ordering = ['-timestamp']
    
    def get_queryset(self):
        user_api_keys = APIKey.objects.filter(user=self.request.user)
        return APIUsage.objects.filter(api_key__in=user_api_keys)

class AuthViewSet(viewsets.GenericViewSet):
    """ViewSet for authentication"""
    authentication_classes = [SessionAuthentication]
    
    @action(detail=False, methods=['post'])
    def login(self, request):
        """Login user"""
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            
            user = authenticate(request, username=email, password=password)
            if user:
                login(request, user)
                return Response({
                    'message': 'Login successful',
                    'user': UserSerializer(user).data
                })
            else:
                return Response(
                    {'error': 'Invalid credentials'}, 
                    status=status.HTTP_401_UNAUTHORIZED
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def register(self, request):
        """Register new user"""
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'message': 'Registration successful',
                'user': UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def logout(self, request):
        """Logout user"""
        from django.contrib.auth import logout
        logout(request)
        return Response({'message': 'Logout successful'})

class PublicStatsView(generics.RetrieveAPIView):
    """Public API statistics"""
    authentication_classes = [APIKeyAuthentication, SessionAuthentication]
    permission_classes = []  # Public endpoint
    
    def get(self, request):
        """Get public API statistics"""
        total_datasets = Dataset.objects.count()
        total_users = Dataset.objects.values('author').distinct().count()
        total_downloads = Dataset.objects.aggregate(
            total=models.Sum('downloads')
        )['total'] or 0
        
        popular_topics = Dataset.objects.values('topics').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        return Response({
            'total_datasets': total_datasets,
            'total_users': total_users,
            'total_downloads': total_downloads,
            'popular_topics': popular_topics
        })
            