from django.shortcuts import render
from django.http import HttpResponse

def user_profile(request):
    """
    Basic view that renders a template
    
    context = {
        'title': 'My Page',
        'message': 'Hello from Django!',
        'user': request.user if request.user.is_authenticated else None,
    }"""
    
    return render(request, 'user/user_profile.html') 