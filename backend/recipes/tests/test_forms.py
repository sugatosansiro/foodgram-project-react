import shutil
import tempfile
from http import HTTPStatus
from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from posts.forms import PostForm, CommentForm
from posts.models import Post, Group, User, Comment


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

COMMENTS_COUNT = 1


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_author = User.objects.create_user(username='Author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        super().setUp()
        self.user_guest = Client()
        self.author = Client()
        self.author.force_login(self.user_author)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        post_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        self.form_data = {
            'text': 'Текст Формы',
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.author.post(
            reverse('posts:post_create'),
            data=self.form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.new_post = Post.objects.latest('pub_date')
        self.assertEqual(self.new_post.text, self.form_data['text'])
        self.assertEqual(self.new_post.group.id, self.form_data['group'])
        self.new_post.image.seek(0)
        self.assertEqual(self.new_post.image._get_file().read(), small_gif)
        self.assertEqual(Post.objects.count(), post_count + 1)

    def test_cant_create_with_empty_text(self):
        """Запись в Post не создастся с ошибкой в Форме"""
        post_count = Post.objects.count()
        form_data = {
            'text': '',
            'group': self.group.id
        }
        response = self.author.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.count(), post_count)
        self.assertFormError(
            response,
            'form',
            'text',
            'Обязательное поле.'
        )

    def test_edit_post(self):
        """Валидная форма редактирует запись в Post."""
        self.group = Group.objects.create(
            title='Тестовая группа 2',
            slug='test_slug2',
            description='Тестовое описание 2'
        )
        self.post = Post.objects.create(
            author=self.user_author,
            text='Тестовый текст0',
        )
        post_count = Post.objects.count()
        form_data = {
            'text': 'Текст ИЗМЕНЕН',
            'group': self.group.id,
        }
        response = self.author.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.id}
            ),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        edited_post = Post.objects.get()
        self.assertEqual(edited_post.text, form_data['text'])
        self.assertEqual(edited_post.group.id, form_data['group'])
        self.assertEqual(Post.objects.count(), post_count)


class CommentCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_author = User.objects.create_user(username='Author')
        cls.user = User.objects.create_user(username='StasBasov')

    def setUp(cls):
        super().setUp()
        cls.user_guest = Client()
        cls.author = Client()
        cls.author.force_login(cls.user_author)
        cls.user_authorized = Client()
        cls.user_authorized.force_login(cls.user)
        cls.post = Post.objects.create(
            author=cls.user_author,
            text='Тестовый текст0',
        )
        cls.rev_detail = reverse(
            'posts:post_detail',
            kwargs={'post_id': cls.post.id}
        )
        cls.comment_data = {
            'text': 'Комментарий 1',
        }
        cls.post_comment = cls.user_authorized.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': cls.post.id}
            ),
            data=cls.comment_data,
            follow=True
        )

    def test_comment_post(self):
        """Валидная форма добавляет комментарий в Post."""
        response = self.user_authorized.get(self.rev_detail)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn('comments', response.context)
        self.assertTrue(
            len(response.context['comments']) == COMMENTS_COUNT
        )
        obj_1 = response.context['comments'][0]
        self.assertIsInstance(obj_1, Comment)
        self.assertEqual(obj_1.author, self.user)
        self.assertEqual(obj_1.text, self.comment_data['text'])

    def test_comment_for_quest(self):
        """Неавторизованный пользователь не может добавить комментарий."""
        comment_data = {
            'text': 'Комментарий 2',
        }
        self.user_guest.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': self.post.id}
            ),
            data=comment_data,
            follow=True
        )
        response = self.user_guest.get(self.rev_detail)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        comment = Comment.objects.get()
        self.assertNotEqual(comment.text, comment_data['text'])
        self.assertTrue(
            len(response.context['comments']) == COMMENTS_COUNT
        )


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.form_labels = {
            'text': 'Текст поста',
            'group': 'Группа'
        }
        cls.help_texts = {
            'text': 'Текст нового поста',
            'group': 'Группа, к которой будет относиться пост'
        }

    def test_text_label(self):
        for text, label in self.form_labels.items():
            text_label = PostForm().fields[text].label
            self.assertEqual(text_label, label)

    def test_help_texts(self):
        for text, label in self.help_texts.items():
            text_label = PostForm().fields[text].help_text
            self.assertEqual(text_label, label)


class CommentFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.form_labels = {'text': 'Комментарий'}
        cls.help_texts = {'text': 'Комментарий к посту'}

    def test_comment_label(self):
        for text, label in self.form_labels.items():
            text_label = CommentForm().fields[text].label
            self.assertEqual(text_label, label)

    def test_comment_help_texts(self):
        for text, label in self.help_texts.items():
            help_texts = CommentForm().fields[text].help_text
            self.assertEqual(help_texts, label)
