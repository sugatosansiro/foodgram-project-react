from django.urls import include, path
from rest_framework import routers
from .views import (IngredientViewSet, RecipeViewSet, FollowViewSet,
                    TagViewSet, CustomUserViewSet)

app_name = 'api'

router = routers.DefaultRouter()
router.register(r'ingredients', IngredientViewSet, basename='ingredients')
router.register(r'recipes', RecipeViewSet, basename='recipes')
router.register(r'tags', TagViewSet, basename='tags')
router.register(r'users', CustomUserViewSet, basename='users')
router.register(
    r'users/(?P<user_id>\d+)/subscribe',
    FollowViewSet,
    basename='follows'
)

urlpatterns = [
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
