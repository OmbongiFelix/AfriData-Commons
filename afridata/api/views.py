from django.shortcuts import render
from django.http import HttpResponse

def api_request(request):
    """
    Basic view that renders a template
    
    context = {
        'title': 'My Page',
        'message': 'Hello from Django!',
        'user': request.user if request.user.is_authenticated else None,
    }"""

    return HttpResponse("This is the api page.")