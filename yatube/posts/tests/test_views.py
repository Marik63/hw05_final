import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from posts.forms import PostForm
from django.core.paginator import Page

from posts.models import Comment, Follow, Group, Post

User = get_user_model()


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Иван')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
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
        Post.objects.bulk_create([
            Post(
                author=cls.user,
                text=f'Тестовый текст {num}',
                group=cls.group,
                image=uploaded,
            )
            for num in range(1, 15)
        ])
        cls.post = Post.objects.first()

        cls.comment = Comment.objects.create(
            author=cls.user,
            text='Тестовый комментарий',
            post=cls.post
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем автора
        self.author_client = Client()
        self.author_client.force_login(self.user)
        # Создаем авторизованный клиент
        self.authorized_client = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(self.user)

    def test_index_uses_correct_context(self):
        """Шаблон index использует соответствующий контекст."""
        response = self.guest_client.get(reverse('posts:index'))
        page_obj = response.context.get('page_obj')
        task_img = page_obj[0].image
        self.assertIsInstance(page_obj, Page)
        self.assertIsInstance(page_obj[0], Post)
        self.assertEqual(task_img, self.post.image)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse(
            'posts:group_list', args=[self.group.slug]))
        first_object = response.context['page_obj'].object_list[0]
        group_author_0 = first_object.author.username
        group_title_0 = first_object.group.title
        group_description_0 = first_object.group.description
        self.assertEqual(
            group_author_0,
            f'{self.user.username}'
        )
        self.assertEqual(
            group_title_0,
            f'{self.group.title}'
        )
        self.assertEqual(
            group_description_0,
            f'{self.group.description}'
        )

    def test_profile_page_uses_correct_context(self):
        """Шаблон profile использует соответствующий контекст."""
        response = self.authorized_client.get(
            reverse('posts:profile', args=[self.post.author])
        )
        first_object = response.context.get('page_obj')[0]
        post_text_0 = first_object.text
        post_author_0 = first_object.author.username
        group_title_0 = first_object.group.title
        post_pic_0 = first_object.image
        self.assertEqual(
            post_text_0,
            f'{self.post.text}'
        )
        self.assertEqual(
            post_author_0,
            f'{self.user.username}'
        )
        self.assertEqual(
            group_title_0,
            f'{self.group.title}'
        )
        self.assertEqual(
            post_pic_0,
            f'{self.post.image}'
        )

    # def test_post_detail_show_correct_context(self):
    #     """Шаблон post_detail сформирован с правильным контекстом."""
    #     response = self.authorized_client.get(
    #         reverse('posts:post_detail', args=[self.post.id]))
    #     self.assertEqual(response.context['post'].author, self.post.author)

    # def test_create_edit_post_show_correct_form(self):
    #     """Шаблон create_post сформирован с правильным контекстом."""
    #     check_forms = (
    #         self.authorized_client.get(reverse('posts:post_create')),
    #         self.authorized_client.get(
    #             reverse(
    #                 'posts:post_edit',
    #                 args=[self.post.id]
    #             )
    #         )
    #     )
    #     for form in check_forms:
    #         self.assertIsInstance(form.context['form'], PostForm)

    # def test_pages_having_correct_context(self):
    #     """Проверка соответствие поста на разных страницах
    #     что они целиком соответствуют созданному посту."""
    #     check_pages = (
    #         reverse('posts:index'),
    #         reverse('posts:group_list', kwargs={'slug': self.group.slug}),
    #         reverse('posts:profile',
    #                 kwargs={'username': self.post.author.username}),
    #     )
    #     for page in check_pages:
    #         with self.subTest(page=page):
    #             response = self.authorized_client.get(page)
    #             self.assertEqual(response.context['page_obj'][0], self.post)

    # def test_pictures_on_pages_list_posts(self):
    #     reverse_context = {
    #         reverse('posts:index'):
    #             Post.objects.all()[:10],
    #         reverse('posts:group_list', args=[self.group.slug]):
    #             Group.objects.get(slug='test_slug').posts.all()[:10],
    #         reverse('posts:profile', args=[self.user.username]):
    #             User.objects.get(username='Иван').posts.all()[:10]
    #     }
    #     for adress, passed_posts in reverse_context.items():
    #         with self.subTest(adress=adress):
    #             nums_passed_posts = passed_posts.count()
    #             response = self.author_client.get(adress)
    #             objs_on_page = list(response.context['page_obj'].object_list)
    #             self.assertEqual(nums_passed_posts, len(objs_on_page))
    #             for i in range(nums_passed_posts):
    #                 self.assertEqual(
    #                     passed_posts[i].image, objs_on_page[i].image)

    # def test_cache_index(self):
    #     """Тестирование кэширования главной страницы."""
    #     def response_page():
    #         response = self.authorized_client.get(
    #             reverse('posts:index')).content.decode('UTF-8')
    #         return response
    #     cache.clear()
    #     text_cache = self.post.text
    #     self.assertIn(text_cache, response_page())
    #     Post.objects.filter(text=text_cache).delete()
    #     cache.clear()
    #     self.assertNotIn(text_cache, response_page())

    # def test_comment_view(self):
    #     """Шаблоны post_detail отображают созданный комментарий на
    #     странице поста.
    #     """
    #     response = self.authorized_client.get(
    #         reverse(
    #             'posts:post_detail',
    #             kwargs={'post_id': f'{PostsPagesTests.post.id}'}
    #         )
    #     )
    #     first_object = response.context.get('comments')[0]
    #     comment_post_0 = first_object
    #     self.assertEqual(comment_post_0, PostsPagesTests.comment)

    # def test_follow_create_subcribe_on_user(self):
    #     """Новая запись пользователя появляется в ленте
    #        тех, кто на него подписан.
    #     """
    #     user_temp = User.objects.create(username='Петр')
    #     self.authorized_client.get(
    #         reverse('posts:profile_follow', kwargs={'username': user_temp}))
    #     self.assertTrue(
    #         Follow.objects.filter(
    #             user=self.user, author=user_temp).exists())

    # def test_unfollow_destroy_subscribe_on_user(self):
    #     """Новая запись пользователя не появляется в ленте
    #        тех, кто на него не подписан.
    #     """
    #     user_temp = User.objects.create(username='Петр')
    #     Follow.objects.create(user=self.user, author=user_temp)
    #     self.authorized_client.get(reverse(
    #         'posts:profile_unfollow', kwargs={'username': user_temp}))
    #     self.assertFalse(
    #         Follow.objects.filter(
    #             user=self.user, author=user_temp).exists())

    # def test_appearance_post_on_page_with_subscribes(self):
    #     """Проверка появление нового поста любимого автора на его странице."""
    #     user_temp = User.objects.create(username='Петр')
    #     Follow.objects.create(user=self.user, author=user_temp)
    #     test_post = Post.objects.create(
    #         text="one post",
    #         author=user_temp,
    #     )
    #     response = self.authorized_client.get(reverse('posts:follow_index'))
    #     self.assertIn(
    #         test_post, list(response.context['page_obj'].object_list))
    #     # disappearance posts of athour after delete him from his favorites
    #     Follow.objects.filter(user=self.user, author=user_temp).delete()
    #     response = self.authorized_client.get(reverse('posts:follow_index'))
    #     self.assertNotIn(
    #         test_post, list(response.context['page_obj'].object_list))
