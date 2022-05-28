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
from posts.forms import PostForm

from posts.models import Comment, Follow, Group, Post

User = get_user_model()


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='posts_test')
        cls.author = User.objects.create_user(username='posts_test2')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.group2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test_slug2',
            description='Тестовое описание 2',
        )
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
        cls.post = Post.objects.create(
            text='Тестовый текст поста',
            author=cls.author,
            group=cls.group,
            image=cls.uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self) -> None:
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostsPagesTests.user)
        self.authorized_author_client = Client()
        self.authorized_author_client.force_login(self.author)

    def test_pages_use_correct_templates(self):
        """Проверяем что URL адреса использую корректные шаблоны."""
        post = PostsPagesTests.post
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': self.group.slug}):
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

    # Проверка словаря контекста главной страницы (в нём передаётся форма)
    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        # Словарь ожидаемых типов полей формы:
        # указываем, объектами какого класса должны быть поля формы
        form_fields = {
            # При создании формы поля модели типа TextField 
            # преобразуются в CharField с виджетом forms.Textarea  
            'text': forms.fields.TextField,
            'pub_date': forms.fields.DateTimeField,
            'user': forms.fields.ForeignKey,
            'author': forms.fields.ForeignKey,
            'image': forms.fields.ImageField,
        }        

        # Проверяем, что типы полей формы в словаре context соответствуют ожиданиям
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                # Проверяет, что поле формы является экземпляром
                # указанного класса
                self.assertIsInstance(form_field, expected)

    # Проверяем, что словарь context страницы /index
    # в первом элементе списка содержит ожидаемые значения 
    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse('posts:index'))
        self.correct_context(response)

    # Проверяем, что словарь context страницы group/test_slug
    # содержит ожидаемые значения 
    def test_group_posts_pages_show_correct_context(self):
        """Шаблон group_posts сформирован с правильным контекстом."""
        response = (self.authorized_client.
            get(reverse('posts:group_posts', kwargs={'slug': self.group.slug})))
        self.assertEqual(response.context.get('post').text, self.post.text)
        self.assertEqual(response.contextget('post').image, self.post.image)
        self.assertEqual(response.context.get('group').slug, 'test_slug') 
        self.assertEqual(response.contextget('group').description,
                         self.group.description)
        self.correct_context(response, group=PostsPagesTests.group)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:profile',
            kwargs={'username': self.author.username})
        )
        first_object = response.context['page'][0]
        post_text_0 = first_object.text
        post_author_0 = first_object.author.username
        post_pic_0 = first_object.image

        self.assertEqual(
            post_text_0,
            'Тестовый текст поста',
            'Неверный текст поста на странице профиля'
        )
        self.assertEqual(
            post_author_0,
            f'{self.author.username}',
            'Неверный автор поста на странице профиля'
        )
        self.assertEqual(
            post_pic_0,
            f'{self.post.image}',
            'Неверный текст поста на главной странице'
        )
        self.correct_context(
            response,
            author=PostsPagesTests.author,
            post_id=PostsPagesTests.post.id
        )

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': 'self.post.id'})
        )
        self.assertEqual(response.context.get('post').group, self.post.group)
        self.assertEqual(response.context.get('post').autor, self.post.autor)
        self.assertEqual(response.context.get('post').text, self.post.text)
        self.assertEqual(response.contextget('post').image, self.post.image)
        self.assertEqual(response.context.get('group').slug, 'test_slug') 
        self.assertEqual(response.context.get('group').description,
                         self.group.description)

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_author.get(
            reverse('post:post_edit', kwargs={'post_id': self.first_post.pk}))
        obj_from_context = response.context.get('form').fields.get('text')
        self.assertIsInstance(obj_from_context, forms.fields.CharField)
        obj_from_context = response.context.get('form').fields.get('group')
        self.assertIsInstance(obj_from_context, forms.models.ModelChoiceField)
        first_post = self.first_post
        passed_to_context = first_post.text
        from_context = response.context['form']['text'].value()
        self.assertEqual(passed_to_context, from_context)
        # список групп на форме начинается с 0 -> пустого названия
        # поэтому можно брать как номер группы в списке - group.pk
        passed_to_context = first_post.group.pk
        from_context = response.context['form']['group'].value()
        self.assertEqual(passed_to_context, from_context)


    def test_create_edit_post_show_correct_form(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        check_forms = (
            self.authorized_client.get(reverse('posts:post_create')),
            self.authorized_client.get(
                reverse(
                    'posts:post_edit',
                    kwargs={'post_id': self.post.id}
                )
            )
        )
        for form in check_forms:
            self.assertIsInstance(form.context['form'], PostForm)

    def test_pages_having_correct_context(self):
        """Проверка соответствие поста на разных страницах
        что они целиком соответствуют созданному посту."""
        check_pages = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile',
                    kwargs={'username': self.post.author.username}),
        )
        for page in check_pages:
            with self.subTest(page=page):
                response = self.authorized_client.get(page)
                self.assertEqual(response.context['page_obj'][0], self.post)

    def test_guest_pages_has_correct_http_status(self):
        """Тестируем доступность страниц неавторизованными пользователями."""
        post = PostsPagesTests.post
        urls = {
            reverse('posts:index'):
                HTTPStatus.OK,
            reverse('posts:group_list', kwargs={'slug': 'test_slug'}):
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

    def test_error_400(self):
        """Cервер не возвращает код 404, если страница не найдена."""
        response = self.client.get('/summer/')
        self.assertEqual(response.status_code, 404)


    def test_cache_index(self):
        """Тестирование кэширования главной страницы."""
        def response_page():
            response = self.authorized_client.get(
                reverse('posts:index')).content.decode('UTF-8')
            return response

        cache.clear()
        text_cache = self.post.text
        self.assertIn(text_cache, response_page())
        Post.objects.filter(text=text_cache).delete()
        cache.clear()
        self.assertNotIn(text_cache, response_page())