from django.shortcuts import render
from django.http import HttpResponse

def render_login_page(request):
    """
    Basic view that renders a template
    
    context = {
        'title': 'My Page',
        'message': 'Hello from Django!',
        'user': request.user if request.user.is_authenticated else None,
    }"""
    
    return render(request, 'login/login.html') 