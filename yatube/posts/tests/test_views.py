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

@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
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

    def compare_objects(self, post):
        self.assertEqual(post.text, f'{self.post.text}')
        self.assertEqual(post.author.username, self.user.username)
        self.assertEqual(post.group, self.group)
        self.assertEqual(post.image, self.post.image)

    def create_follower(self):
        another_user = User.objects.create_user(username='admin')
        self.authorized_client.force_login(another_user)

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

    def test_error_400(self):
        """Cервер не возвращает код 404, если страница не найдена."""
        response = self.client.get('/summer/')
        self.assertEqual(response.status_code, 404)



class TestComment(TestCase):
    def setUp(self):
        self.client = Client()
        self.user_user = User.objects.create_user(username='user')
        self.user_user2 = User.objects.create_user(username='user2')
        self.post_user2 = Post.objects.create(
            text='текст',
            author=self.user_user2
        )
        self.data_page_user2 = {'username': self.user_user2.username,
                               'post_id': self.post_user2.id}

        self.data_comment = {'text': 'Комментарий'}

    def test_comment_authorized_user(self):
        """Авторизованный пользователь мщжет оставить комментарий под другим постом."""
        self.client.force_login(self.user_user)
        post_add_comment = reverse('add_comment', kwargs=self.data_page_user2)
        self.client.post(post_add_comment, self.data_comment)
        post_view_url = reverse(
            'post_view', kwargs=self.data_page_user2)
        response = self.client.get(post_view_url)
        self.assertContains(response,
                            text=self.data_comment['text'],
                            status_code=200)

    def test_comment_unauthorized_user(self):
        """Авторизованный пользователь может оставить комментарий под другим постом."""
        post_add_comment = reverse('add_comment', kwargs=self.data_page_user2)
        self.client.post(post_add_comment, self.data_comment)
        post_view_url = reverse(
            'post_view', kwargs=self.data_page_user2)
        response = self.client.get(post_view_url)
        self.assertNotContains(response,
                               text=self.data_comment['text'],
                               status_code=200)



    def test_cache_index(self):
        """Тестирование кэширования главной страницы"""
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


class TestFollow(TestCase):
    def setUp(self):
        self.client = Client()
        self.user_user = User.objects.create_user(username='user')
        self.user_user2 = User.objects.create_user(username='user2')
        self.data_page_user2 = {'username': self.user_user2.username}
        self.post_user2 = Post.objects.create(
            text='текст', author=self.user_user2)
        self.client.force_login(self.user_user)

    def test_follow_unfollow(self):
        """Авторизованный пользователь не может подписываться на других пользователей."""
        follow_url = reverse(
            'profile_follow',  kwargs=self.data_page_user2)
        self.client.get(follow_url)
        follow = Follow.objects.filter(
            user=self.user_user,
            author=self.user_user2
        ).exists()

        unfollow_url = reverse(
            'profile_unfollow',
            kwargs=self.data_page_user2)
        self.client.get(unfollow_url)
        follow = Follow.objects.filter(
            user=self.user_user,
            author=self.user_user2
        ).exists()


    def test_published_post_from_following_author_on_follow_page(self):
        """Пост пользователя появился в избранных постах его подписчика."""
        follow = Follow.objects.create(
            user=self.user_user,  author=self.user_user2)
        self.assertTrue(follow)
        follow_url = reverse('follow_index')

        response = self.client.get(follow_url)
        self.assertContains(response,
                            text=self.post_user2.text,
                            status_code=200)

    def test_published_post_from_unfollowing_author_on_follow_page(self):
        """Пост пользователя появился в избранных постах тех, кто на него не подписан."""
        follow = Follow.objects.filter(
            user=self.user_user,
            author=self.user_user2
        ).exists()
        self.assertFalse(follow)
        follow_url = reverse('follow_index')
        response = self.client.get(follow_url)
        self.assertNotContains(response,
                               text=self.post_user2.text,
                               status_code=200)
