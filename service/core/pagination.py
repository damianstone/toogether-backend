from rest_framework.pagination import PageNumberPagination, CursorPagination
from rest_framework.response import Response


class CustomNumberPagination(PageNumberPagination):
    page_size =  50
    max_page_size = 50
    
    def get_paginated_response(self, data):
        return Response({
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'count': self.page.paginator.count,
            "page_count": len(data),
            'results': data
        })


class ChatPagination(PageNumberPagination):
    page_size =  50
    max_page_size = 50
    
    def get_paginated_response(self, data):
        return Response({
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'count': self.page.paginator.count,
            "page_count": len(data),
            'results': data
        })    


class MatchPagination(PageNumberPagination):
    page_size =  20
    max_page_size = 20
    
    def get_paginated_response(self, data):
        return Response({
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'count': self.page.paginator.count,
            "page_count": len(data),
            'results': data
        })    


class CustomCursorPagination(CursorPagination):
    page_size = 2
    cursor_query_param = 'c'


