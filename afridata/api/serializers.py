'''
This file contains serializer classes that convert Django model instances to JSON format for API responses and handle validation when converting JSON data back to Django models. It acts as the bridge between your Django models and the JSON data that APIs send and receive.
'''
# api/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from dataset.models import Dataset, Comment
from .models import APIKey, APIUsage

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """Serializer for user data"""
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'full_name', 'bio', 'profile_picture', 
                 'date_of_birth', 'is_verified', 'created_at']
        read_only_fields = ['id', 'created_at', 'is_verified']

class CommentSerializer(serializers.ModelSerializer):
    """Serializer for comments"""
    author = UserSerializer(read_only=True)
    author_id = serializers.IntegerField(write_only=True, required=False)
    
    class Meta:
        model = Comment
        fields = ['id', 'author', 'author_id', 'content', 'upvotes', 'created_at']
        read_only_fields = ['id', 'upvotes', 'created_at']

class DatasetSerializer(serializers.ModelSerializer):
    """Serializer for datasets"""
    author = UserSerializer(read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    topics_list = serializers.ListField(read_only=True, source='get_topics_list')
    
    class Meta:
        model = Dataset
        fields = ['id', 'title', 'author', 'file', 'dataset_type', 'bio', 
                 'topics', 'topics_list', 'rating', 'downloads', 'views', 
                 'created_at', 'updated_at', 'comments']
        read_only_fields = ['id', 'author', 'downloads', 'views', 'rating', 
                           'created_at', 'updated_at']

class DatasetCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating datasets"""
    class Meta:
        model = Dataset
        fields = ['title', 'file', 'dataset_type', 'bio', 'topics']
    
    def validate_file(self, value):
        """Validate file upload"""
        if not value:
            raise serializers.ValidationError("File is required")
        
        # Check file extension
        allowed_extensions = ['.csv', '.xlsx', '.xls']
        file_extension = value.name.lower().split('.')[-1]
        if f'.{file_extension}' not in allowed_extensions:
            raise serializers.ValidationError(
                "Only CSV and Excel files are allowed"
            )
        
        # Check file size (max 50MB)
        if value.size > 50 * 1024 * 1024:
            raise serializers.ValidationError(
                "File size must be less than 50MB"
            )
        
        return value

class DatasetUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating datasets"""
    class Meta:
        model = Dataset
        fields = ['title', 'bio', 'topics']

class APIKeySerializer(serializers.ModelSerializer):
    """Serializer for API keys"""
    class Meta:
        model = APIKey
        fields = ['id', 'name', 'key', 'is_active', 'created_at', 'last_used']
        read_only_fields = ['id', 'key', 'created_at', 'last_used']

class APIKeyCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating API keys"""
    class Meta:
        model = APIKey
        fields = ['name']

class APIUsageSerializer(serializers.ModelSerializer):
    """Serializer for API usage statistics"""
    class Meta:
        model = APIUsage
        fields = ['id', 'endpoint', 'method', 'timestamp', 'response_code', 
                 'response_time', 'ip_address']
        read_only_fields = ['id', 'timestamp']

class APIUsageStatsSerializer(serializers.Serializer):
    """Serializer for API usage statistics summary"""
    total_requests = serializers.IntegerField()
    requests_today = serializers.IntegerField()
    requests_this_month = serializers.IntegerField()
    error_rate = serializers.FloatField()
    popular_endpoint = serializers.CharField()
    popular_endpoint_percentage = serializers.FloatField()
    daily_usage = serializers.ListField(child=serializers.DictField())
    
class LoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    email = serializers.EmailField()
    password = serializers.CharField()

class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['email', 'username', 'full_name', 'password', 'password_confirm']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user
