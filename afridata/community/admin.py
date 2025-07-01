# community/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Sum, Q
from django.utils.safestring import mark_safe
from django.contrib import messages
from django.utils import timezone
from .models import Topic, Thread, Post, PostVote, UserActivity


class ThreadInline(admin.TabularInline):
    """Inline admin for Threads within Topic"""
    model = Thread
    extra = 0
    readonly_fields = ('author', 'views', 'created_at', 'post_count_display')
    fields = ('title', 'author', 'is_pinned', 'is_locked', 'is_active', 'views', 'post_count_display', 'created_at')
    
    def post_count_display(self, obj):
        if obj.pk:
            return obj.get_post_count()
        return 0
    post_count_display.short_description = 'Posts'
    
    def has_add_permission(self, request, obj=None):
        return False  # Prevent adding threads directly from topic admin


class PostInline(admin.TabularInline):
    """Inline admin for Posts within Thread"""
    model = Post
    extra = 0
    readonly_fields = ('author', 'created_at', 'vote_score_display')
    fields = ('author', 'content', 'is_active', 'vote_score_display', 'created_at')
    
    def vote_score_display(self, obj):
        if obj.pk:
            upvotes = obj.votes.filter(vote=1).count()
            downvotes = obj.votes.filter(vote=-1).count()
            return f"+{upvotes} / -{downvotes}"
        return "No votes"
    vote_score_display.short_description = 'Votes'
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    """Enhanced admin interface for Topic"""
    inlines = [ThreadInline]
    
    list_display = (
        'name', 'description_preview', 'color_display', 'icon_display',
        'is_active', 'thread_count_display', 'post_count_display', 
        'latest_activity', 'created_at'
    )
    
    list_filter = ('is_active', 'created_at', 'color')
    search_fields = ('name', 'description')
    list_editable = ('is_active',)
    ordering = ('name',)
    list_per_page = 20
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description')
        }),
        ('Appearance', {
            'fields': ('icon', 'color'),
            'description': 'Icon should be a FontAwesome class (e.g., "fas fa-comments"). Color should be a hex code.'
        }),
        ('Settings', {
            'fields': ('is_active',)
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ('created_at',)
    
    def description_preview(self, obj):
        """Show truncated description"""
        if len(obj.description) > 50:
            return obj.description[:50] + "..."
        return obj.description
    description_preview.short_description = 'Description'
    
    def color_display(self, obj):
        """Display color as colored box"""
        return format_html(
            '<div style="width: 20px; height: 20px; background-color: {}; border: 1px solid #ccc; display: inline-block;"></div> {}',
            obj.color, obj.color
        )
    color_display.short_description = 'Color'
    
    def icon_display(self, obj):
        """Display icon if available"""
        if obj.icon:
            return format_html('<i class="{}"></i> {}', obj.icon, obj.icon)
        return "No icon"
    icon_display.short_description = 'Icon'
    
    def thread_count_display(self, obj):
        """Display thread count"""
        count = obj.get_thread_count()
        return format_html('<strong>{}</strong>', count)
    thread_count_display.short_description = 'Threads'
    thread_count_display.admin_order_field = 'thread_count'
    
    def post_count_display(self, obj):
        """Display post count"""
        count = obj.get_post_count()
        return format_html('<strong>{}</strong>', count)
    post_count_display.short_description = 'Posts'
    
    def latest_activity(self, obj):
        """Display latest post time"""
        latest_post = obj.get_latest_post()
        if latest_post:
            return format_html(
                '<span title="{}">{}</span>',
                latest_post.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                latest_post.created_at.strftime('%m/%d %H:%M')
            )
        return "No activity"
    latest_activity.short_description = 'Latest Activity'
    
    actions = ['activate_topics', 'deactivate_topics']
    
    def activate_topics(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} topics activated.')
    activate_topics.short_description = "Activate selected topics"
    
    def deactivate_topics(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} topics deactivated.')
    deactivate_topics.short_description = "Deactivate selected topics"
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(
            thread_count=Count('threads', filter=Q(threads__is_active=True))
        )


@admin.register(Thread)
class ThreadAdmin(admin.ModelAdmin):
    """Enhanced admin interface for Thread"""
    inlines = [PostInline]
    
    list_display = (
        'title', 'topic_link', 'author_link', 'status_display', 
        'views', 'post_count_display', 'created_at', 'updated_at',
        'is_pinned', 'is_locked', 'is_active'
    )
    
    list_filter = ('is_pinned', 'is_locked', 'is_active', 'topic', 'created_at')
    search_fields = ('title', 'content', 'author__email', 'author__full_name')
    list_editable = ('is_pinned', 'is_locked', 'is_active')  #should also be included in list_display
    ordering = ('-is_pinned', '-updated_at')
    list_per_page = 25
    
    fieldsets = (
        ('Thread Information', {
            'fields': ('title', 'topic', 'author', 'content')
        }),
        ('Settings', {
            'fields': ('is_pinned', 'is_locked', 'is_active')
        }),
        ('Statistics', {
            'fields': ('views',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ('views', 'created_at', 'updated_at')
    
    def topic_link(self, obj):
        """Link to topic admin"""
        url = reverse('admin:community_topic_change', args=[obj.topic.pk])
        return format_html('<a href="{}">{}</a>', url, obj.topic.name)
    topic_link.short_description = 'Topic'
    topic_link.admin_order_field = 'topic__name'
    
    def author_link(self, obj):
        """Link to author admin"""
        url = reverse('admin:accounts_customuser_change', args=[obj.author.pk])
        return format_html('<a href="{}">{}</a>', url, obj.author.email)
    author_link.short_description = 'Author'
    author_link.admin_order_field = 'author__email'
    
    def status_display(self, obj):
        """Display thread status with icons"""
        status = []
        if obj.is_pinned:
            status.append('<span style="color: orange;" title="Pinned">📌</span>')
        if obj.is_locked:
            status.append('<span style="color: red;" title="Locked">🔒</span>')
        if not obj.is_active:
            status.append('<span style="color: gray;" title="Inactive">❌</span>')
        if not status:
            status.append('<span style="color: green;" title="Active">✅</span>')
        return format_html(' '.join(status))
    status_display.short_description = 'Status'
    
    def post_count_display(self, obj):
        """Display post count"""
        count = obj.get_post_count()
        return format_html('<strong>{}</strong>', count)
    post_count_display.short_description = 'Posts'
    
    actions = ['pin_threads', 'unpin_threads', 'lock_threads', 'unlock_threads', 'activate_threads', 'deactivate_threads']
    
    def pin_threads(self, request, queryset):
        updated = queryset.update(is_pinned=True)
        self.message_user(request, f'{updated} threads pinned.')
    pin_threads.short_description = "Pin selected threads"
    
    def unpin_threads(self, request, queryset):
        updated = queryset.update(is_pinned=False)
        self.message_user(request, f'{updated} threads unpinned.')
    unpin_threads.short_description = "Unpin selected threads"
    
    def lock_threads(self, request, queryset):
        updated = queryset.update(is_locked=True)
        self.message_user(request, f'{updated} threads locked.')
    lock_threads.short_description = "Lock selected threads"
    
    def unlock_threads(self, request, queryset):
        updated = queryset.update(is_locked=False)
        self.message_user(request, f'{updated} threads unlocked.')
    unlock_threads.short_description = "Unlock selected threads"
    
    def activate_threads(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} threads activated.')
    activate_threads.short_description = "Activate selected threads"
    
    def deactivate_threads(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} threads deactivated.')
    deactivate_threads.short_description = "Deactivate selected threads"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('topic', 'author')


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    """Enhanced admin interface for Post"""
    list_display = (
        'id', 'thread_link', 'author_link', 'content_preview',
        'vote_score_display', 'is_active', 'created_at'
    )
    
    list_filter = ('is_active', 'created_at', 'thread__topic')
    search_fields = ('content', 'author__email', 'author__full_name', 'thread__title')
    list_editable = ('is_active',)
    ordering = ('-created_at',)
    list_per_page = 30
    
    fieldsets = (
        ('Post Information', {
            'fields': ('thread', 'author', 'content')
        }),
        ('Settings', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def thread_link(self, obj):
        """Link to thread admin"""
        url = reverse('admin:community_thread_change', args=[obj.thread.pk])
        return format_html('<a href="{}">{}</a>', url, obj.thread.title[:30] + "..." if len(obj.thread.title) > 30 else obj.thread.title)
    thread_link.short_description = 'Thread'
    thread_link.admin_order_field = 'thread__title'
    
    def author_link(self, obj):
        """Link to author admin"""
        url = reverse('admin:accounts_customuser_change', args=[obj.author.pk])
        return format_html('<a href="{}">{}</a>', url, obj.author.email)
    author_link.short_description = 'Author'
    author_link.admin_order_field = 'author__email'
    
    def content_preview(self, obj):
        """Show truncated content"""
        if len(obj.content) > 100:
            return obj.content[:100] + "..."
        return obj.content
    content_preview.short_description = 'Content'
    
    def vote_score_display(self, obj):
        """Display vote score with visual indicators"""
        upvotes = obj.votes.filter(vote=1).count()
        downvotes = obj.votes.filter(vote=-1).count()
        score = upvotes - downvotes
        
        if score > 0:
            return format_html('<span style="color: green;">+{} (👍{} 👎{})</span>', score, upvotes, downvotes)
        elif score < 0:
            return format_html('<span style="color: red;">{} (👍{} 👎{})</span>', score, upvotes, downvotes)
        else:
            return format_html('<span style="color: gray;">0 (👍{} 👎{})</span>', upvotes, downvotes)
    vote_score_display.short_description = 'Vote Score'
    
    actions = ['activate_posts', 'deactivate_posts']
    
    def activate_posts(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} posts activated.')
    activate_posts.short_description = "Activate selected posts"
    
    def deactivate_posts(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} posts deactivated.')
    deactivate_posts.short_description = "Deactivate selected posts"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('thread', 'author').prefetch_related('votes')


@admin.register(PostVote)
class PostVoteAdmin(admin.ModelAdmin):
    """Admin interface for PostVote"""
    list_display = ('id', 'post_link', 'user_link', 'vote_display', 'created_at')
    list_filter = ('vote', 'created_at')
    search_fields = ('post__content', 'user__email', 'user__full_name')
    ordering = ('-created_at',)
    list_per_page = 50
    
    readonly_fields = ('created_at',)
    
    def post_link(self, obj):
        """Link to post admin"""
        url = reverse('admin:community_post_change', args=[obj.post.pk])
        content_preview = obj.post.content[:30] + "..." if len(obj.post.content) > 30 else obj.post.content
        return format_html('<a href="{}">{}</a>', url, content_preview)
    post_link.short_description = 'Post'
    
    def user_link(self, obj):
        """Link to user admin"""
        url = reverse('admin:accounts_customuser_change', args=[obj.user.pk])
        return format_html('<a href="{}">{}</a>', url, obj.user.email)
    user_link.short_description = 'User'
    user_link.admin_order_field = 'user__email'
    
    def vote_display(self, obj):
        """Display vote with visual indicator"""
        if obj.vote == 1:
            return format_html('<span style="color: green;">👍 Upvote</span>')
        else:
            return format_html('<span style="color: red;">👎 Downvote</span>')
    vote_display.short_description = 'Vote'
    vote_display.admin_order_field = 'vote'
    
    def has_add_permission(self, request):
        return False  # Votes should only be created through the application
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('post', 'user')


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    """Admin interface for UserActivity"""
    list_display = (
        'user_link', 'last_seen', 'post_count', 'thread_count', 
        'reputation_display', 'activity_level'
    )
    
    list_filter = ('last_seen', 'reputation')
    search_fields = ('user__email', 'user__full_name')
    ordering = ('-last_seen',)
    list_per_page = 30
    
    readonly_fields = ('last_seen',)
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Activity Statistics', {
            'fields': ('post_count', 'thread_count', 'reputation')
        }),
        ('Metadata', {
            'fields': ('last_seen',),
            'classes': ('collapse',)
        })
    )
    
    def user_link(self, obj):
        """Link to user admin"""
        url = reverse('admin:accounts_customuser_change', args=[obj.user.pk])
        return format_html('<a href="{}">{}</a>', url, obj.user.email)
    user_link.short_description = 'User'
    user_link.admin_order_field = 'user__email'
    
    def reputation_display(self, obj):
        """Display reputation with visual indicator"""
        if obj.reputation > 0:
            return format_html('<span style="color: green;">+{}</span>', obj.reputation)
        elif obj.reputation < 0:
            return format_html('<span style="color: red;">{}</span>', obj.reputation)
        else:
            return format_html('<span style="color: gray;">0</span>')
    reputation_display.short_description = 'Reputation'
    reputation_display.admin_order_field = 'reputation'
    
    def activity_level(self, obj):
        """Calculate and display activity level"""
        total_activity = obj.post_count + obj.thread_count
        if total_activity > 100:
            return format_html('<span style="color: gold;">🌟 Very Active</span>')
        elif total_activity > 50:
            return format_html('<span style="color: green;">🔥 Active</span>')
        elif total_activity > 10:
            return format_html('<span style="color: blue;">📝 Moderate</span>')
        else:
            return format_html('<span style="color: gray;">😴 Low</span>')
    activity_level.short_description = 'Activity Level'
    
    actions = ['reset_reputation', 'update_statistics']
    
    def reset_reputation(self, request, queryset):
        updated = queryset.update(reputation=0)
        self.message_user(request, f'Reputation reset for {updated} users.')
    reset_reputation.short_description = "Reset reputation to 0"
    
    def update_statistics(self, request, queryset):
        for activity in queryset:
            activity.update_post_count()
            activity.update_thread_count()
        count = queryset.count()
        self.message_user(request, f'Statistics updated for {count} users.')
    update_statistics.short_description = "Update post/thread counts"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


# Custom admin site configuration
admin.site.site_header = "Community Forum Admin"
admin.site.site_title = "Forum Admin"
admin.site.index_title = "Community Management Dashboard"