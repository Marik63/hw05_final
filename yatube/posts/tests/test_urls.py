import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings, tag
from django.urls import reverse
from posts.models import Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TaskURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.user = User.objects.create_user(username='posts_test')
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
        cls.group_image = Group.objects.create(
            title='Тестовая группа для постов с изображением',
            slug='posts_test_image_slug',
            description='Тестовое описание с изображением',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост для проверки',
        )
        cls.post_image = Post.objects.create(
            author=cls.user,
            text='Тестовый пост с изображением для проверки',
            image=cls.uploaded,
        )
        cls.group_post = Post.objects.create(
            author=cls.user,
            text='Групповой тестовый пост для проверки',
            group=cls.group,
        )
        cls.group_post_image = Post.objects.create(
            author=cls.user,
            text='Групповой тестовый пост с изображением для проверки',
            group=cls.group_image,
            image=cls.uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем авторизованый клиент
        #self.user = TaskURLTests.user
        # Создаем второй клиент
        self.authorized_client = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(self.user)

    def test_guest_templates(self):
        """Тестируем шаблоны общедоступных страниц."""
        url_templates = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user.username}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
        }
        for url, expected_template in url_templates.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, expected_template)

    def test_authorized_pages(self):
        """Тестируем доступность страниц авторизованными пользователями и
        доступность страниц автором."""
        post = TaskURLTests.post
        urls = {
            '/create/': HTTPStatus.OK,
            f'/posts/{self.post.id}/edit/': HTTPStatus.OK,
        }
        for field, expected_value in urls.items():
            with self.subTest(field=field):
                response = self.authorized_client.get(field)
                self.assertEqual(response.status_code, expected_value)

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

    def test_guest_view_pages(self):
        """Тестируем доступность страниц неавторизованными пользователями."""
        post = TaskURLTests.post
        urls = {
            '/': HTTPStatus.OK,
            '/group/test_slug/': HTTPStatus.OK,
            '/profile/posts_test/': HTTPStatus.OK,
            f'/posts/{post.id}/': HTTPStatus.OK,
            '/unexisting_page/': HTTPStatus.NOT_FOUND,
        }
        for field, expected_value in urls.items():
            with self.subTest(field=field):
                response = self.guest_client.get(field)
                self.assertEqual(response.status_code, expected_value)

    @tag('sprint6')
    def test_page_have_a_post_with_image(self):
        """Проверяем context содержит изображение."""
        url = reverse('posts:group_list', args=['posts_test_image_slug'])
        response = self.authorized_client.get(url)
        print(response.context.get("page_obj")[0].text)
        self.assertNotEqual(len(response.context.get("page_obj")[0].image), 0)

    @tag('sprint6')
    def test_detail_page_have_a_post_with_image(self):
        """Проверяем что detail в context содержит изображение."""
        post = TaskURLTests.post_image
        url = reverse('posts:post_detail', args=[post.id])
        response = self.authorized_client.get(url)
        self.assertNotEqual(len(response.context.get("post").image), 0)

    @tag('sprint6')
    def test_index_page_have_a_post_with_image(self):
        """Проверяем что index в context содержит изображение."""
        url = reverse('posts:index')
        response = self.authorized_client.get(url)
        for cont in response.context.get("page_obj"):
            with self.subTest(cont=cont):
                if cont.image:
                    self.assertNotEqual(len(cont.image), 0)
                else:
                    self.assertRaisesMessage(
                        ValueError, "The 'image' attribute has no file "
                                    "associated with it.")

    @tag('sprint6')
    def test_profile_page_have_a_post_with_image(self):
        """Проверяем что index в context содержит изображение."""
        url = reverse('posts:profile', args=['posts_test'])
        response = self.authorized_client.get(url)
        for cont in response.context.get("page_obj"):
            with self.subTest(cont=cont):
                if cont.image:
                    self.assertNotEqual(len(cont.image), 0)
                else:
                    self.assertRaisesMessage(
                        ValueError, "The 'image' attribute has no file "
                                    "associated with it.")
