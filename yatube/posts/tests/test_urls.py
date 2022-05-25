from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from http import HTTPStatus

from posts.models import Group, Post

User = get_user_model()


class TaskURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Создадим запись в БД для проверки доступности адреса group/test-slug/
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test_slug',
            description='Тестовое описание',
        )

        cls.post = Post.objects.create(
            author=cls.user,
            text='Текст поста',
        )

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем авторизованый клиент
        self.user = TaskURLTests.user
        # Создаем второй клиент
        self.authorized_client = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(self.user)

    def test_authorized_pages(self):
        """Тестируем доступность страниц авторизованными пользователями и
        доступность страниц автором."""
        post = TaskURLTests.post
        urls = {
            '/create/': HTTPStatus.OK,
            f'/posts/{post.id}/edit/': HTTPStatus.OK,
        }
        for field, expected_value in urls.items():
            with self.subTest(field=field):
                response = self.authorized_client.get(field)
                self.assertEqual(response.status_code, expected_value)

    def test_guest_templates(self):
        """Тестируем шаблоны общедоступных страниц."""
        post = TaskURLTests.post
        url_templates = {
            '/': 'posts/index.html',
            '/group/test_slug/': 'posts/group_list.html',
            '/profile/auth/': 'posts/profile.html',
            f'/posts/{post.id}/': 'posts/post_detail.html',
        }
        for url, expected_template in url_templates.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, expected_template)

    def test_author_templates(self):
        """Тестируем шаблоны страниц авторизованного пользователя и автора."""
        post = TaskURLTests.post
        url_templates = {
            '/create/': 'posts/create_post.html',
            f'/posts/{post.id}/edit/': 'posts/create_post.html',
        }
        for url, expected_template in url_templates.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, expected_template)

    def test_guest_pages(self):
        """Тестируем доступность страниц неавторизованными пользователями."""
        post = TaskURLTests.post
        urls = {
            '/': HTTPStatus.OK,
            '/group/test_slug/': HTTPStatus.OK,
            '/profile/auth/': HTTPStatus.OK,
            f'/posts/{post.id}/': HTTPStatus.OK,
            '/unexisting_page/': HTTPStatus.NOT_FOUND,
        }
        for field, expected_value in urls.items():
            with self.subTest(field=field):
                response = self.guest_client.get(field)
                self.assertEqual(response.status_code, expected_value)
