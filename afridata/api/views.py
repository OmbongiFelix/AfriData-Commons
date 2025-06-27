#api/views.py
#Handle the API logic
from django.shortcuts import render
from django.http import HttpResponse

from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from dataset.models import Dataset
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


