# dataset/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, Http404, JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum
from django.utils import timezone
from datetime import timedelta
from .models import Dataset, Comment
import pandas as pd
import numpy as np
import io
from django.views.decorators.csrf import csrf_exempt
from .forms import DatasetUploadForm
import json
from django.http import JsonResponse
from django.urls import reverse


def dataset_detail(request, dataset_id):
    """View to display dataset details and bio with enhanced functionality"""
    dataset = get_object_or_404(Dataset, id=dataset_id)
   
    # Increment view count
    dataset.views += 1
    dataset.save(update_fields=['views'])
   
    # Get preview data
    preview_data = []
    columns = []
    graph_data = None
    error_message = None
    
    try:
        # Read dataset file for preview
        if dataset.file:
            # Reset file pointer to beginning
            dataset.file.seek(0)
            file_content = dataset.file.read()
            
            # Determine file type and read accordingly
            if dataset.dataset_type == 'csv':
                df = pd.read_csv(io.BytesIO(file_content))
            elif dataset.dataset_type == 'excel':
                df = pd.read_excel(io.BytesIO(file_content))
            else:
                # Try CSV as fallback
                df = pd.read_csv(io.BytesIO(file_content))
            
            if not df.empty:
                # Get columns
                columns = df.columns.tolist()
                
                # Get preview data (first 10 rows)
                preview_rows = df.head(10)
                preview_data = preview_rows.to_dict('records')
                
                # Generate graph data for numeric columns
                numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
                if numeric_columns and len(df) > 1:
                    # Create a simple line chart with first numeric column
                    first_numeric = numeric_columns[0]
                    chart_data = df[first_numeric].fillna(0).head(20).tolist()
                    labels = [f"Row {i+1}" for i in range(len(chart_data))]
                    
                    graph_data = {
                        'chart_type': 'line',
                        'labels': json.dumps(labels),
                        'datasets': json.dumps([{
                            'label': first_numeric,
                            'data': chart_data,
                            'borderColor': 'rgb(75, 192, 192)',
                            'backgroundColor': 'rgba(75, 192, 192, 0.2)',
                            'tension': 0.1
                        }])
                    }
    
    except Exception as e:
        error_message = f"Error reading dataset file: {str(e)}"
        print(f"Error reading dataset file: {e}")
        # Handle file reading errors gracefully
        preview_data = []
        columns = []
        graph_data = None
    
    # Get comments (top 5 by upvotes)
    comments = Comment.objects.filter(
        dataset=dataset
    ).select_related('author').order_by('-upvotes', '-created_at')[:5]
    
    # Get related datasets (same topics or author)
    related_datasets = Dataset.objects.filter(
        Q(topics__icontains=dataset.topics) | Q(author=dataset.author)
    ).exclude(id=dataset.id).distinct()[:5]
    
    context = {
        'dataset': dataset,
        'author_name': dataset.author.get_full_name() or dataset.author.username,
        'topics': dataset.get_topics_list(),
        'preview_data': preview_data,
        'columns': columns,
        'graph_data': graph_data,
        'comments': comments,
        'related_datasets': related_datasets,
        'error_message': error_message,
    }
    
    return render(request, 'dataset/dataset_detail.html', context)


def dataset_preview(request, dataset_id):
    """View to display full dataset preview with pagination"""
    dataset = get_object_or_404(Dataset, id=dataset_id)
    
    try:
        if dataset.file:
            # Reset file pointer to beginning
            dataset.file.seek(0)
            file_content = dataset.file.read()
            
            if dataset.dataset_type == 'csv':
                df = pd.read_csv(io.BytesIO(file_content))
            elif dataset.dataset_type == 'excel':
                df = pd.read_excel(io.BytesIO(file_content))
            else:
                df = pd.read_csv(io.BytesIO(file_content))
            
            columns = df.columns.tolist()
            
            # Paginate the data
            page_number = request.GET.get('page', 1)
            rows_per_page = 50
            
            total_rows = len(df)
            start_idx = (int(page_number) - 1) * rows_per_page
            end_idx = start_idx + rows_per_page
            
            preview_data = df.iloc[start_idx:end_idx].to_dict('records')
            
            # Calculate pagination info
            has_previous = start_idx > 0
            has_next = end_idx < total_rows
            
            context = {
                'dataset': dataset,
                'columns': columns,
                'preview_data': preview_data,
                'current_page': int(page_number),
                'has_previous': has_previous,
                'has_next': has_next,
                'total_rows': total_rows,
                'start_row': start_idx + 1,
                'end_row': min(end_idx, total_rows),
                'author_name': dataset.author.get_full_name() or dataset.author.username,
            }
            
            return render(request, 'dataset/dataset_preview.html', context)
            
    except Exception as e:
        print(f"Error reading dataset file: {e}")
        context = {
            'dataset': dataset,
            'error_message': 'Unable to load dataset preview',
            'author_name': dataset.author.get_full_name() or dataset.author.username,
        }
        return render(request, 'dataset/dataset_preview.html', context)


