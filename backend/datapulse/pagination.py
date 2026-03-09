"""Custom pagination class for DataPulse."""

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class DataPulsePagination(PageNumberPagination):
    """
    Pagination class that matches the legacy FastAPI response format.
    FastAPI used { "datasets": [...], "total": N }
    """
    page_size_query_param = "limit"
    max_page_size = 100

    def get_paginated_response(self, data):
        # We try to keep the key dynamic based on the view if possible, 
        # but for datasets it was specifically "datasets".
        # If this is used for other lists, it might need more logic or just stay generic.
        
        # Determine the key from the view name or context
        view = self.request.parser_context.get("view")
        key = "results"
        if hasattr(view, "pagination_key"):
            key = view.pagination_key
        elif "dataset" in self.request.path:
            key = "datasets"

        return Response({
            key: data,
            "total": self.page.paginator.count
        })
