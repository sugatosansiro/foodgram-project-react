from api.filters import IngredientFilter, RecipeFilter
from api.generate_pdf import generate_pdf_shopping_cart
from api.mixins import CreateAndDeleteRelatedMixin, ListCreateDestroyViewSet
from api.permissions import AdminOnly, IsAdminUserOrReadOnly, OwnerOrReadOnly
from api.serializers import (CartSerializer, CustomUserCreateSerializer,
                             CustomUserSerializer, FavoriteSerializer,
                             IngredientSerializer,
                             RecipeCreateUpdateSerializer,
                             RecipeListSerializer, RecipeMinifiedSerializer,
                             SubscriptionSerializer, TagSerializer,
                             UserExtendedSerializer)
# RecipeSerializer,
from django.shortcuts import get_object_or_404
from django_filters import rest_framework as filters
from recipes.models import (Cart, Favorite, Ingredient, Recipe, Subscription,
                            Tag)
from recipes.pagination import RecipePagination
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import BasePagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from users.models import User


class UserViewSet(viewsets.ModelViewSet):
    """Вьюсет для пользователей."""
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = (IsAuthenticated, AdminOnly,)
    lookup_field = 'username'

    @action(
        methods=['GET', 'PATCH'],
        detail=False,
        permission_classes=(IsAuthenticated,),
        url_path='me')
    def get_current_user_info(self, request):
        """Функция для информации о пользователе"""
        serializer = CustomUserSerializer(request.user)
        if request.method == 'PATCH':
            serializer = CustomUserCreateSerializer(
                request.user,
                data=request.data,
                partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.data)


class CustomUserViewSet(UserViewSet, CreateAndDeleteRelatedMixin):
    """Cпециальный вьюсет для пользователей"""
    http_method_name = ['get', 'post', 'delete']

    def get_permissions(self):
        if self.action in ('subscribe', 'subscriptions'):
            return [IsAuthenticated()]
        return super().get_permissions()

    def destroy(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def get_serializer_class(self):
        if self.action in ('subscribe', 'subscriptions'):
            return UserExtendedSerializer
        return super().get_serializer_class()

    @action(methods=['post', 'delete'], detail=True)
    def subscribe(self, request, pk=None):
        return self.create_and_delete_related(
            pk=pk,
            klass=Subscription,
            create_failed_message='Не удалось совершить подписку',
            delete_failed_message='Такой подписки не существует',
            field_to_create_or_delete_name='author'
        )

    @action(methods=['get'], detail=False)
    def subscriptions(self, request):
        queryset = User.objects.filter(
            following__user=self.request.user
        ).all()
        context = self.get_serializer_context()
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer_class()(
            page,
            context=context,
            many=True
        )
        return self.get_paginated_response(serializer.data)


class RecipeViewSet(viewsets.ModelViewSet, CreateAndDeleteRelatedMixin):
    """Вьюсет для рецептов"""
    queryset = Recipe.objects.all()
    http_method_name = ['get', 'post', 'patch', 'delete']   # 'retrieve'
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = RecipeFilter
    pagination_class = RecipePagination
    permission_classes = (OwnerOrReadOnly,)

    def get_permissions(self):
        if self.action in (
            'shopping_cart',
            'favorite',
            'download_shopping_cart'
        ):
            return [IsAuthenticated()]
        if self.action == 'delete':
            return [OwnerOrReadOnly()]
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def destroy(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return RecipeCreateUpdateSerializer
        if self.action in ('shopping_cart', 'favorite'):
            return RecipeMinifiedSerializer
        # if self.action in ('retrieve'):
        #     return RecipeSerializer
        return RecipeListSerializer

    @action(methods=['post', 'delete'], detail=True)
    def shopping_cart(self, request, pk=None):
        return self.create_and_delete_related(
            pk=pk,
            klass=Cart,
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

    @action(methods=['post', 'delete'], detail=True)
    def favorite(self, request, pk=None):
        return self.create_and_delete_related(
            pk=pk,
            klass=Favorite,
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


class SubscriptionViewSet(UserViewSet):
    """Возвращает все подписки пользователя, сделавшего запрос.
    Анонимные запросы запрещены."""
    queryset = User.objects.all()
    serializer_class = UserExtendedSerializer
    pagination_class = BasePagination

    @action(detail=False)
    def subscriptions(self, request):
        follows = request.user.follower.all()
        pages = self.paginate_queryset(follows)
        serializer = SubscriptionSerializer(pages, many=True)
        return self.get_paginated_response(serializer.data)

    @action(methods=['post', 'delete'], detail=True)
    def subscribe(self, request, **kwargs):
        author = get_object_or_404(User, id=self.kwargs.get('id'))
        if request.method == 'POST':
            serializer = SubscriptionSerializer(author, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        follow = get_object_or_404(
            Subscription,
            user=self.request.user,
            author=author)
        follow.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


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
