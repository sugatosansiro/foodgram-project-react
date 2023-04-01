from django.shortcuts import get_object_or_404
from django_filters import rest_framework as filters
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from djoser.permissions import CurrentUserOrAdminOrReadOnly

from api.filters import IngredientFilter, RecipeFilter
from api.generate_pdf import generate_pdf_shopping_cart
from api.mixins import CreateAndDeleteRelatedMixin, ListCreateDestroyViewSet
from api.permissions import IsAdminUserOrReadOnly
from api.serializers import (CartSerializer, CustomUserCreateSerializer,
                             FavoriteSerializer,
                             IngredientSerializer, RecipeSerializer,
                             RecipeCreateUpdateSerializer,
                             RecipeListSerializer, RecipeMinifiedSerializer,
                             SubscriptionGetSerializer, TagSerializer)

from recipes.models import (Cart, Ingredient, Favorite, Recipe,
                            Subscription, Tag)
from recipes.pagination import RecipePagination
from users.models import User


class CustomUserViewSet(UserViewSet, CreateAndDeleteRelatedMixin):
    """Cпециальный вьюсет для пользователей"""
    http_method_name = ['GET', 'POST', 'DELETE']
    lookup_field = 'pk'

    def get_permissions(self):
        if self.action in ('subscribe', 'subscriptions'):
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()

    def destroy(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def get_serializer_class(self):
        if self.action in ('subscribe', 'subscriptions'):
            return CustomUserCreateSerializer
        return super().get_serializer_class()

    @action(
        methods=['POST', 'DELETE'], detail=True
    )
    def subscribe(self, request, pk=None):
        return self.create_and_delete_related(
            pk=pk,
            model=Subscription,
            create_failed_message='Не удалось совершить подписку',
            delete_failed_message='Такой подписки не существует',
            field_to_create_or_delete_name='author'
        )

    @action(methods=['GET'], detail=False)
    def subscriptions(self, request):
        queryset = User.objects.filter(
            following__user=self.request.user
        ).all()
        page = self.paginate_queryset(queryset)
        serializer = SubscriptionGetSerializer(
            page,
            context={'request': request},
            many=True
        )
        return self.get_paginated_response(serializer.data)


class RecipeViewSet(viewsets.ModelViewSet, CreateAndDeleteRelatedMixin):
    """Вьюсет для рецептов"""
    http_method_name = ['GET', 'POST', 'PATCH', 'DELETE']
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = RecipeFilter
    pagination_class = RecipePagination
    permission_classes = (CurrentUserOrAdminOrReadOnly,)

    def get_serializer_class(self):
        if self.request.method in ('POST', 'PATCH'):
            return RecipeCreateUpdateSerializer
        if self.action in ('shopping_cart', 'favorite'):
            return RecipeMinifiedSerializer
        if self.request.user.is_anonymous:
            return RecipeSerializer
        return RecipeListSerializer

    def get_queryset(self):
        if self.request.user.is_anonymous:
            return (
                Recipe.objects
                .select_related('author')
                .prefetch_related('tags', 'ingredients')
            )
        return (
            Recipe.objects
            .add_user_annotations(user_id=self.request.user.pk)
            .select_related('author')
            .prefetch_related('tags', 'ingredients')
        )

    def get_permissions(self):
        # if self.action == 'GET':
        #     return [AllowAny()]
        if self.action in (
                'POST',
                'shopping_cart',
                'favorite',
                'download_shopping_cart'
        ):
            return [IsAuthenticated()]
        if self.action in (
                'DELETE',
                'PATCH'
        ):
            return [CurrentUserOrAdminOrReadOnly()]
        # return super().get_permissions()
        return [AllowAny()]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(methods=['POST', 'DELETE'], detail=True)
    def shopping_cart(self, request, pk=None):
        return self.create_and_delete_related(
            pk=pk,
            model=Cart,
            create_failed_message=(
                'Не удалось добавить рецепт в список покупок'
            ),
            delete_failed_message='Рецепт отсутствует в списке покупок',
            field_to_create_or_delete_name='recipe'
        )

    @action(detail=False, methods=['GET'])
    def download_shopping_cart(self, request):
        """Вызов выгрузки PDF-файла со списком покупок"""
        return generate_pdf_shopping_cart(request)

    @action(methods=['POST', 'DELETE'], detail=True)
    def favorite(self, request, pk=None):
        return self.create_and_delete_related(
            pk=pk,
            model=Favorite,
            create_failed_message='Не удалось добавить рецепт в избранное',
            delete_failed_message='Рецепт отсутствует в избранном',
            field_to_create_or_delete_name='recipe'
        )


class TagViewSet(ListCreateDestroyViewSet):
    """Вьюсет для тэгов."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (IsAdminUserOrReadOnly,)
    pagination_class = None

    def perform_create(self, serializer):
        serializer.save(
            name=self.request.data['name'], slug=self.request.data['slug']
        )

    def perform_destroy(self, serializer):
        serializer = get_object_or_404(Tag, slug=self.kwargs.get('slug'))
        serializer.delete()


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Получение доступных тэгов."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = IngredientFilter
    pagination_class = None


class FavoriteViewSet(RecipeViewSet):
    """Возвращает все избранные рецепты пользователя, сделавшего запрос"""
    serializer_class = FavoriteSerializer

    def get_queryset(self):
        return Recipe.objects.filter(
            is_favorited=True,
            recipe__favorite__user=self.request.user
        ).all()


class CartViewset(RecipeViewSet):
    """Возвращает список покупок пользователя"""
    serializer_class = CartSerializer

    def get_queryset(self):
        return Recipe.objects.filter(
            is_in_shopping_cart=True,
            recipe__shopping_cart__user=self.request.user
        ).all()
