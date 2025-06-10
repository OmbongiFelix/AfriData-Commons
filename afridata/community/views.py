from django.shortcuts import render
from django.http import HttpResponse

def community(request):
    """
    Basic view that renders a template
    
    context = {
        'title': 'My Page',
        'message': 'Hello from Django!',
        'user': request.user if request.user.is_authenticated else None,
    }"""
    
    return HttpResponse("This is the community page. You can add your content here.")