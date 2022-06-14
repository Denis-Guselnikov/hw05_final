import shutil
import tempfile
from django.core.cache import cache
from django import forms
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from ..models import Group, Post, User, Follow

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='wwork',
            slug='slug',
            description='work description',
        )

        cls.group2 = Group.objects.create(
            title='wwork2',
            slug='slug2',
            description='work description2',
        )
        cls.author_post = User.objects.create_user(username='leo')
        cls.no_author_post = User.objects.create_user(username='no_leo')

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

        posts_list = []
        for _ in range(1, 14):
            post = Post(
                author=cls.author_post,
                group=cls.group,
                text='Текст',
                image=uploaded
            )
            posts_list.append(post)
        cls.post = Post.objects.bulk_create(objs=posts_list)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author_post)
        # Авторизовываем второго клиента, не автор поста (no_leo)
        self.authorized_client_1 = Client()
        self.authorized_client_1.force_login(self.no_author_post)
        cache.clear()

    def test_about_page_uses_correct_template(self):
        """URL-адрес использует соответствующие шаблоны."""
        templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': 'slug'}):
            'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': 'leo'}):
            'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': 1}):
            'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit', kwargs={'post_id': 1}):
            'posts/create_post.html',
        }

        for reverse_name, template in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index.html сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        post_text = first_object.text
        post_image = first_object.image
        self.assertEqual(post_text, 'Текст')
        self.assertTrue(post_image, 'posts/small.gif')

    def test_profile_list_page_show_correct_context(self):
        """Шаблон profile.html сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:profile',
                                              kwargs={'username': 'leo'}))
        first_object = response.context['page_obj'][0]
        post_author = first_object.author.username
        post_text = first_object.text
        post_image = first_object.image
        self.assertEqual(post_text, 'Текст')
        self.assertEqual(post_author, 'leo')
        self.assertTrue(post_image, 'posts/small.gif')

    def test_group_list_correct_context(self):
        """Шаблон group_list.html сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:group_list',
                                              kwargs={'slug': 'slug'}))
        first_object = response.context['page_obj'][0]
        post_text = first_object.text
        post_group = first_object.group.title
        post_image = first_object.image
        self.assertEqual(post_text, 'Текст')
        self.assertEqual(post_group, 'wwork')
        self.assertTrue(post_image, 'posts/small.gif')

    def test_post_detail_correct_context(self):
        """Шаблон post_detail.html сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_detail',
                                              kwargs={'post_id': 1}))
        first_object = response.context['post_id']
        post_author = first_object.author
        post_text = first_object.text
        group_title = first_object.group.title
        post_image = first_object.image
        self.assertEqual(post_author, self.author_post)
        self.assertEqual(post_text, 'Текст')
        self.assertEqual(group_title, self.group.title)
        self.assertTrue(post_image, 'posts/small.gif')

    def test_index_containse_ten_records(self):
        """Количество постов на первой странице равно 10"""
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(len(response.context.get('page_obj').object_list),
                         settings.NUM_POSTS)

    def test_group_list_containse_ten_records(self):
        """Количество постов в группе равно 10"""
        response = self.client.get(reverse('posts:group_list',
                                   kwargs={'slug': 'slug'}))
        self.assertEqual(len(response.context.get('page_obj').object_list),
                         settings.NUM_POSTS)

    def test_profile_containse_ten_records(self):
        """Количество постов в профиле равно 10"""
        response = self.client.get(reverse('posts:profile',
                                   kwargs={'username': 'leo'}))
        self.assertEqual(len(response.context.get('page_obj').object_list),
                         settings.NUM_POSTS)

    def test_second_page_containse_three_records(self):
        response = self.guest_client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context.get('page_obj').object_list), 3)

    def test_second_page_group_list_containse_three_records(self):
        response = self.guest_client.get(reverse('posts:group_list', kwargs={
            'slug': 'slug'}) + '?page=2')
        self.assertEqual(len(response.context.get('page_obj').object_list), 3)

    def test_second_page_profile_containse_three_records(self):
        response = self.guest_client.get(reverse('posts:profile', kwargs={
            'username': 'leo'}) + '?page=2')
        self.assertEqual(len(response.context.get('page_obj').object_list), 3)
        self.assertTrue(response.context.get('title'))

    def test_context_in_post_edit(self):
        """Проверка /<username>/<post_id>/edit/"""
        response = self.authorized_client.get(reverse('posts:post_edit',
                                              kwargs={'post_id': 1}))
        form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField,
        }
        is_edit = True
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_fields = response.context['form'].fields[value]
                self.assertIsInstance(form_fields, expected)
        self.assertEqual(response.context['is_edit'], is_edit)

    def test_new_post_correct_context(self):
        """Форма добавления нового поста с правильным контекстом"""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_fields = response.context['form'].fields[value]
                self.assertIsInstance(form_fields, expected)

    def test_new_post_if_is_valid_form_show_in_pages(self):
        """Проверяем, что пост с группой попадает на страницы."""
        group_post_pages = {
            reverse('posts:index'): 10,
            reverse('posts:group_list', kwargs={'slug': 'slug'}): 10,
            reverse('posts:profile', kwargs={'username': 'leo'}): 10,
        }
        for value, expected in group_post_pages.items():
            with self.subTest(value=value):
                response = self.authorized_client.get(value)
                self.assertEqual(len(response.context["page_obj"]), expected)

    def test_new_group_page_dont_have_a_post(self):
        """Проверяем что на странице другой группы нет постов."""
        url = reverse('posts:group_list', args=['slug2'])
        response = self.authorized_client.get(url)
        self.assertEqual(len(response.context["page_obj"]), 0)

    def test_comment_post_from_guest(self):
        """Проверка невозможности комментирования гостем"""
        form_data = {'text': 'Тестовый комментарий'}
        response = self.guest_client.post(reverse('posts:add_comment',
                                                  kwargs={'post_id': 1}),
                                          data=form_data,
                                          follow=True)
        self.assertRedirects(response, (
            '/auth/login/?next=/posts/1/comment/'))

    def test_comment_create(self):
        """Проверка добавления комментария"""
        form_data = {'text': 'Тестовый комментарий'}
        self.authorized_client.post(reverse('posts:add_comment',
                                            kwargs={'post_id': 1}),
                                    data=form_data, follow=True)
        response = self.guest_client.get(reverse('posts:post_detail',
                                                 kwargs={'post_id': 1}))
        object = response.context['comments'][0].text
        self.assertEqual(object, 'Тестовый комментарий')


class CacheTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='wwork',
            slug='slug',
            description='work description',
        )

        cls.author_post = User.objects.create_user(username='leo')

        cls.post = Post.objects.create(
            author=cls.author_post,
            group=cls.group,
            text='Текст',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author_post)

    def test_cache_index(self):
        """Тест кэширования страницы index.html"""
        first = self.guest_client.get(reverse('posts:index'))
        post = Post.objects.get(pk=1)
        post.text = 'Другой текст'
        post.save()
        second = self.guest_client.get(reverse('posts:index'))
        self.assertEqual(first.content, second.content)
        cache.clear()
        third = self.guest_client.get(reverse('posts:index'))
        self.assertNotEqual(first.content, third.content)


class FollowTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user_1 = User.objects.create_user(username='follower')
        cls.author_post = User.objects.create_user(username='following')

        cls.group = Group.objects.create(
            title='wwork',
            slug='slug',
            description='work description',
        )

        cls.post = Post.objects.create(
            author=cls.author_post,
            group=cls.group,
            text='Текст для проверки',
        )

    def setUp(self):
        self.guest_client = Client()
        # Первый клиент, кто будет подписоваться (follower)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_1)
        # Второй клиент, автор постов (following)
        self.authorized_client_1 = Client()
        self.authorized_client_1.force_login(self.author_post)

    def test_follow(self):
        """Авторизовываный пользователь подписывается"""
        self.authorized_client.get(reverse('posts:profile_follow',
                                           kwargs={'username': 'following'}))
        self.assertEqual(Follow.objects.all().count(), 1)

    def test_unfollow(self):
        """Авторизовываный пользователь отменяет подписку"""
        self.authorized_client.get(reverse('posts:profile_follow',
                                           kwargs={'username': 'following'}))
        self.authorized_client.get(reverse('posts:profile_unfollow',
                                           kwargs={'username': 'following'}))
        self.assertEqual(Follow.objects.all().count(), 0)

    def test_subscription_feed(self):
        """Запись появляется в ленте Избранные Авторы"""
        Follow.objects.create(user=self.user_1, author=self.author_post)
        response = self.authorized_client.get('/follow/')
        post_text = response.context["page_obj"][0]
        self.assertTrue(post_text, 'Текст для проверки')
        response = self.authorized_client_1.get('/follow/')
        self.assertNotContains(response, 'Текст для проверки')
