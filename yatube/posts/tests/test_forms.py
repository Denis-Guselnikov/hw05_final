from django.test import Client, TestCase, override_settings
from django.urls import reverse
from ..models import Group, Post, User
from http import HTTPStatus
from django.conf import settings
import tempfile
import shutil
from django.core.files.uploadedfile import SimpleUploadedFile

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TaskCreateForm(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.group = Group.objects.create(
            title='wwork',
            slug='work',
            description='work description',
        )

        cls.group2 = Group.objects.create(
            title='wwork2',
            slug='work2',
            description='work description2',
        )

        cls.author = User.objects.create_user(
            username='leo',
            first_name='Лев',
            last_name='Толстой',
            email='testuser@yatube.ru'
        )

        cls.post = Post.objects.create(
            author=cls.author,
            group=cls.group,
            text='Текст с картинкой',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_form_create(self):
        """Проверка создания нового поста, авторизированным пользователем"""
        post_count = Post.objects.count()
        form_data = {
            'group': TaskCreateForm.group.id,
            'text': 'Отправить текст',
        }
        response = self.authorized_client.post(reverse('posts:post_create'),
                                               data=form_data, follow=True)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, reverse('posts:profile',
                                               kwargs={'username': 'leo'}))
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(Post.objects.filter(
            text='Отправить текст',
            group=TaskCreateForm.group).exists())

    def test_form_update(self):
        """Проверка редактирования поста через форму на странице"""
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)
        form_data = {
            'group': self.group2.id,
            'text': 'Обновленный текст',
        }
        self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),
            data=form_data, follow=True)

        self.assertTrue(Post.objects.filter(
            text='Обновленный текст',
            group=TaskCreateForm.group2).exists())

    def test_form_create_img(self):
        """
        Проверка отправки нового поста с картинкой,
        авторизированным пользователем в БД.
        """
        post_count = Post.objects.count()
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
        form_data = {
            'group': TaskCreateForm.group.id,
            'text': 'Отправить текст',
            'image': uploaded,
        }
        response = self.authorized_client.post(reverse('posts:post_create'),
                                               data=form_data, follow=True)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        post = Post.objects.get(id=self.group.id)
        author = User.objects.get(username='leo')
        group = Group.objects.get(title='wwork')
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertRedirects(response, reverse('posts:profile',
                                               kwargs={'username': 'leo'}))
        self.assertEqual(post.text, 'Текст с картинкой')
        self.assertEqual(author.username, 'leo')
        self.assertEqual(group.title, 'wwork')
        self.assertTrue(Post.objects.filter(image='posts/small.gif').exists())
