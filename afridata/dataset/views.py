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
    return render(request, 'datasets/dataset_list.html', context)

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



def render_dataset(request):
    """
    Basic view that renders a template
    
    context = {
        'title': 'My Page',
        'message': 'Hello from Django!',
        'user': request.user if request.user.is_authenticated else None,
    }"""
    
    return render(request, 'dataset/dataset_page.html') 

