from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class DefaultPageNumberPagination(PageNumberPagination):
    page_size = 20
    max_page_size = 10000
    page_query_param = "page"
    page_size_query_param = "per_page"

    def get_paginated_response(self, data: list) -> Response:
        return Response(
            data={
                "items": data,
                "pagination": {
                    "page": self.page.number,
                    "per_page": self.page.paginator.per_page,
                    "current_entries_size": len(data),
                    "total_entries_size": self.page.paginator.count,
                    "total_pages": self.page.paginator.num_pages,
                },
            }
        )
