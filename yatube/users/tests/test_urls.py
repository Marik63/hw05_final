from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from http import HTTPStatus

from django.urls import reverse

User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем пользователя
        self.user = StaticURLTests.user
        # Создаем второй клиент
        self.authorized_client = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(self.user)

    def test_guest_pages(self):
        """Тестируем доступность страниц неавторизованными пользователями"""
        urls_status = {
            '/auth/logout/': HTTPStatus.OK,
            '/auth/signup/': HTTPStatus.OK,
            '/auth/login/': HTTPStatus.OK,
            '/auth/password_reset/': HTTPStatus.OK,
            '/auth/password_reset/done/': HTTPStatus.OK,
        }
        for url, expected_status in urls_status.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, expected_status)

    def test_authorized_pages(self):
        """Тестируем доступность страниц авторизованными пользователями"""
        urls_status = {
            '/auth/password_change/': HTTPStatus.OK,
            '/auth/password_change/done/': HTTPStatus.OK,
        }
        for url, expected_status in urls_status.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, expected_status)

    def test_guest_templates(self):
        """Тестируем шаблоны страниц неавторизованных пользователей"""
        url_templates = {
            '/auth/logout/': 'users/logged_out.html',
            '/auth/signup/': 'users/signup.html',
            '/auth/login/': 'users/login.html',
            reverse('users:logout'): 'users/logged_out.html',
            reverse('users:signup'): 'users/signup.html',
            reverse('users:login'): 'users/login.html',
            reverse('users:password_reset'):
                'users/password_reset_form.html',
            reverse('users:password_reset_done'):
                'users/password_reset_done.html',
        }
        for url, expected_template in url_templates.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, expected_template)

    def test_authorized_templates(self):
        """Тестируем шаблоны страниц авторизованных пользователей"""
        url_templates = {
            reverse('users:password_change'):
                'users/password_change_form.html',
            reverse('users:password_change_done'):
                'users/password_change_done.html',
        }
        for url, expected_template in url_templates.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, expected_template)
