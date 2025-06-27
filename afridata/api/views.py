#api/views.py
#Handle the API logic
from django.shortcuts import render
from django.http import HttpRespons

from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from datasets.models import Dataset
from .serializers import DatasetSerializer

class DatasetViewSet(viewsets.ModelViewSet):
    queryset = Dataset.objects.all()
    serializer_class = DatasetSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    @action(detail=False, methods=['get'])
    def popular(self, request):
        popular_datasets = Dataset.objects.filter(is_popular=True)
        serializer = self.get_serializer(popular_datasets, many=True)
        return Response(serializer.data)




def api_request(request):
    """
    Basic view that renders a template
    
    context = {
        'title': 'My Page',
        'message': 'Hello from Django!',
        'user': request.user if request.user.is_authenticated else None,
    }"""

    return HttpResponse("This is the api page.")