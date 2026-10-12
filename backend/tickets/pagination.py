from rest_framework.pagination import PageNumberPagination


class TicketPagination(PageNumberPagination):
    """?page=<n>&limit=<n>, default 10 per page, capped at 100."""

    page_size = 10
    page_size_query_param = "limit"
    max_page_size = 100
