# community/models.py
from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils import timezone

class Topic(models.Model):
    """Forum topics/categories"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(max_length=500)
    icon = models.CharField(max_length=50, blank=True, help_text="FontAwesome icon class")
    color = models.CharField(max_length=7, default="#3498db", help_text="Hex color code")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('community:topic_detail', kwargs={'pk': self.pk})
    
    def get_thread_count(self):
        return self.threads.filter(is_active=True).count()
    
    def get_post_count(self):
        return Post.objects.filter(thread__topic=self, is_active=True).count()
    
    def get_latest_post(self):
        return Post.objects.filter(thread__topic=self, is_active=True).order_by('-created_at').first()

class Thread(models.Model):
    """Forum threads/discussions"""
    title = models.CharField(max_length=255)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='threads')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='threads')
    content = models.TextField()
    is_pinned = models.BooleanField(default=False)
    is_locked = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    views = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_pinned', '-updated_at']
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('community:thread_detail', kwargs={'pk': self.pk})
    
    def get_post_count(self):
        return self.posts.filter(is_active=True).count()
    
    def get_latest_post(self):
        return self.posts.filter(is_active=True).order_by('-created_at').first()
    
    def increment_views(self):
        self.views += 1
        self.save(update_fields=['views'])

class Post(models.Model):
    """Forum posts/replies"""
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name='posts')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='posts')
    content = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Post by {self.author.username} in {self.thread.title}"
    
    def get_absolute_url(self):
        return f"{self.thread.get_absolute_url()}#post-{self.pk}"

class PostVote(models.Model):
    """Voting system for posts"""
    VOTE_CHOICES = [
        (1, 'Upvote'),
        (-1, 'Downvote'),
    ]
    
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='votes')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    vote = models.IntegerField(choices=VOTE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['post', 'user']
    
    def __str__(self):
        return f"{self.user.username} {'upvoted' if self.vote == 1 else 'downvoted'} post in {self.post.thread.title}"

class UserActivity(models.Model):
    """Track user activity in forums"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='forum_activities')
    last_seen = models.DateTimeField(auto_now=True)
    post_count = models.PositiveIntegerField(default=0)
    thread_count = models.PositiveIntegerField(default=0)
    reputation = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.user.username}'s Forum Activity"
    
    def update_post_count(self):
        self.post_count = Post.objects.filter(author=self.user, is_active=True).count()
        self.save(update_fields=['post_count'])
    
    def update_thread_count(self):
        self.thread_count = Thread.objects.filter(author=self.user, is_active=True).count()
        self.save(update_fields=['thread_count'])