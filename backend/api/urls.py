from api.views import (CartViewset, CustomUserViewSet, FavoriteViewSet,
                       IngredientViewSet, RecipeViewSet, SubscriptionViewSet,
                       TagViewSet)
from django.urls import include, path
from rest_framework import routers

app_name = 'api'

router = routers.DefaultRouter()
router.register(r'ingredients', IngredientViewSet, basename='ingredients')
router.register(r'favorites', FavoriteViewSet, basename='favorites')
router.register(r'recipes', RecipeViewSet, basename='recipes')
router.register(r'tags', TagViewSet, basename='tags')
router.register(r'users', CustomUserViewSet, basename='users')
router.register(
    r'subscriptions',
    SubscriptionViewSet,
    basename='subscriptions'
)
router.register(r'cart', CartViewset, basename='shopping_cart')

urlpatterns = [
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
