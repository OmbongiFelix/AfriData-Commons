'''
This file contains serializer classes that convert Django model instances to JSON format for API responses and handle validation when converting JSON data back to Django models. It acts as the bridge between your Django models and the JSON data that APIs send and receive.
'''
#api/serializers.py
from rest_framework import serializers
from datasets.models import Dataset
from accounts.models import User

class DatasetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dataset
        fields = '__all__'
        
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

