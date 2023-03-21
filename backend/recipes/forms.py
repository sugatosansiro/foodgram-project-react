from django import forms
from .models import Recipe


class RecipeForm(forms.ModelForm):
    class Meta:
        model = Recipe
        fields = (
            'name',
            'ingredients',
            'tags',
            'image',
            'text',
            'cooking_time'
        )
        labels = {
            'name': 'Название рецепта',
            'ingredients': 'Список ингридиентов',
            'tags': 'Тэги',
            'image': 'Изображение',
            'text': 'Описание рецепта',
            'cooking_time': 'Время приготовления (в минутах)',
        }
        help_texts = {
            'name': 'Назовите ваш рецепт',
            'ingredients': 'Введите список ингридиентов',
            'tags': 'Укажите подходящие тэги',
            'image': 'Загрузите изображение к рецепту',
            'text': 'Подробно опишите рецепт',
            'cooking_time': 'Время приготовления (в минутах)'
        }
