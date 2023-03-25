from django.contrib import admin

from recipes.models import (Favorite, Follow, Ingredient, Recipe,
                            RecipeIngredients, ShoppingCart, Tag)
from users.models import User


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


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredients
    min_num = 1
    extra = 0


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit', )
    search_fields = ('id', 'name', 'measurement_unit', )
    list_filter = ('name', 'measurement_unit', )
    empty_value_display = '-пусто-'


class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'color', 'slug', )
    search_fields = ('id', 'name', 'color', 'slug', )
    list_filter = ('name', 'color', 'slug', )
    empty_value_display = '-пусто-'


class RecipeAdmin(admin.ModelAdmin):

    def added_to_favorites_amount(self, obj):
        return Favorite.objects, filter(recipe=obj).count()

    added_to_favorites_amount.short_description = (
        'Количество добавлений в избранное'
    )

    list_display = ('id', 'name', 'author', 'cooking_time', )
    search_fields = ('id', 'name', 'author', 'tags', 'cooking_time', )
    list_filter = ('name', 'author', 'tags', )
    empty_value_display = '-пусто-'
    inlines = (RecipeIngredientInline,)
    empty_value_display = '-пусто-'


class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'ingredient', 'amount', )
    search_fields = ('id', 'recipe', 'ingredient', 'amount', )
    list_filter = ('recipe', 'ingredient', 'amount', )
    empty_value_display = '-пусто-'


class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe', )
    search_fields = ('id', 'user', 'recipe', )
    list_filter = ('user', 'recipe', )
    empty_value_display = '-пусто-'


class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe', )
    search_fields = ('id', 'user', 'recipe', )
    list_filter = ('user', 'recipe', )
    empty_value_display = '-пусто-'


class FollowAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'author', )
    search_fields = ('id', 'user', 'author', )
    list_filter = ('user', 'author', )
    empty_value_display = '-пусто-'


admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(RecipeIngredients, RecipeIngredientAdmin)
admin.site.register(Favorite, FavoriteAdmin)
admin.site.register(ShoppingCart, ShoppingCartAdmin)
admin.site.register(Follow, FollowAdmin)
admin.site.register(User, UserAdmin)
