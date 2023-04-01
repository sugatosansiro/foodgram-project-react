import base64
import re

from django.core.files.base import ContentFile
from django.db import transaction
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers
from rest_framework import status
from rest_framework.validators import UniqueTogetherValidator

from recipes.models import (Cart, Favorite, Ingredient, Recipe,
                            RecipeIngredients,
                            Subscription, Tag)
from users.models import User

MIN = 1
MAX = 32767


class CustomUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return Subscription.objects.filter(
            user=request.user,
            author=obj
        ).exists()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
        )


class CustomUserCreateSerializer(UserCreateSerializer):
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        """Переопределяем метод validate для проверки заполняемых
        полей модели пользователя на предмет специальных символов."""
        attrs = super().validate(attrs)
        regex = re.compile('[^a-zA-Z0-9]')
        for field, value in attrs.items():
            if regex.search(value) and field not in ['email', 'password']:
                raise serializers.ValidationError(
                    f'Ошибка в поле {field}:'
                    f'введены запрещенные символы'
                )
        return attrs

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password',
            'role',
        )
        read_only_fields = ('role',)


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = '__all__'


class RecipeIngredientGetSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredients
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class RecipeListSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    author = CustomUserSerializer()
    ingredients = RecipeIngredientGetSerializer(
        many=True,
        source='recipe_ingredient'
    )
    is_favorited = serializers.BooleanField()
    is_in_shopping_cart = serializers.BooleanField()
    # is_favorited = serializers.SerializerMethodField()
    # is_in_shopping_cart = serializers.SerializerMethodField()

    # def get_is_favorited(self, obj):
    #     if self.context['request'].user.is_anonymous:
    #         return False
    #     return serializers.BooleanField()

    # def get_is_in_shopping_cart(self, obj):
    #     if self.context['request'].user.is_anonymous:
    #         return False
    #     return serializers.BooleanField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time'
        )


class IngredientCreateInRecipeSerializer(serializers.ModelSerializer):
    recipe = serializers.PrimaryKeyRelatedField(read_only=True)
    id = serializers.PrimaryKeyRelatedField(
        source='ingredient',
        queryset=Ingredient.objects.all()
    )
    amount = serializers.IntegerField(write_only=True, min_value=1)

    class Meta:
        model = RecipeIngredients
        fields = ('recipe', 'id', 'amount',)


class TagsCreateInRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id',)


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientGetSerializer(
        many=True, source='recipe_ingredient'
    )
    tags = TagSerializer(many=True)
    image = Base64ImageField()
    author = CustomUserSerializer(required=False)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time'
        )


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    ingredients = IngredientCreateInRecipeSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all()
    )
    image = Base64ImageField()
    author = CustomUserSerializer(required=False)

    def validate_ingredients(self, data):
        """Валидация ингердиентов в рецепте"""
        ingredients = self.initial_data.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError(
                {'ingredients': 'Добавьте хотя бы один ингредиент'},
                status.HTTP_400_BAD_REQUEST,
            )
        valid_list = []
        for ingredient in ingredients:
            ingr_id = ingredient.get('id')
            if ingr_id in valid_list:
                raise serializers.ValidationError(
                    {'ingredients': 'Ингредиенты не должны повторяться'},
                    status.HTTP_400_BAD_REQUEST,
                )
            valid_list.append(ingredient.get('id'))
            if not MIN <= int(ingredient['amount']) <= MAX:
                raise serializers.ValidationError(
                    {'ingredients':
                        f'Количество ингредиента должно быть не менее {MIN}'
                        f' и меньше {MAX}'},
                    status.HTTP_400_BAD_REQUEST,
                )
        return data

    def bulk_create_ingredients(self, recipe, ingredients):
        create_ingredients = [
            RecipeIngredients(
                recipe=recipe,
                ingredient=ingredient['ingredient'],
                amount=ingredient['amount']
            )
            for ingredient in ingredients
        ]
        return RecipeIngredients.objects.bulk_create(
            create_ingredients
        )

    @transaction.atomic
    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.bulk_create_ingredients(recipe, ingredients)
        return recipe

    def update(self, instance, validated_data):
        instance.ingredients.clear()
        instance.tags.clear()

        ingredients = validated_data.pop('ingredients')
        instance.tags.set(validated_data.pop('tags', instance.tags))

        self.bulk_create_ingredients(instance, ingredients)
        return super().update(instance, validated_data)

    def to_representation(self, obj):
        return RecipeListSerializer(
            obj, context={'request': self.context.get('request')}
        ).data

    class Meta:
        model = Recipe
        exclude = ('pub_date', )


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для избранных рецептов"""

    class Meta:
        model = Favorite
        fields = ('user', 'recipe',)
        validators = [
            UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=('user', 'recipe')
            )
        ]

    def validate(self, data):
        user = data['user']
        recipe = data['recipe']
        if user.favorite.filter(recipe=recipe).exists():
            raise serializers.ValidationError(
                'Рецепт уже добавлен в Избранное'
            )
        return data

    def to_representation(self, instance):
        return RecipeMinifiedSerializer(
            instance.recipe,
            context={'request': self.context.get('request')}
        ).data


class SubscriptionGetSerializer(CustomUserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    update = serializers.ModelSerializer.update

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')
        recipes = obj.recipes.all()[:int(recipes_limit)]
        return RecipeMinifiedSerializer(
            recipes,
            many=True,
            context=self.context
        ).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    class Meta:
        model = User
        fields = (
            CustomUserSerializer.Meta.fields + ('recipes', 'recipes_count')
        )


class CartSerializer(FavoriteSerializer):
    """Сериализатор для Списка покупок"""
    def validate(self, obj):
        user = self.context['request'].user
        recipe = obj['recipe']
        cart_exists = user.shopping_cart.filter(recipe=recipe).exists()

        if self.context.get('request').method == 'POST' and cart_exists:
            raise serializers.ValidationError(
                'Этот рецепт уже добавлен в корзину'
            )
        if self.context.get('request').method == 'DELETE' and not cart_exists:
            raise serializers.ValidationError(
                'Этот рецепт отсутсвует в корзине'
            )

    class Meta(FavoriteSerializer.Meta):
        model = Cart
