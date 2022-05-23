from http import HTTPStatus

from django.test import TestCase, Client
from django.urls import reverse


class StaticViewsTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_about_pages_accessible_by_name(self):
        """URLs, приложения about доступны."""
        urls = {
            reverse('about:author'): HTTPStatus.OK,
            reverse('about:tech'): HTTPStatus.OK,
        }
        for url, expected_status in urls.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, expected_status)

    def test_about_pages_uses_correct_template(self):
        """При запросе к about применяется правильные шаблоны."""
        urls = {
            reverse('about:author'): 'about/author.html',
            reverse('about:tech'): 'about/tech.html',
        }
        for url, expected_template in urls.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, expected_template)