def dataset_comments(request, dataset_id):
    """View to display comments with pagination"""
    dataset = get_object_or_404(Dataset, id=dataset_id)
    
    # Get comments ordered by upvotes then by creation date
    comments = Comment.objects.filter(
        dataset=dataset
    ).select_related('author').order_by('-upvotes', '-created_at')
    
    # Paginate comments
    paginator = Paginator(comments, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'dataset': dataset,
        'comments': page_obj,
        'author_name': dataset.author.get_full_name() or dataset.author.username,
    }
    
    return render(request, 'dataset/dataset_comments.html', context)


@login_required
@require_POST
def post_comment(request, dataset_id):
    """View to allow authenticated user to post a comment"""
    dataset = get_object_or_404(Dataset, id=dataset_id)
    
    content = request.POST.get('content', '').strip()
    
    if not content:
        messages.error(request, 'Comment content cannot be empty.')
        return redirect('dataset_detail', dataset_id=dataset_id)
    
    # Create new comment
    comment = Comment.objects.create(
        dataset=dataset,
        author=request.user,
        content=content
    )
    
    messages.success(request, 'Comment posted successfully!')
    return redirect('dataset_detail', dataset_id=dataset_id)


@login_required
@require_POST
def upvote_comment(request, comment_id):
    """View to upvote a comment"""
    comment = get_object_or_404(Comment, id=comment_id)
    
    # Increment upvote count
    comment.upvotes += 1
    comment.save(update_fields=['upvotes'])
    
    if request.headers.get('Content-Type') == 'application/json':
        return JsonResponse({'upvotes': comment.upvotes})
    
    return redirect('dataset_detail', dataset_id=comment.dataset.id)


def download_dataset(request, dataset_id):
    """Handle dataset download"""
    dataset = get_object_or_404(Dataset, id=dataset_id)
    
    # Increment download count
    dataset.downloads += 1
    dataset.save(update_fields=['downloads'])
    
    # Return file response
    if dataset.file:
        # Reset file pointer to beginning
        dataset.file.seek(0)
        response = HttpResponse(
            dataset.file.read(), 
            content_type='application/octet-stream'
        )
        response['Content-Disposition'] = f'attachment; filename="{dataset.file.name}"'
        return response
    
    messages.error(request, 'Dataset file not found.')
    return redirect('dataset_detail', dataset_id=dataset_id)


@login_required
def upload_dataset(request):
    """Handle dataset upload via regular form submission and AJAX"""
    if request.method == 'POST':
        form = DatasetUploadForm(request.POST, request.FILES)
        if form.is_valid():
            dataset = form.save(commit=False)
            dataset.author = request.user
            dataset.save()
            
            # Check if it's an AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Dataset uploaded successfully!',
                    'dataset_id': dataset.pk,
                    'redirect_url': reverse('dataset_detail', kwargs={'dataset_id': dataset.pk})
                })
            else:
                # Regular form submission - redirect as usual
                messages.success(request, 'Dataset uploaded successfully!')
                return redirect('dataset_detail', dataset_id=dataset.pk)
        else:
            # Form has errors
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'errors': form.errors,
                    'message': 'Please correct the errors below.'
                }, status=400)
            else:
                # Regular form submission with errors
                messages.error(request, 'Please correct the errors below.')
    else:
        form = DatasetUploadForm()
   
    return render(request, 'dataset/upload.html', {'form': form})



