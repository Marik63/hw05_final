from http import HTTPStatus
import shutil
import tempfile

from django.contrib.auth import get_user_model
from django import forms
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile

from posts.models import Follow, Group, Post

User = get_user_model()


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
small_gif = (
    b"\x47\x49\x46\x38\x39\x61\x02\x00"
    b"\x01\x00\x80\x00\x00\x00\x00\x00"
    b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
    b"\x00\x00\x00\x2C\x00\x00\x00\x00"
    b"\x02\x00\x01\x00\x00\x02\x02\x0C"
    b"\x0A\x00\x3B"
)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        uploaded = SimpleUploadedFile(
            name="small.gif",
            content=small_gif,
            content_type="image/gif"
        )        
        cls.user = User.objects.create_user(username='posts_test')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='posts_test_slug',
            description='Тестовое описание',
        )
        cls.group2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='posts_test_slug2',
            description='Тестовое описание 2',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост для проверки',
            image=uploaded,
        )
        cls.group_post = Post.objects.create(
            author=cls.user,
            text='Групповой тестовый пост для проверки',
            group=cls.group,
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self) -> None:
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostsPagesTests.user)
        cache.clear()

    def test_pages_use_correct_templates(self):
        """Проверяем что URL адреса использую корректные шаблоны."""
        post = PostsPagesTests.post
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': 'posts_test_slug'}):
                'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': 'posts_test'}):
                'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': f'{post.id}'}):
                'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit', kwargs={'post_id': f'{post.id}'}):
                'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_guest_pages_has_correct_http_status(self):
        """Тестируем доступность страниц неавторизованными пользователями."""
        post = PostsPagesTests.post
        urls = {
            reverse('posts:index'):
                HTTPStatus.OK,
            reverse('posts:group_list', kwargs={'slug': 'posts_test_slug'}):
                HTTPStatus.OK,
            reverse('posts:profile', kwargs={'username': 'posts_test'}):
                HTTPStatus.OK,
            reverse('posts:post_detail', kwargs={'post_id': f'{post.id}'}):
                HTTPStatus.OK,
        }
        for url, expected_value in urls.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, expected_value)

    def test_authorized_pages_has_correct_http_status(self):
        """Тестируем доступность страниц авторизованными пользователями."""
        urls = {
            reverse('posts:post_create'): HTTPStatus.OK,
        }
        for field, expected_value in urls.items():
            with self.subTest(field=field):
                response = self.authorized_client.get(field)
                self.assertEqual(response.status_code, expected_value)

    def test_author_pages_has_correct_http_status(self):
        """Тестируем доступность страниц автором."""
        post = PostsPagesTests.post
        urls = {
            reverse('posts:post_edit', kwargs={'post_id': f'{post.id}'}):
                HTTPStatus.OK,
        }
        for field, expected_value in urls.items():
            with self.subTest(field=field):
                response = self.authorized_client.get(field)
                self.assertEqual(response.status_code, expected_value)

    def test_post_detail_page_show_correct_context(self):
        """Проверяем что post_detail имеет правильный context."""
        post = PostsPagesTests.post
        context_pages = {
            reverse('posts:post_detail', kwargs={'post_id': f'{post.id}'}):
                post.id,
        }
        for reverse_name, expect_context in context_pages.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(response.context['post'].id, expect_context)

    def test_post_create_page_show_correct_context(self):
        """Проверяем что post_create имеет правильный context."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_show_correct_context(self):
        """Проверяем что post_edit имеет правильный context."""
        post = PostsPagesTests.post
        url = reverse('posts:post_edit', kwargs={'post_id': f'{post.id}'})
        response = self.authorized_client.get(url)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        is_edit = True
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        self.assertEqual(response.context["is_edit"], is_edit)

    def test_pages_has_correct_context(self):
        """Тестируем что страницы имеют корректный context."""
        paginator_pages = {
            reverse('posts:index'): 'page_obj',
            reverse('posts:group_list', kwargs={
                'slug': 'posts_test_slug'}): 'page_obj',
            reverse('posts:profile', kwargs={'username': 'posts_test'}):
                'page_obj',
        }
        for reverse_name, obj in paginator_pages.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertIsNotNone(response.context[obj])

    def test_grouped_post_show_in_pages(self):
        """Проверяем что пост с группой попадает на страницы."""
        group_post_pages = {
            reverse('posts:index'): 2,
            reverse('posts:group_list', kwargs={'slug': 'posts_test_slug'}): 1,
            reverse('posts:profile', kwargs={'username': 'posts_test'}): 2,
        }
        for value, expected in group_post_pages.items():
            with self.subTest(value=value):
                response = self.authorized_client.get(value)
                self.assertEqual(len(response.context["page_obj"]), expected)

    def test_new_group_page_dont_have_a_post(self):
        """Проверяем что страница новой группы не имеет постов."""
        url = reverse('posts:group_list', args=['posts_test_slug2'])
        response = self.authorized_client.get(url)
        self.assertEqual(len(response.context["page_obj"]), 0)
