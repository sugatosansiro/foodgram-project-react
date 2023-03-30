from django.contrib import admin

from recipes.models import (Cart, Favorite, Ingredient, Recipe,
                            RecipeIngredients, Subscription, Tag)
from users.models import User


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredients
    min_num = 1
    extra = 0


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'username',
        'email',
        'first_name',
        'last_name',
        'role',
    )
    search_fields = ('id', 'username', 'email', 'first_name', 'last_name', )
    list_filter = ('username', 'email',)
    empty_value_display = '-пусто-'


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit', )
    search_fields = ('id', 'name', 'measurement_unit', )
    list_filter = ('name', 'measurement_unit', )
    empty_value_display = '-пусто-'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'color', 'slug', )
    search_fields = ('id', 'name', 'color', 'slug', )
    list_filter = ('name', 'color', 'slug', )
    empty_value_display = '-пусто-'


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):

    def added_to_favorites_amount(self, obj):
        return Subscription.objects.filter(recipe=obj).count()

    added_to_favorites_amount.short_description = (
        'Количество добавлений в избранное'
    )

    list_display = ('id', 'name', 'author', 'cooking_time', )
    search_fields = ('id', 'name', 'author', 'tags', 'cooking_time', )
    list_filter = ('name', 'author', 'tags', )
    empty_value_display = '-пусто-'
    inlines = (RecipeIngredientInline,)
    empty_value_display = '-пусто-'


@admin.register(RecipeIngredients)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'ingredient', 'amount', )
    search_fields = ('id', 'recipe', 'ingredient', 'amount', )
    list_filter = ('recipe', 'ingredient', 'amount', )
    empty_value_display = '-пусто-'


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe', )
    search_fields = ('id', 'user', 'recipe', )
    list_filter = ('user', 'recipe', )
    empty_value_display = '-пусто-'


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe', )
    search_fields = ('id', 'user', 'recipe', )
    list_filter = ('user', 'recipe', )
    empty_value_display = '-пусто-'


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'author', )
    search_fields = ('id', 'user', 'author', )
    list_filter = ('user', 'author', )
    empty_value_display = '-пусто-'
