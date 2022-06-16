from django.test import TestCase
from ..models import Group, Post, User, Comment


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая пост',
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Текст комментария',
            created='Дата публикации',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        post = self.post
        group = self.group
        comment = self.comment
        field_verboses = {
            post.text[:15]: str(post),
            group.title: str(group),
            comment.text: str(comment),
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(value, expected)

    def test_group_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        task = PostModelTest.group
        field_verboses = {
            'title': 'Заголовок',
            'slug': 'Слаг поста',
            'description': 'Описание',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    task._meta.get_field(field).verbose_name, expected_value)

    def test_post_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        task = PostModelTest.post
        field_verboses = {
            'text': 'Текст постов',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    task._meta.get_field(field).verbose_name, expected_value)

    def test_comment_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        task = PostModelTest.comment
        field_verboses = {
            'post': 'Пост комментария',
            'author': 'Автор комментария',
            'text': 'Текст комментария',
            'created': 'Дата публикации',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    task._meta.get_field(field).verbose_name, expected_value)
