import shutil
import tempfile
from django import forms
from django.core.cache import cache
from django.conf import settings
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from yatube.settings import POSTS_ON_PAGE
from posts.models import Post, Group, User, Follow


POST_COUNTER_1 = 13
CACHE_TIME = 1

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cache.clear()
        cls.user_author = User.objects.create_user(username='Author')
        cls.user = User.objects.create_user(username='StasBasov')
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )

        cls.group_0 = Group.objects.create(
            title='Тестовая группа 0',
            slug='test_slug_0',
            description='Тестовое описание 0'
        )

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание'
        )

        cls.post = Post.objects.create(
            author=cls.user_author,
            text='Тестовый пост',
            group=cls.group,
            image=cls.uploaded
        )

        cls.rev_index = reverse('posts:index')
        cls.rev_group = reverse(
            'posts:group_list',
            kwargs={'slug': cls.group.slug}
        )
        cls.rev_group_0 = reverse(
            'posts:group_list',
            kwargs={'slug': cls.group_0.slug}
        )
        cls.rev_profile = reverse(
            'posts:profile',
            kwargs={'username': cls.post.author}
        )
        cls.rev_detail = reverse(
            'posts:post_detail',
            kwargs={'post_id': cls.post.id}
        )
        cls.rev_edit = reverse(
            'posts:post_edit',
            kwargs={'post_id': cls.post.id}
        )
        cls.rev_create = reverse('posts:post_create')
        cls.rev_login = reverse('users:login')

        cls.url_template_dict = {
            cls.rev_index: 'posts/index.html',
            cls.rev_group: 'posts/group_list.html',
            cls.rev_profile: 'posts/profile.html',
            cls.rev_create: 'posts/create_post.html',
            cls.rev_detail: 'posts/post_detail.html',
            cls.rev_edit: 'posts/create_post.html'
        }

    def setUp(self):
        cache.clear()
        self.user_guest = Client()
        self.author = Client()
        self.author.force_login(self.user_author)
        self.user_authorized = Client()
        self.user_authorized.force_login(self.user)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for reverse_name, template in self.url_template_dict.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.author.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_group_list_pages_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.user_authorized.get(self.rev_group).context
        group_obj = response['group']
        self.assertIn('group', response)
        self.assertIsInstance(response['group'], Group)
        self.assertEqual(group_obj.title, self.group.title)
        self.assertEqual(group_obj.slug, self.group.slug)
        self.assertEqual(group_obj.description, self.group.description)

    def test_zero_group_list_page_is_empty(self):
        """Проверка что в другой групее не создалось постов."""
        response = (self.user_authorized.get(self.rev_group_0))
        self.assertTrue(response.context['page_obj'].paginator.count == 0)

    def test_create_post_and_edit_post_shows_correct_context(self):
        """Шаблоны create_post и edit_post имеют правильный контекст."""
        response_create = self.user_authorized.get(self.rev_create)
        response_edit = self.author.get(self.rev_edit)
        responses = [response_create, response_edit]
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
            'image': forms.fields.ImageField,
        }
        for response in responses:
            with self.subTest(response=response):
                for value, expected in form_fields.items():
                    with self.subTest(value=value):
                        field = response.context.get('form').fields.get(value)
                        self.assertIsInstance(field, expected)
        self.assertTrue(response_edit.context.get('is_edit'))

    def test_index_and_profile_and_group_list_pages_show_correct_context(self):
        """Шаблоны index, profile, group_list
        сформированы с правильным контекстом."""
        rev_list = [
            self.rev_index,
            self.rev_profile,
            self.rev_group
        ]
        for url in rev_list:
            with self.subTest(url=url):
                response = self.user_authorized.get(url)
                self.assertIn('page_obj', response.context)
                self.assertTrue(
                    response.context['page_obj'].paginator.count > 0
                )
                obj_1 = response.context['page_obj'][0]
                self.assertIsInstance(obj_1, Post)
                self.assertEqual(
                    obj_1.author,
                    self.user_author
                )
                self.assertEqual(obj_1.text, self.post.text)
                self.assertEqual(obj_1.group, self.post.group)
                obj_1.image.seek(0)
                self.post.image.seek(0)
                self.assertEqual(
                    obj_1.image._get_file().read(),
                    self.post.image._get_file().read()
                )

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.user_guest.get(self.rev_profile).context
        self.assertIn('author', response)
        self.assertIsInstance(response['author'], User)
        self.assertEqual(
            response['author'].username,
            self.user_author.username
        )


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cache.clear()
        cls.user_guest = Client()
        cls.user_author = User.objects.create_user(username='Author')
        cls.author = Client()
        cls.author.force_login(cls.user_author)
        cls.user = User.objects.create_user(username='StasBasov')
        cls.user_authorized = Client()
        cls.user_authorized.force_login(cls.user)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание'
        )

        posts_list = []
        for posts_counter in range(POST_COUNTER_1):
            posts_list.append(
                Post(
                    author=cls.user_author,
                    text=f'Тест. пост № {posts_counter}',
                    group=cls.group,
                )
            )
        Post.objects.bulk_create(posts_list)
        cls.post = Post.objects.get(id=POST_COUNTER_1)

        cls.rev_index = reverse('posts:index')
        cls.rev_group = reverse(
            'posts:group_list',
            kwargs={'slug': cls.group.slug}
        )
        cls.rev_profile = reverse(
            'posts:profile',
            kwargs={'username': cls.post.author}
        )

    def test_paginator(self):
        """Проверка пагинатора"""
        paginator_list = [
            self.rev_index,
            self.rev_group,
            self.rev_profile,
        ]

        pages_dict = {
            '?page=1': POSTS_ON_PAGE,
            '?page=2': POST_COUNTER_1 - POSTS_ON_PAGE,
        }

        for url in paginator_list:
            with self.subTest(url=url):
                for page, post_count in pages_dict.items():
                    with self.subTest(page=page):
                        response = self.user_guest.get(url + page)
                        self.assertEqual(
                            len(response.context['page_obj']),
                            post_count
                        )


class CacheViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cache.clear()
        cls.user_author = User.objects.create_user(username='Author')
        cls.author = Client()
        cls.author.force_login(cls.user_author)
        cls.post_cache = Post.objects.create(
            author=cls.user_author,
            text='Кэшируемый пост'
        )
        cls.rev_index = reverse('posts:index')

    def test_cache(self):
        """Проверка кэширования"""
        response = self.author.get(self.rev_index)
        self.assertIn(self.post_cache, response.context['page_obj'])
        self.post_cache.delete()
        response = self.author.get(self.rev_index)
        self.assertNotIn(self.post_cache, response.context['page_obj'])
        self.assertIn(self.post_cache.text, response.content.decode())
        cache.clear()
        response = self.author.get(self.rev_index)
        self.assertNotIn(self.post_cache.text, response.content.decode())


class FollowViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cache.clear()
        cls.user_author = User.objects.create_user(username='Author')
        cls.user_1 = User.objects.create_user(username='StasBasov')
        cls.user_2 = User.objects.create_user(username='BasStasov')
        cls.post = Post.objects.create(
            author=cls.user_author,
            text='Тестовый пост'
        )
        cls.rev_index = reverse('posts:index')
        cls.rev_follow = '/follow/'
        cls.rev_author_follow = f'/profile/{cls.post.author}/follow/'
        cls.rev_author_unfollow = f'/profile/{cls.post.author}/unfollow/'

    def setUp(self):
        cache.clear()
        self.author = Client()
        self.author.force_login(self.user_author)
        self.user_authorized_1 = Client()
        self.user_authorized_1.force_login(self.user_1)
        self.user_authorized_2 = Client()
        self.user_authorized_2.force_login(self.user_2)

    def test_post_for_follower(self):
        """Проверка появления поста в ленте после подписки"""
        Follow.objects.create(
            user=self.user_1,
            author=self.user_author
        )
        response = self.user_authorized_1.get(self.rev_follow)
        self.assertIn('page_obj', response.context)
        self.assertTrue(
            response.context['page_obj'].paginator.count > 0
        )
        obj_1 = response.context['page_obj'][0]
        self.assertIsInstance(obj_1, Post)
        self.assertEqual(
            obj_1.author,
            self.user_author
        )

    def test_post_for_non_followers(self):
        """Проверка, что новый пост не появится у не-подписчика"""
        response = self.user_authorized_2.get(self.rev_follow)
        self.assertIn('page_obj', response.context)
        self.assertNotIn(self.post, response.context['page_obj'])

    def test_user_follow_author(self):
        """Проверка подписки на автора"""
        self.assertFalse(Follow.objects.filter(
            user=self.user_2,
            author=self.user_author
        ).exists())
        self.user_authorized_2.post(
            self.rev_author_follow,
            follow=True
        )
        self.assertTrue(Follow.objects.filter(
            user=self.user_2,
            author=self.user_author
        ).exists())

    def test_unfollow_author(self):
        """Проверка отписки от автора"""
        Follow.objects.create(
            user=self.user_1,
            author=self.user_author
        )
        self.user_authorized_1.post(
            self.rev_author_unfollow,
            follow=True
        )
        self.assertFalse(Follow.objects.filter(
            user=self.user_1,
            author=self.user_author
        ).exists())
