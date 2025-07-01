# dataset/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Avg
from django.utils.safestring import mark_safe
from django.contrib import messages
from .models import Dataset, Comment


class CommentInline(admin.TabularInline):
    """Inline admin for Comments on Dataset detail page"""
    model = Comment
    extra = 0
    readonly_fields = ('author', 'created_at', 'upvotes')
    fields = ('author', 'content', 'upvotes', 'created_at')
    
    def has_add_permission(self, request, obj=None):
        return False  # Prevent adding comments directly from dataset admin


@admin.register(Dataset)
class DatasetAdmin(admin.ModelAdmin):
    """Enhanced admin interface for Dataset"""
    inlines = [CommentInline]
    
    # Fields to display in the dataset list
    list_display = (
        'title', 'author_link', 'dataset_type', 'rating_display', 
        'downloads', 'views', 'comment_count', 'topics_preview', 
        'created_at', 'file_link'
    )
    
    # Fields that can be searched
    search_fields = ('title', 'bio', 'topics', 'author__email', 'author__full_name')
    
    # Filters in the right sidebar
    list_filter = ('dataset_type', 'created_at', 'rating', 'author')
    
    # Fields that are clickable links to the detail page
    list_display_links = ('title',)
    
    # Number of items per page
    list_per_page = 20
    
    # Default ordering
    ordering = ('-created_at',)
    
    # Fields that can be edited directly from list view
    list_editable = ('rating',)
    
    # Fields layout in the detail/edit form
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'author', 'bio')
        }),
        ('File Information', {
            'fields': ('file', 'dataset_type')
        }),
        ('Categorization', {
            'fields': ('topics',),
            'description': 'Enter topics separated by commas (e.g., "machine learning, data science, python")'
        }),
        ('Statistics', {
            'fields': ('rating', 'downloads', 'views'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    # Read-only fields
    readonly_fields = ('created_at', 'updated_at', 'downloads', 'views')
    
    # Custom methods for list display
    def author_link(self, obj):
        """Display author with link to user admin"""
        url = reverse('admin:accounts_customuser_change', args=[obj.author.pk])
        return format_html('<a href="{}">{}</a>', url, obj.author.email)
    author_link.short_description = 'Author'
    author_link.admin_order_field = 'author__email'
    
    def rating_display(self, obj):
        """Display rating with stars"""
        stars = '★' * int(obj.rating) + '☆' * (5 - int(obj.rating))
        return format_html(
            '<span title="{}/5">{}</span>',
            obj.rating,
            stars
        )
    rating_display.short_description = 'Rating'
    rating_display.admin_order_field = 'rating'
    
    def topics_preview(self, obj):
        """Display first few topics"""
        topics = obj.get_topics_list()
        if not topics:
            return "No topics"
        preview = ', '.join(topics[:3])
        if len(topics) > 3:
            preview += f" (+{len(topics) - 3} more)"
        return preview
    topics_preview.short_description = 'Topics'
    
    def comment_count(self, obj):
        """Display number of comments"""
        count = obj.comments.count()
        if count > 0:
            return format_html(
                '<span style="color: blue;">{} comments</span>',
                count
            )
        return "No comments"
    comment_count.short_description = 'Comments'
    
    def file_link(self, obj):
        """Display download link for the file"""
        if obj.file:
            return format_html(
                '<a href="{}" target="_blank">📁 Download</a>',
                obj.file.url
            )
        return "No file"
    file_link.short_description = 'File'
    
    # Custom actions
    actions = ['reset_downloads', 'reset_views', 'increment_downloads']
    
    def reset_downloads(self, request, queryset):
        """Reset download count to 0"""
        updated = queryset.update(downloads=0)
        self.message_user(request, f'Download count reset for {updated} datasets.')
    reset_downloads.short_description = "Reset download count"
    
    def reset_views(self, request, queryset):
        """Reset view count to 0"""
        updated = queryset.update(views=0)
        self.message_user(request, f'View count reset for {updated} datasets.')
    reset_views.short_description = "Reset view count"
    
    def increment_downloads(self, request, queryset):
        """Increment download count by 1 (for testing purposes)"""
        for dataset in queryset:
            dataset.downloads += 1
            dataset.save()
        count = queryset.count()
        self.message_user(request, f'Download count incremented for {count} datasets.')
    increment_downloads.short_description = "Increment download count (+1)"
    
    # Override queryset to add annotations for better performance
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('author').annotate(
            comment_count_annotation=Count('comments')
        )


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """Enhanced admin interface for Comment"""
    list_display = (
        'id', 'dataset_link', 'author_link', 'content_preview', 
        'upvotes_display', 'created_at'
    )
    
    list_filter = ('created_at', 'upvotes', 'dataset__dataset_type')
    search_fields = ('content', 'author__email', 'author__full_name', 'dataset__title')
    
    # Default ordering
    ordering = ('-created_at',)
    
    # Fields that can be edited directly from list view
    list_editable = ('upvotes',)
    
    # Number of items per page
    list_per_page = 25
    
    # Fields layout in the detail/edit form
    fieldsets = (
        ('Comment Information', {
            'fields': ('dataset', 'author', 'content')
        }),
        ('Statistics', {
            'fields': ('upvotes',)
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    # Read-only fields
    readonly_fields = ('created_at',)
    
    # Custom methods for list display
    def dataset_link(self, obj):
        """Display dataset title with link to dataset admin"""
        url = reverse('admin:dataset_dataset_change', args=[obj.dataset.pk])
        return format_html('<a href="{}">{}</a>', url, obj.dataset.title)
    dataset_link.short_description = 'Dataset'
    dataset_link.admin_order_field = 'dataset__title'
    
    def author_link(self, obj):
        """Display author with link to user admin"""
        url = reverse('admin:accounts_customuser_change', args=[obj.author.pk])
        return format_html('<a href="{}">{}</a>', url, obj.author.email)
    author_link.short_description = 'Author'
    author_link.admin_order_field = 'author__email'
    
    def content_preview(self, obj):
        """Display truncated content"""
        if len(obj.content) > 50:
            return obj.content[:50] + "..."
        return obj.content
    content_preview.short_description = 'Content'
    
    def upvotes_display(self, obj):
        """Display upvotes with thumbs up icon"""
        if obj.upvotes > 0:
            return format_html(
                '<span style="color: green;">👍 {}</span>',
                obj.upvotes
            )
        return "0"
    upvotes_display.short_description = 'Upvotes'
    upvotes_display.admin_order_field = 'upvotes'
    
    # Custom actions
    actions = ['reset_upvotes', 'add_upvote', 'feature_comments']
    
    def reset_upvotes(self, request, queryset):
        """Reset upvotes to 0"""
        updated = queryset.update(upvotes=0)
        self.message_user(request, f'Upvotes reset for {updated} comments.')
    reset_upvotes.short_description = "Reset upvotes to 0"
    
    def add_upvote(self, request, queryset):
        """Add one upvote to selected comments"""
        for comment in queryset:
            comment.upvotes += 1
            comment.save()
        count = queryset.count()
        self.message_user(request, f'Added 1 upvote to {count} comments.')
    add_upvote.short_description = "Add 1 upvote"
    
    def feature_comments(self, request, queryset):
        """Add 10 upvotes to feature selected comments"""
        for comment in queryset:
            comment.upvotes += 10
            comment.save()
        count = queryset.count()
        self.message_user(request, f'Featured {count} comments (+10 upvotes each).')
    feature_comments.short_description = "Feature comments (+10 upvotes)"
    
    # Override queryset for better performance
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('author', 'dataset')


# Custom admin site configuration
admin.site.site_header = "Dataset Management Admin"
admin.site.site_title = "Dataset Admin"
admin.site.index_title = "Dataset & Comment Administration"

