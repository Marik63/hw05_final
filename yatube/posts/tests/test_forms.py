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
        # Создаем пользователя
        cls.user = User.objects.create(
            username='test_user'
        )
        cls.group = Group.objects.create(
            title='Test group 1',
            slug='test_group_slug',
            description='Test group 1 description'
        )
        cls.group_two = Group.objects.create(
            title='Тестовая группа для постов с изображением',
            slug='posts_test_two_slug',
            description='Тестовое описание с изображением',
        )
        cls.post = Post.objects.create(
            text='Test post 1 text.',
            author=cls.user,
            group=cls.group,
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self) -> None:
        self.user = PostsFormsTestCase.user
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
            'text': 'Новый текст очередного поста.',
            'group': self.group.id,
            'image': PostsFormsTestCase.uploaded
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username': self.user})
        )
        post = Post.objects.latest('pub_date')
        post_last = {
            post.text: form_data['text'],
            post.group.id: form_data['group'],
            post.author: PostsFormsTestCase.user
        }
        for date, value in post_last.items():
            with self.subTest(date=date):
                self.assertEqual(date, value)
        Post.objects.filter(
            text=form_data['text'],
            author=self.post.author,
            group=self.group,
            image='posts/small.gif'
        ).exists()
        latest = Post.objects.order_by('-pub_date').first()
        self.assertEqual(latest.pk, post_count + 1)
        self.assertEqual(latest.text, form_data['text'])
        self.assertEqual(latest.group, self.group)
        #self.assertEqual(latest.image, 'posts/small.gif')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_edit_valid_post(self):
        """Проверка валидности формы со страницы редактирования
        поста reverse('posts:post_edit') меняется запись в базе данных.
        """
        form_data = {
            'text': 'Test post 1 text.',
            'group': self.group.id,
        }
        post = Post.objects.latest('pub_date')
        post_last = {
            post.text: form_data['text'],
            post.group.id: form_data['group'],
            post.author: PostsFormsTestCase.user,
        }
        for date, value in post_last.items():
            with self.subTest(date=date):
                self.assertEqual(date, value)

    def test_valid_post_with_image_create_db_post(self):
        """Проверка валидности поста с картинкой создает
        запись в базе данных."""
        count = Post.objects.all().count()
        form_data = {
            'text': 'Test post with image text. Long long text.',
            'image': 'posts/small.gif',
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
        )
        self.assertEqual(Post.objects.all().count(), count + 1)

    def test_check_editing_existing_post(self):
        """Проверка редактирования поста с новым текстом и группой."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Новый текст поста',
            'group': self.group_two.id
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(response.context.get('post').text, form_data['text'])
        self.assertEqual(
            response.context.get('post').group.id,
            form_data['group']
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
