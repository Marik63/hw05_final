from django.contrib.auth import get_user_model
from django import forms
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Post, Group

User = get_user_model()


class UsersPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='posts_test')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='posts_test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост для проверки',
        )
        cls.group_post = Post.objects.create(
            author=cls.user,
            text='Групповой тестовый пост для проверки',
            group=cls.group,
        )

    def setUp(self) -> None:
        self.authorized_client = Client()
        self.authorized_client.force_login(UsersPagesTests.user)

    def test_user_signup_page_show_correct_context(self):
        """Проверяем что signup имеет правильный context"""
        response = self.client.get(reverse('users:signup'))
        form_fields = {
            'first_name': forms.fields.CharField,
            'last_name': forms.fields.CharField,
            'username': forms.fields.CharField,
            'email': forms.fields.CharField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
