from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from posts.models import Group, Post
from django.urls import reverse

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Иван')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост для проверки',
        )

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем автора
        self.author_client = Client()
        self.author_client.force_login(self.user)
        # Создаем авторизованный клиент
        self.authorized_client = Client()
        self.user = User.objects.create_user(username='Петя')
        # Авторизуем пользователя
        self.authorized_client.force_login(self.user)

    def test_guest_urls(self):
        """Тестируем дотупность страниц любым пользователям."""
        urls = [
            '/',
            f'/group/{self.group.slug}/',
            f'/profile/{self.user.username}/',
            f'/posts/{self.post.id}/'
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_authorized_pages(self):
        """Тестируем доступность страниц авторизованными пользователями."""
        urls = [
            '/',
            '/create/',
            f'/group/{self.group.slug}/',
            f'/profile/{self.user.username}/',
            f'/posts/{self.post.id}/',
            f'/posts/{self.post.id}/edit/'
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.author_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_error_404(self):
        """Cервер не возвращает код 404, если страница не найдена."""
        response = self.guest_client.get('/summer/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_guest_redirect(self):
        """Проверка редирект для неавторизированного пользователя."""
        urls_redirect = {
            '/create/': '/auth/login/?next=/create/',
            f'/posts/{self.post.id}/edit/': '/auth/login/?next='
            + f'/posts/{self.post.id}/edit/',
            f'/posts/{self.post.id}/comment/': '/auth/login/?next='
            + f'/posts/{self.post.id}/comment/'
        }
        for url, redirect in urls_redirect.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertRedirects(response, redirect)

    def test_not_author_redirect(self):
        """Проверка редирект не для автора."""
        url = f'/posts/{self.post.id}/edit/'
        print(reverse('posts:post_edit', args=[self.post.id]))
        print(url)
        redirect = f'/posts/{self.post.id}/'
        response = self.authorized_client.get(url)
        self.assertRedirects(response, redirect)

    def test_comment_authorized_client_redirect(self):
        """Проверка редирект коммента для авторизованного
        пользователя на страницу поста.
        """
        url = reverse('posts:add_comment', args=[self.post.id])
        redirect = reverse('posts:post_detail', args=[self.post.id])
        response = self.authorized_client.get(url)
        self.assertRedirects(response, redirect)

    def test_pages_use_correct_templates(self):
        """Проверяем что URL адреса использую корректные шаблоны."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', args=[self.group.slug]):
                'posts/group_list.html',
            reverse('posts:profile', args=[self.user.username]):
                'posts/profile.html',
            reverse('posts:post_detail', args=[self.post.id]):
                'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit', args=[self.post.id]):
                'posts/create_post.html'
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.author_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
