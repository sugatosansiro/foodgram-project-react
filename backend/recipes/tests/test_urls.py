from http import HTTPStatus
from django.core.cache import cache
from django.test import TestCase, Client
from django.urls import reverse
from posts.models import Post, Group, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_author = User.objects.create_user(username='Author')
        cls.user = User.objects.create_user(username='StasBasov')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            author=cls.user_author,
            text='Тестовый пост'
        )

        cls.rev_index = '/'
        cls.rev_group = f'/group/{cls.group.slug}/'
        cls.rev_profile = f'/profile/{cls.post.author}/'
        cls.rev_detail = f'/posts/{cls.post.id}/'
        cls.rev_edit = f'/posts/{cls.post.id}/edit/'
        cls.rev_create = '/create/'
        cls.rev_login = reverse('users:login')
        cls.rev_follow = '/follow/'
        cls.rev_author_follow = f'/profile/{cls.post.author}/follow/'
        cls.rev_404 = '/unexisting_page/'

        cls.urls_for_guest = [
            cls.rev_index,
            cls.rev_group,
            cls.rev_profile,
            cls.rev_detail
        ]

        cls.urls_for_authorized = [
            cls.rev_index,
            cls.rev_group,
            cls.rev_profile,
            cls.rev_detail,
            cls.rev_create,
            cls.rev_follow,
        ]

        cls.urls_for_author = [
            cls.rev_index,
            cls.rev_group,
            cls.rev_profile,
            cls.rev_detail,
            cls.rev_create,
            cls.rev_edit,
            cls.rev_follow,
        ]

        cls.redirect_for_guest = {
            cls.rev_create: (cls.rev_login + '?next=' + cls.rev_create),
            cls.rev_edit: (cls.rev_login + '?next=' + cls.rev_edit),
            cls.rev_author_follow: (
                cls.rev_login + '?next=' + cls.rev_author_follow
            )
        }

        cls.url_template_dict = {
            cls.rev_index: 'posts/index.html',
            cls.rev_group: 'posts/group_list.html',
            cls.rev_profile: 'posts/profile.html',
            cls.rev_create: 'posts/create_post.html',
            cls.rev_detail: 'posts/post_detail.html',
            cls.rev_edit: 'posts/create_post.html',
            cls.rev_follow: 'posts/follow.html',
            cls.rev_404: 'core/404.html',
        }

    def setUp(self):
        cache.clear()
        self.user_guest = Client()
        self.author = Client()
        self.author.force_login(self.user_author)
        self.user_authorized = Client()
        self.user_authorized.force_login(self.user)

    def test_redirection_for_guest(self):
        """Перенаправление анонимного пользователя на другую страницу."""
        for url_name, url in self.redirect_for_guest.items():
            with self.subTest(url_name=url_name):
                response = self.user_guest.get(url_name, follow=True)
                self.assertRedirects(response, url)

    def test_unexisting_url(self):
        """Страница '/unexisting_page/ НЕ доступна любому пользователю."""
        response = self.user_guest.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')

    def test_urls_for_guest(self):
        """Страницы, доступные любому пользователю."""
        for url in self.urls_for_guest:
            with self.subTest(url=url):
                response = self.user_guest.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_for_authorized(self):
        """Страницы, доступные авторизованному пользователю."""
        for url in self.urls_for_authorized:
            with self.subTest(url=url):
                response = self.user_authorized.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_for_author(self):
        """Страницы, доступные автору поста."""
        for url in self.urls_for_author:
            with self.subTest(url=url):
                response = self.author.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for url, template in self.url_template_dict.items():
            with self.subTest(url=url):
                response = self.author.get(url)
                self.assertTemplateUsed(response, template)

    def test_redirection_for_authorized(self):
        """Перенаправление автора на другую страницу."""
        response = self.user_authorized.get(self.rev_edit, follow=True)
        self.assertRedirects(response, self.rev_detail)
