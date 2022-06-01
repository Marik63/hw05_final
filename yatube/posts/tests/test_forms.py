from http import HTTPStatus
import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Group, Post

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsFormsTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
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
        small_gif: bytes = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded2 = SimpleUploadedFile(
            name='small2.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.user = User.objects.create(
            username='test_user'
        )
        cls.group = Group.objects.create(
            title='Test group 1',
            slug='test_group_slug',
            description='Test group 1 description'
        )
        cls.group_two = Group.objects.create(
            title='Test group 2',
            slug='posts_test_two_slug',
            description='Тестовое описание с изображением',
        )
        cls.post = Post.objects.create(
            text='Test post 1 text.',
            author=cls.user,
            group=cls.group,
            image=cls.uploaded
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self) -> None:
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_create_new_post(self):
        """Проверка добавления нового поста
           в базу данных.
        """
        post_count = Post.objects.count()
        form_data = {
            'text': 'Test group 1.',
            'group': self.group.id,
            'image': self.uploaded2
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username': self.user})
        )
        self.assertEqual(Post.objects.count(), post_count + 1)
        latest = Post.objects.order_by('-pub_date').first()
        self.assertEqual(latest.pk, post_count + 1)
        self.assertEqual(latest.text, form_data['text'])
        self.assertEqual(latest.group, self.group)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(latest.image.name, 'posts/small2.gif')

    def test_edit_valid_post(self):
        """Проверка редактирования поста с новым текстом и группой."""
        form_data = {
            'text': 'Test post 1 text.',
            'group': self.group_two.id,
            'image': self.uploaded2
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', args=[self.post.id]),
            data=form_data,
            follow=True
        )
        latest = Post.objects.get(post=self.post.id)
        self.assertEqual(latest.text, form_data['text'])
        self.assertEqual(latest.group, self.group)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(latest.image.name, 'posts/small.gif')
        self.assertEqual(response.status_code, HTTPStatus.OK)
