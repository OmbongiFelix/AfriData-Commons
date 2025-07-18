# dataset/models.py
from django.db import models
#from django.contrib.auth.models import User    //since i have a custom user model
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

class Dataset(models.Model):
    DATASET_TYPES = [
        ('csv', 'CSV'),
        ('excel', 'Excel'),
        ('pdf', 'PDF'),
        ('txt', 'Text'),
        ('json', 'JSON'),
        ('xml', 'XML'),
        ('zip', 'ZIP Archive'),
        ('yaml', 'YAML'),
        ('parquet', 'Parquet'),
    ]
    
    title = models.CharField(max_length=255)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='authored_datasets')
    file = models.FileField(upload_to='datasets/')
    dataset_type = models.CharField(max_length=20, choices=DATASET_TYPES)  # Increased max_length from 10 to 20
    bio = models.TextField()
    topics = models.CharField(max_length=500, help_text="Comma-separated topics")
    rating = models.FloatField(default=0.0, validators=[MinValueValidator(0.0), MaxValueValidator(5.0)])
    downloads = models.PositiveIntegerField(default=0)
    views = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title
    
    def get_topics_list(self):
        return [topic.strip() for topic in self.topics.split(',') if topic.strip()]

class Comment(models.Model):
    id = models.AutoField(primary_key=True)
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='authored_comments')
    content = models.TextField()
    upvotes = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-upvotes', '-created_at']
    
    def __str__(self):
        return f"Comment by {self.author.username} on {self.dataset.title}"