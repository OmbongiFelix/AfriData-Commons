# views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, Http404, JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.core.paginator import Paginator
from .models import Dataset, Comment
import pandas as pd
import io



def dataset_list(request):
    """View to return dataset title, author name, downloads, views"""
    datasets = Dataset.objects.select_related('author').all()
    
    dataset_data = []
    for dataset in datasets:
        dataset_data.append({
            'id': dataset.id,
            'title': dataset.title,
            'author_name': dataset.author.get_full_name() or dataset.author.username,
            'downloads': dataset.downloads,
            'views': dataset.views,
            'rating': dataset.rating,
            'created_at': dataset.created_at,
        })
    
    context = {
        'datasets': dataset_data
    }
    return render(request, 'dataset/dataset_list.html', context)

def dataset_detail(request, dataset_id):
    """View to display dataset details and bio"""
    dataset = get_object_or_404(Dataset, id=dataset_id)
    
    # Increment view count
    dataset.views += 1
    dataset.save(update_fields=['views'])
    
    context = {
        'dataset': dataset,
        'author_name': dataset.author.get_full_name() or dataset.author.username,
        'topics': dataset.get_topics_list(),
    }
    return render(request, 'datasets/dataset_detail.html', context)

def download_dataset(request, dataset_id):
    """View to download dataset file"""
    dataset = get_object_or_404(Dataset, id=dataset_id)
    
    try:
        # Increment download count
        dataset.downloads += 1
        dataset.save(update_fields=['downloads'])
        
        # Serve the file
        response = HttpResponse(dataset.file.read(), content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{dataset.file.name.split("/")[-1]}"'
        return response
    except Exception as e:
        raise Http404("File not found")

def dataset_preview(request, dataset_id):
    """View to display preview of dataset"""
    dataset = get_object_or_404(Dataset, id=dataset_id)
    
    try:
        # Read file content
        file_content = dataset.file.read()
        
        preview_data = []
        error_message = None
        
        if dataset.dataset_type == 'csv':
            try:
                # Read CSV file
                df = pd.read_csv(io.BytesIO(file_content))
                # Get first 10 rows for preview
                preview_data = df.head(10).to_dict('records')
                columns = df.columns.tolist()
            except Exception as e:
                error_message = f"Error reading CSV file: {str(e)}"
                
        elif dataset.dataset_type == 'excel':
            try:
                # Read Excel file
                df = pd.read_excel(io.BytesIO(file_content))
                # Get first 10 rows for preview
                preview_data = df.head(10).to_dict('records')
                columns = df.columns.tolist()
            except Exception as e:
                error_message = f"Error reading Excel file: {str(e)}"
        
        context = {
            'dataset': dataset,
            'preview_data': preview_data,
            'columns': columns if preview_data else [],
            'error_message': error_message,
            'author_name': dataset.author.get_full_name() or dataset.author.username,
        }
        
    except Exception as e:
        context = {
            'dataset': dataset,
            'error_message': f"Could not read file: {str(e)}",
            'author_name': dataset.author.get_full_name() or dataset.author.username,
        }
    
    return render(request, 'datasets/dataset_preview.html', context)

def dataset_comments(request, dataset_id):
    """View to display top 15 comments by upvotes"""
    dataset = get_object_or_404(Dataset, id=dataset_id)
    
    # Get top 15 comments ordered by upvotes then by creation date
    top_comments = Comment.objects.filter(dataset=dataset).select_related('author').order_by('-upvotes', '-created_at')[:15]
    
    comments_data = []
    for comment in top_comments:
        comments_data.append({
            'id': comment.id,
            'content': comment.content,
            'upvotes': comment.upvotes,
            'author_name': comment.author.get_full_name() or comment.author.username,
            'created_at': comment.created_at,
        })
    
    context = {
        'dataset': dataset,
        'comments': comments_data,
        'author_name': dataset.author.get_full_name() or dataset.author.username,
    }
    return render(request, 'datasets/dataset_comments.html', context)

@login_required
@require_POST
def post_comment(request, dataset_id):
    """View to allow authenticated user to post a comment"""
    dataset = get_object_or_404(Dataset, id=dataset_id)
    
    content = request.POST.get('content', '').strip()
    
    if not content:
        messages.error(request, 'Comment content cannot be empty.')
        return redirect('dataset_comments', dataset_id=dataset_id)
    
    # Create new comment
    comment = Comment.objects.create(
        dataset=dataset,
        author=request.user,
        content=content
    )
    
    messages.success(request, 'Comment posted successfully!')
    return redirect('dataset_comments', dataset_id=dataset_id)

@login_required
@require_POST
def upvote_comment(request, comment_id):
    """View to upvote a comment (bonus functionality)"""
    comment = get_object_or_404(Comment, id=comment_id)
    
    # Increment upvote count
    comment.upvotes += 1
    comment.save(update_fields=['upvotes'])
    
    if request.headers.get('Content-Type') == 'application/json':
        return JsonResponse({'upvotes': comment.upvotes})
    
    return redirect('dataset_comments', dataset_id=comment.dataset.id)


def render_dataset(request, dataset_id=None):
    """
    Dynamic view that renders dataset page with full functionality
    """
    dataset = None
    preview_data = []
    columns = []
    comments = []
    related_datasets = []
    graph_data = None
    error_message = None
    
    if dataset_id:
        try:
            dataset = get_object_or_404(Dataset, id=dataset_id)
            
            # Increment view count
            dataset.views += 1
            dataset.save(update_fields=['views'])
            
            # Get preview data (first 5 rows)
            try:
                file_content = dataset.file.read()
                
                if dataset.dataset_type == 'csv':
                    df = pd.read_csv(io.BytesIO(file_content))
                elif dataset.dataset_type == 'excel':
                    df = pd.read_excel(io.BytesIO(file_content))
                
                if not df.empty:
                    preview_data = df.head(5).to_dict('records')
                    columns = df.columns.tolist()
                    
                    # Generate simple graph data for numerical columns
                    numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
                    if numeric_columns and len(df) > 1:
                        # Create a simple line chart with first numeric column
                        first_numeric = numeric_columns[0]
                        if len(df) <= 20:  # Only for small datasets
                            graph_data = {
                                'chart_type': 'line',
                                'labels': [str(i+1) for i in range(len(df))],
                                'datasets': [{
                                    'label': first_numeric,
                                    'data': df[first_numeric].fillna(0).tolist(),
                                    'borderColor': '#3b82f6',
                                    'backgroundColor': 'rgba(59, 130, 246, 0.1)',
                                    'fill': True
                                }]
                            }
                            
            except Exception as e:
                error_message = f"Error reading file: {str(e)}"
            
            # Get recent comments (top 5)
            top_comments = Comment.objects.filter(dataset=dataset).select_related('author').order_by('-upvotes', '-created_at')[:5]
            comments = [{
                'id': comment.id,
                'content': comment.content,
                'upvotes': comment.upvotes,
                'author_name': comment.author.get_full_name() or comment.author.username,
                'created_at': comment.created_at,
            } for comment in top_comments]
            
            # Get related datasets (same topics, different dataset)
            if dataset.topics:
                topics_list = dataset.get_topics_list()
                if topics_list:
                    # Find datasets with similar topics
                    related_datasets = Dataset.objects.exclude(id=dataset.id).filter(
                        topics__icontains=topics_list[0]
                    )[:3]
        
        except Exception as e:
            error_message = f"Dataset not found: {str(e)}"
    
    context = {
        'dataset': dataset,
        'author_name': dataset.author.get_full_name() or dataset.author.username if dataset else None,
        'topics': dataset.get_topics_list() if dataset else [],
        'preview_data': preview_data,
        'columns': columns,
        'comments': comments,
        'related_datasets': related_datasets,
        'graph_data': graph_data,
        'error_message': error_message,
    }
    
    return render(request, 'dataset/dataset_page.html', context)
