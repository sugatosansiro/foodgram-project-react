import base64
from django.core.files.base import ContentFile
from django.db import transaction
from djoser.serializers import UserCreateSerializer, UserSerializer
# from django.shortcuts import get_object_or_404
from rest_framework.validators import UniqueTogetherValidator
from rest_framework import serializers
from recipes.models import (Cart, Favorite, Ingredient, Recipe,
                            RecipeIngredients,
                            Subscription, Tag)
from users.models import User


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
            # 'password',
        )


class CustomUserCreateSerializer(UserCreateSerializer):
    password = serializers.CharField(write_only=True)

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

    # def to_internal_value(self, data):
    #     if not Ingredient.objects.filter(id=data.get('id')).exists():
    #         raise serializers.ValidationError(
    #             'Такой ингредиент не найден'
    #         )
    #     return data


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = '__all__'

    # def to_internal_value(self, data):
    #     if not Ingredient.objects.filter(id=data.get('id')).exists():
    #         raise serializers.ValidationError(
    #             'Такой тэг не найден'
    #         )
    #     return data


# class RecipeIngredientSerializer(serializers.ModelSerializer):
#     id = serializers.PrimaryKeyRelatedField(
#         queryset=Ingredient.objects.all()
#     )

#     class Meta:
#         model = RecipeIngredients
#         fields = ('id', 'amount')


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

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'tags',
            'author',
            'image',
            'pub_date',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
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

# убираем_дубли ранее был RecipeSerializer
# class RecipeSerializer(serializers.ModelSerializer):
#     ingredients = RecipeIngredientGetSerializer(
#         many=True,
#         source='recipe_ingredient'
#     )
#     tags = TagSerializer(many=True)
#     image = Base64ImageField()
#     author = CustomUserSerializer(required=False)


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
#     class Meta:
#         model = Recipe
#         fields = (
#             'id',
#             'tags',
#             'author',
#             'ingredients',
#             'name',
#             'image',
#             'text',
#             'cooking_time'
#         )


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    ingredients = IngredientCreateInRecipeSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all()
    )
    image = Base64ImageField()
    author = CustomUserSerializer(required=False)

    # def validate_ingredients(self, value):
    #     if len(value) < 1:
    #         raise serializers.ValidationError(
    #             'Добавьте хотя-бы один ингредиент')
    #     return value
    #
    # def validate(self, data):
    #     """Валидация ингердиентов и тэгов в рецепте"""
    #     ingredients = data.get('ingredients')
    #     tags = data.get('tags')
    #     if not ingredients:
    #         raise serializers.ValidationError(
    #             'Добавьте хотя бы один ингредиент'
    #         )
    #     ingredients_list = []
    #     for ingr_i in ingredients:
    #         ingredient = get_object_or_404(
    #             Ingredient,
    #             id=ingr_i.get('id')
    #         )
    #         if ingredient in ingredients_list:
    #             raise serializers.ValidationError(
    #                 'Ингредиенты не должны повторяться'
    #             )
    #         ingredients_list.append(ingredient)
    #     if not tags:
    #         raise serializers.ValidationError(
    #             'Укажите хотя бы один тэг для рецепта'
    #         )
    #     return data

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

# убираем_дубли ранее был RecipeSerializer
    def to_representation(self, obj):
        return RecipeSerializer(
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


# class SubscriptionSerializer(serializers.ModelSerializer):
#     """Сериализатор для подписки на авторов рецептов"""
#     user = serializers.SlugRelatedField(
#         slug_field='username',
#         read_only=True,
#         default=serializers.CurrentUserDefault()
#     )
#     following = serializers.SlugRelatedField(
#         slug_field='username',
#         queryset=User.objects.all()
#     )

#     class Meta:
#         fields = '__all__'
#         model = Subscription
#         validators = [
#             UniqueTogetherValidator(
#                 queryset=Subscription.objects.all(),
#                 fields=('user', 'following')
#             )
#         ]

#     def validate(self, data):
#         if self.context['request'].user == data['follower']:
#             raise serializers.ValidationError(
#                 'Зачем подписаться на самого себя?)'
#             )
#         return data


class SubscriptionGetSerializer(CustomUserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    # Переопределение на базовый
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
