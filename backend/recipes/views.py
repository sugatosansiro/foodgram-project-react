from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from foodgram.settings import RECIPES_ON_PAGE
from .models import Recipe, Follow
from users.models import User
from recipes.forms import RecipeForm


def index(request):
    recipe_list = Recipe.objects.select_related('author', 'tags')
    paginator = Paginator(recipe_list, RECIPES_ON_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'recipes/index.html', context)


# def group_posts(request, slug):
#     group = get_object_or_404(Group, slug=slug)
#     post_list = group.posts.select_related('author', 'group')
#     paginator = Paginator(post_list, POSTS_ON_PAGE)
#     page_number = request.GET.get('page')
#     page_obj = paginator.get_page(page_number)
#     context = {
#         'group': group,
#         'page_obj': page_obj,
#     }
#     return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    recipe_list = author.recipe.select_related('author', 'tags')
    paginator = Paginator(recipe_list, RECIPES_ON_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    following = (
        request.user.is_authenticated
        and author.following.filter(user=request.user).exists()
    )
    context = {
        'author': author,
        'page_obj': page_obj,
        'following': following,
    }
    return render(request, 'recipes/profile.html', context)


def recipe_detail(request, recipe_id):
    recipe = get_object_or_404(Recipe.objects.filter(id=recipe_id))
    context = {
        'recipe': recipe,
    }
    return render(request, 'recipes/recipe_detail.html', context)


@login_required
def recipe_create(request):
    form = RecipeForm(request.POST or None, files=request.FILES or None)
    if not (request.method == 'POST' and form.is_valid()):
        context = {'form': form}
        return render(request, 'recipes/create_recipe.html', context)
    recipe = form.save(commit=False)
    recipe.author = request.user
    recipe.save()
    return redirect('recipes:profile', recipe.author)


@login_required
def recipe_edit(request, recipe_id):
    recipe = get_object_or_404(Recipe, id=recipe_id)
    if recipe.author != request.user:
        return redirect('recipes:recipe_detail', recipe_id=recipe.id)
    form = RecipeForm(
        request.POST or None,
        files=request.FILES or None,
        instance=recipe)
    if request.method != 'POST' or not form.is_valid():
        context = {'form': form, 'is_edit': True}
        return render(request, 'recipes/create_recipe.html', context)
    recipe.save()
    return redirect('recipes:recipe_detail', recipe_id=recipe.id)


@login_required
def follow_index(request):
    recipe_list = Recipe.objects.filter(author__following__user=request.user)
    paginator = Paginator(recipe_list, RECIPES_ON_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'recipes/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user == author:
        return redirect('recipes:profile', username=username)
    Follow.objects.get_or_create(
        user=request.user,
        author=author
    )
    return redirect('recipes:follow_index')


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(
        user=request.user,
        author=author,
    ).delete()
    return redirect('recipes:follow_index')
