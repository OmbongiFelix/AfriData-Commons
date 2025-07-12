# forms.py
from django import forms
from .models import Dataset

class DatasetUploadForm(forms.ModelForm):
    class Meta:
        model = Dataset
        fields = ['title', 'file', 'dataset_type', 'bio', 'topics']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Enter dataset title'
            }),
            'file': forms.FileInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'accept': '.csv,.xlsx,.xls'
            }),
            'dataset_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 4,
                'placeholder': 'Describe your dataset...'
            }),
            'topics': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'machine learning, data science, statistics'
            }),
        }
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Check file size (limit to 10MB)
            if file.size > 10 * 1024 * 1024:
                raise forms.ValidationError('File size cannot exceed 10MB')
            
            # Check file extension
            allowed_extensions = ['.csv', '.xlsx', '.xls', '.pdf', '.txt', '.json', '.xml', '.zip', '.yaml', '.yml', '.parquet']
            file_extension = file.name.lower().split('.')[-1]
            if f'.{file_extension}' not in allowed_extensions:
                raise forms.ValidationError('Only CSV, Excel, PDF, TXT, JSON, XML, ZIP, YAML, and Parquet files are allowed')

        return file

