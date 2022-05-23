from django.contrib.auth import get_user_model
from django.test import TestCase

from posts.models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создаём тестовую запись в БД и
        # сохраняем ее в качестве переменной класса
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Заголовок группы',
            slug='Тестовый слаг',
            description='Описание группы'
        )
        cls.post = Post.objects.create(
            text='Текст поста',
            author=cls.user,
            group=cls.group,
        )

    def test_obj_name_title_field(self):
        """Проверка вывода вводного текса до 15 символов и
            наличия поля title в модели.
            """
        task = PostModelTest.post
        expected_object_name = task.text[:15]
        self.assertEqual(expected_object_name, str(task))
        task = PostModelTest.group
        expected_object_name = task.title
        self.assertEqual(expected_object_name, str(task))

    def test_verbose_name(self):
        """verbose_name поля title совпадает с ожидаемым."""
        task = PostModelTest.group
        field_verboses = {
            'title': 'Заголовок группы',
            'description': 'Описание',
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    task._meta.get_field(value).verbose_name, expected)

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        task = PostModelTest.post
        field_verboses = {
            'text': 'Текст поста',
            'author': 'Автор',
            'group': 'Группа',
            'image': 'Картинка',
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    task._meta.get_field(value).verbose_name, expected)

        task = PostModelTest.group
        field_verboses = {
            'title': 'Заголовок группы',
            'description': 'Описание',
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    task._meta.get_field(value).verbose_name, expected)


    def test_help_text(self):
        """help_text в полях совпадает с ожидаемым."""
        task = PostModelTest.post
        field_help_texts = {
            'author': 'Выберите имя автора',
            'text': 'Введите текст поста',
            'image': 'Загрузите картинку',
        }
        for value, expected in field_help_texts.items():
            with self.subTest(value=value):
                self.assertEqual(
                    task._meta.get_field(value).help_text, expected)

        task = PostModelTest.group
        field_help_texts = {
            'title': 'Укажите заголовок группы'
        }
        for value, expected in field_help_texts.items():
            with self.subTest(value=value):
                self.assertEqual(
                    task._meta.get_field(value).help_text, expected)
