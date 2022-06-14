from django.test import TestCase, Client
from ..models import Group, Post, User
from django.urls import reverse
from http import HTTPStatus


class URLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='wwork',
            slug='slug',
            description='work description',
        )
        # Создание двух пользователей
        cls.author_post = User.objects.create_user(username='leo')
        cls.no_author_post = User.objects.create_user(username='no_leo')

        # Создание тестового поста
        cls.post = Post.objects.create(
            author=cls.author_post,
            group=cls.group,
            text='Текст',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author_post)
        # Авторизовываем второго клиента, не автор поста (no_leo)
        self.authorized_client_1 = Client()
        self.authorized_client_1.force_login(self.no_author_post)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '': 'posts/index.html',
            '/posts/1/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
            '/posts/1/': 'posts/post_detail.html',
            '/group/slug/': 'posts/group_list.html',
            '/profile/leo/': 'posts/profile.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_create_url(self):
        """Страница /create/ доступна авторизованному пользователю."""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_unknown_page(self):
        """Страница не существует."""
        response = self.guest_client.get('/list/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_no_authorized_client_status_code(self):
        """Страницы не доступные для не авторизованного пользователя"""
        pages_urls_status = {
            '/create/': HTTPStatus.NOT_FOUND,
            '/password_reset/': HTTPStatus.NOT_FOUND,
        }
        for urls, status_code in pages_urls_status.items():
            with self.subTest(urls=urls):
                response = self.guest_client.get(urls)
                self.assertTrue(response, status_code)

    def test_post_edit_url_redirect_no_authorized(self):
        """
        Проверка редиректа анонимного пользователя, при обращении
        к странице редактирования чужого поста
        """
        url = reverse('posts:post_edit', kwargs={'post_id': 1})
        response = self.guest_client.get(url, follow=True)
        self.assertRedirects(response, '/auth/login/?next=' + url)

    def test_redirect_authorized_client_1_edit_post(self):
        """
        Проверка редиректа пользователя, при обращении
        к странице редактирования чужого поста
        """
        url = reverse('posts:post_edit', kwargs={'post_id': 1})
        response = self.authorized_client_1.get(url, follow=True)
        self.assertRedirects(response, '/posts/1/')
