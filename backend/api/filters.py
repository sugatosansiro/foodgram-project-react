from django_filters import rest_framework
from django_filters.rest_framework import (BooleanFilter, CharFilter,
                                           FilterSet,
                                           ModelMultipleChoiceFilter)

from recipes.models import Ingredient, Recipe, Tag
# from django.contrib.auth.models import AnonymousUser

# ГПТКОД
# class RecipeFilter(rest_framework.FilterSet):
#     tags = ModelMultipleChoiceFilter(
#         field_name='tags__slug',
#         to_field_name='slug',
#         queryset=Tag.objects.all(),
#     )
#     is_favorited = BooleanFilter()
#     is_in_shopping_cart = BooleanFilter()

#     class Meta:
#         model = Recipe
#         fields = ('author', 'tags', 'is_in_shopping_cart', 'is_favorited')

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         request = self.request
#         if isinstance(request.user, AnonymousUser):
#             self.Meta.fields = ('tags',)


class RecipeFilter(rest_framework.FilterSet):
    tags = ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
    )
    is_favorited = BooleanFilter()
    is_in_shopping_cart = BooleanFilter()

    class Meta:
        model = Recipe
        fields = ('author', 'tags', 'is_in_shopping_cart', 'is_favorited')


class IngredientFilter(FilterSet):
    name = CharFilter(field_name='name', lookup_expr='contains')

    class Meta:
        model = Ingredient
        fields = ('name',)
