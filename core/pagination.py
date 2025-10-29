# core/pagination.py
from rest_framework.pagination import PageNumberPagination

class StandardResultsSetPagination(PageNumberPagination):
    page_query_param = "page"           # ?page=1
    page_size_query_param = "page_size" # ?page_size=50
    page_size = 25                      # tamaño por defecto
    max_page_size = 200                 # límite superior
