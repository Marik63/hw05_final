from http import HTTPStatus

from django.test import TestCase, Client


class StaticURLTests(TestCase):
    def setUp(self):
        """Настройка класса."""
        self.guest_client = Client()

    def test_about_pages(self):
        """Тестируем доступность страниц приложения about."""
        urls = {
            '/about/author/': HTTPStatus.OK,
            '/about/tech/': HTTPStatus.OK,
        }
        for url, expected_status in urls.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, expected_status)

    def test_about_templates(self):
        """Тестируем использование шаблонов приложения about."""
        urls = {
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html',
        }
        for url, expected_template in urls.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, expected_template)
