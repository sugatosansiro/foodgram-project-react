from rest_framework.pagination import PageNumberPagination


class RecipePagination(PageNumberPagination):
    """Класс для пагинации рецептов"""
    page_size = 6
