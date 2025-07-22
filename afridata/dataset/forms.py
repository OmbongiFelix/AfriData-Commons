# forms.py
from django import forms
from .models import Dataset

class DatasetUploadForm(forms.ModelForm):
    DATASET_TYPE_CHOICES = [
        ('', 'Select dataset type'),
        ('csv', 'CSV'),
        ('excel', 'Excel'),
        ('pdf', 'PDF'),
        ('txt', 'Text'),
        ('json', 'JSON'),
        ('xml', 'XML'),
        ('zip', 'ZIP Archive'),
        ('yaml', 'YAML'),
        ('parquet', 'Parquet'),
    ]
    
    class Meta:
        model = Dataset
        fields = ['title', 'file', 'dataset_type', 'bio', 'topics']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Enter a descriptive title for your dataset',
                'maxlength': '255'
            }),
            'file': forms.FileInput(attrs={
                'accept': '.csv,.xlsx,.xls,.pdf,.txt,.json,.xml,.zip,.yaml,.yml,.parquet',
                'style': 'display: none;'  # Hidden as we use custom upload area
            }),
            'dataset_type': forms.Select(
                choices=DATASET_TYPE_CHOICES,
                attrs={
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
                }
            ),
            'bio': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-vertical',
                'rows': 4,
                'placeholder': 'Describe your dataset, its contents, and potential use cases...'
            }),
            'topics': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'machine learning, data science, statistics, finance',
                'maxlength': '500'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make all fields required
        for field in self.fields:
            self.fields[field].required = True
    
    def clean_title(self):
        title = self.cleaned_data.get('title', '').strip()
        if not title:
            raise forms.ValidationError('This field is required')
        if len(title) < 3:
            raise forms.ValidationError('Title must be at least 3 characters long')
        return title
    
    def clean_bio(self):
        bio = self.cleaned_data.get('bio', '').strip()
        if not bio:
            raise forms.ValidationError('This field is required')
        if len(bio) < 10:
            raise forms.ValidationError('Description must be at least 10 characters long')
        return bio
    
    def clean_topics(self):
        topics = self.cleaned_data.get('topics', '').strip()
        if not topics:
            raise forms.ValidationError('This field is required')
        
        # Split topics by comma and validate
        topic_list = [topic.strip() for topic in topics.split(',') if topic.strip()]
        if len(topic_list) < 1:
            raise forms.ValidationError('Please enter at least one topic')
        if len(topic_list) > 10:
            raise forms.ValidationError('Maximum 10 topics allowed')
        
        # Rejoin cleaned topics
        return ', '.join(topic_list)
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if not file:
            raise forms.ValidationError('Please select a file to upload')
            
        # Check file size (limit to 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if file.size > max_size:
            raise forms.ValidationError('File size cannot exceed 10MB')
        
        # Check file extension
        allowed_extensions = ['.csv', '.xlsx', '.xls', '.pdf', '.txt', '.json', '.xml', '.zip', '.yaml', '.yml', '.parquet']
        file_extension = '.' + file.name.lower().split('.')[-1]
        if file_extension not in allowed_extensions:
            raise forms.ValidationError(
                f'Only these file types are allowed: {", ".join(allowed_extensions)}'
            )
        
        return file
    
    def clean_dataset_type(self):
        dataset_type = self.cleaned_data.get('dataset_type')
        if not dataset_type:
            raise forms.ValidationError('Please select a dataset type')
        return dataset_type
    
    def clean(self):
        cleaned_data = super().clean()
        file = cleaned_data.get('file')
        dataset_type = cleaned_data.get('dataset_type')
        
        # Validate that file type matches selected dataset type
        if file and dataset_type:
            file_extension = '.' + file.name.lower().split('.')[-1]
            type_extension_map = {
                'csv': ['.csv'],
                'excel': ['.xlsx', '.xls'],
                'pdf': ['.pdf'],
                'txt': ['.txt'],
                'json': ['.json'],
                'xml': ['.xml'],
                'zip': ['.zip'],
                'yaml': ['.yaml', '.yml'],
                'parquet': ['.parquet']
            }
            
            expected_extensions = type_extension_map.get(dataset_type, [])
            if file_extension not in expected_extensions:
                raise forms.ValidationError(
                    f'Selected file type does not match the dataset type. '
                    f'Expected: {", ".join(expected_extensions)}, got: {file_extension}'
                )
        
        return cleaned_data