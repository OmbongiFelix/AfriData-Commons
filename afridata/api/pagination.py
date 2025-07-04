'''
This file defines how large datasets are split into smaller, manageable chunks (pages) when returned by the API, preventing performance issues and timeouts. It controls how many items are returned per page and provides navigation links to move between pages of results.
'''

# api/pagination.py
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from collections import OrderedDict

class StandardResultsSetPagination(PageNumberPagination):
    """Standard pagination for API results"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('total_pages', self.page.paginator.num_pages),
            ('current_page', self.page.number),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data)
        ]))

class LargeResultsSetPagination(PageNumberPagination):
    """Pagination for large datasets"""
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200
    
    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('total_pages', self.page.paginator.num_pages),
            ('current_page', self.page.number),
            ('page_size', self.page_size),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data)
        ]))

class SmallResultsSetPagination(PageNumberPagination):
    """Pagination for small result sets"""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50
    
    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('total_pages', self.page.paginator.num_pages),
            ('current_page', self.page.number),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data)
        ]))

class APIKeyPagination(SmallResultsSetPagination):
    """Pagination for API keys"""
    page_size = 10
    max_page_size = 25

class UsagePagination(StandardResultsSetPagination):
    """Pagination for usage statistics"""
    page_size = 50
    max_page_size = 500