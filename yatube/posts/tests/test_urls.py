import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
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
        cls.group_image = Group.objects.create(
            title='Тестовая группа для постов с изображением',
            slug='posts_test_image_slug',
            description='Тестовое описание с изображением',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост для проверки',
        )
        cls.post_with_picture = Post.objects.create(
            author=cls.user,
            text='Тестовый пост с изображением для проверки',
            image=cls.uploaded,
        )
        cls.group_post = Post.objects.create(
            author=cls.user,
            text='Групповой тестовый пост для проверки',
            group=cls.group,
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

    def test_pictures_on_pages_list_posts(self):
        """Проверка вывода картинки на главную страницу."""
        reverse_context = {
            reverse('post:index'): Post.objects.all()[:10],
            reverse('post:group_list', kwargs={'slug': self.test_slug.slug}):
                Group.objects.get(slug='test_slug').posts.all()[:10],
            reverse('post:profile', kwargs={'username': self.author.username}):
                User.objects.get(username='posts_test').posts.all()[:10]
        }
        for adress, passed_posts in reverse_context.items():
            with self.subTest(adress=adress):
                nums_passed_posts = passed_posts.count()
                response = self.authorized_author.get(adress)
                objs_on_page = list(response.context['page_obj'].object_list)
                self.assertEqual(nums_passed_posts, len(objs_on_page))
                for i in range(nums_passed_posts):
                    self.assertEqual(
                        passed_posts[i].image, objs_on_page[i].image)

    def test_picture_on_page_post_detail(self):
        """Проверка вывода картинки на страницу профайла."""
        passed_post = self.post_with_picture
        adress = reverse(
            'post:post_detail', kwargs={'post_id': passed_post.id})
        response = self.authorized_author.get(adress)
        self.assertEqual(passed_post.image, response.context['post'].image)