@login_required
def home(request):
    """Render authenticated user's home page - Dynamic home page view with real data"""
    
    # Get total statistics
    total_datasets = Dataset.objects.count()
    total_downloads = Dataset.objects.aggregate(Sum('downloads'))['downloads__sum'] or 0
    total_views = Dataset.objects.aggregate(Sum('views'))['views__sum'] or 0
    
    # Get trending datasets (most downloaded in the last week)
    trending_datasets = Dataset.objects.select_related('author').annotate(
        recent_growth=Count('id')
    ).order_by('-downloads', '-views')[:3]
    
    # Get top categories with counts
    all_datasets = Dataset.objects.all()
    category_counts = {}
    
    for dataset in all_datasets:
        topics = dataset.get_topics_list()
        for topic in topics:
            topic_lower = topic.lower().strip()
            if topic_lower in category_counts:
                category_counts[topic_lower] += 1
            else:
                category_counts[topic_lower] = 1
    
    # Sort categories by count and get top 4
    top_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:4]
    
    # Get popular search terms (based on topics)
    popular_terms = []
    if top_categories:
        popular_terms = [category[0].title() for category in top_categories[:6]]
    
    # Get featured datasets (highest rated or most downloaded)
    featured_datasets = Dataset.objects.select_related('author').order_by('-rating', '-downloads')[:3]
    
    # Get file format counts
    format_counts = {
        'csv': Dataset.objects.filter(dataset_type='csv').count(),
        'excel': Dataset.objects.filter(dataset_type='excel').count(),
    }
    
    context = {
        'total_datasets': total_datasets,
        'total_downloads': total_downloads,
        'total_views': total_views,
        'total_countries': 54,  # Static for now
        'total_researchers': total_views // 50,  # Rough estimate
        'trending_datasets': trending_datasets,
        'top_categories': top_categories,
        'popular_terms': popular_terms,
        'featured_datasets': featured_datasets,
        'format_counts': format_counts,
    }

    return render(request, 'accounts/home.html', context)


def dataset_list(request):
    """View to return dataset title, author name, downloads, views with search and filtering"""
    datasets = Dataset.objects.select_related('author').all()
    
    # Handle search
    search_query = request.GET.get('search', '')
    if search_query:
        datasets = datasets.filter(
            Q(title__icontains=search_query) | 
            Q(bio__icontains=search_query) | 
            Q(topics__icontains=search_query)
        )
    
    # Handle category filter
    category = request.GET.get('category', '')
    if category and category != 'all':
        datasets = datasets.filter(topics__icontains=category)
    
    # Handle format filter
    format_filter = request.GET.get('format', '')
    if format_filter:
        datasets = datasets.filter(dataset_type=format_filter)
    
    # Handle sorting
    sort_by = request.GET.get('sort', 'relevance')
    if sort_by == 'downloads':
        datasets = datasets.order_by('-downloads')
    elif sort_by == 'recent':
        datasets = datasets.order_by('-created_at')
    elif sort_by == 'rating':
        datasets = datasets.order_by('-rating')
    else:  # relevance (default)
        datasets = datasets.order_by('-views', '-downloads')
    
    # Pagination
    paginator = Paginator(datasets, 12)  # Show 12 datasets per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    dataset_data = []
    for dataset in page_obj:
        dataset_data.append({
            'id': dataset.id,
            'title': dataset.title,
            'author_name': dataset.author.get_full_name() or dataset.author.username,
            'downloads': dataset.downloads,
            'views': dataset.views,
            'rating': dataset.rating,
            'bio': dataset.bio,
            'topics': dataset.get_topics_list(),
            'dataset_type': dataset.get_dataset_type_display(),
            'created_at': dataset.created_at,
        })
    
    context = {
        'datasets': dataset_data,
        'page_obj': page_obj,
        'search_query': search_query,
        'current_category': category,
        'current_format': format_filter,
        'current_sort': sort_by,
    }
    return render(request, 'dataset/dataset_list.html', context)