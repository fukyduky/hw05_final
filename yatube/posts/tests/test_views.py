from django import forms
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Group, Post, Follow
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

User = get_user_model()


class PostViewsTests(TestCase):
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
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.author = User.objects.create_user(username='test_author')
        cls.group = Group.objects.create(
            title='Заголовок',
            description='Описание',
            slug='test_slug'
        )
        cls.post = Post.objects.create(
            text='Тестовая запись',
            author=cls.author,
            group=cls.group,
            image=uploaded
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='test_user')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_pages_uses_correct_template(self):
        """view-функция использует соответствующий шаблон."""
        templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_posts', kwargs={'slug': 'test_slug'}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile', kwargs={'username': self.user.username}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail', kwargs={'post_id': self.post.id}
            ): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:post_edit', kwargs={'post_id': self.post.id}
            ): 'posts/create_post.html',
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.text, 'Тестовая запись')
        self.assertEqual(first_object.author.username, 'test_author')
        self.assertEqual(first_object.group.title, 'Заголовок')
        self.assertTrue(
            Post.objects.filter(
                text='Тестовая запись',
                image__isnull=False,
                group=self.group.id,
            ).exists())

    def test_group_posts_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_posts', kwargs={'slug': 'test_slug'}))
        first_object = response.context['group']
        self.assertEqual(first_object.slug, 'test_slug')
        self.assertEqual(first_object.title, 'Заголовок')
        self.assertTrue(
            Post.objects.filter(
                text='Тестовая запись',
                image__isnull=False,
                group=self.group.id,
            ).exists())

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': 'test_author'}))
        first_object = response.context['page_obj'][0]
        self.assertEqual(response.context['author'].username, 'test_author')
        self.assertEqual(first_object.text, 'Тестовая запись')
        self.assertTrue(
            Post.objects.filter(
                text='Тестовая запись',
                image__isnull=False,
                group=self.group.id,
            ).exists())

    def test_post_detail_show_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}))
        self.assertEqual(
            response.context['post_list'].author.username, 'test_author')
        self.assertEqual(
            response.context['post_list'].text, 'Тестовая запись')
        self.assertEqual(
            response.context['post_list'].group.title, 'Заголовок')
        self.assertTrue(
            Post.objects.filter(
                text='Тестовая запись',
                image__isnull=False,
                group=self.group.id,
            ).exists())

    def test_post_edit_page_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_create_post_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_on_all_the_right_pages(self):
        """Пост попадает на все страницы"""
        response_1 = self.authorized_client.get(
            reverse('posts:index'))
        response_2 = self.authorized_client.get(
            reverse('posts:group_posts', kwargs={'slug': 'test_slug'}))
        response_3 = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': 'test_author'}))
        first_object_1 = response_1.context['page_obj'][0]
        first_object_2 = response_2.context['page_obj'][0]
        first_object_3 = response_3.context['page_obj'][0]
        self.assertEqual(first_object_1.text, 'Тестовая запись')
        self.assertEqual(first_object_2.text, 'Тестовая запись')
        self.assertEqual(first_object_3.text, 'Тестовая запись')


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test_author')
        cls.group = Group.objects.create(
            title=('Заголовок'),
            slug='test_slug',
            description='Описание')
        cls.posts = []
        for i in range(13):
            cls.posts.append(Post(
                text=f'Тестовая запись {i}',
                author=cls.author,
                group=cls.group
            )
            )
        Post.objects.bulk_create(cls.posts)  # django-bulk-create-function(SO)

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='test_user')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_first_page_contains_ten_posts(self):
        urls_dict = {
            reverse('posts:index'): 'index',
            reverse('posts:group_posts', kwargs={
                'slug': 'test_slug'}): 'group',
            reverse('posts:profile', kwargs={
                'username': 'test_author'}): 'profile',
        }
        for url in urls_dict.keys():
            response = self.client.get(url)
            self.assertEqual(
                len(response.context.get('page_obj').object_list), 10)

    def test_second_page_contains_three_posts(self):
        urls_dict = {
            reverse('posts:index') + '?page=2': 'index',
            reverse('posts:group_posts', kwargs={
                'slug': 'test_slug'}) + '?page=2': 'group',
            reverse('posts:profile', kwargs={
                'username': 'test_author'}) + '?page=2': 'profile',
        }
        for url in urls_dict.keys():
            response = self.client.get(url)
            self.assertEqual(
                len(response.context.get('page_obj').object_list), 3)


class CacheViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post = Post.objects.create(
            author=User.objects.create_user(username='test_author'),
            text='Тестовая запись')

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='test_user')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_cache_index(self):
        """Тест кэширования страницы index.html"""
        initial_state = self.authorized_client.get(reverse('posts:index'))
        post = Post.objects.get(pk=1)
        post.text = 'Измененная тестовая запись'
        post.save()
        changed_state = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(initial_state.content, changed_state.content)
        cache.clear()
        changed_state_2 = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(initial_state.content, changed_state_2.content)


class FollowViewsTests(TestCase):
    def setUp(self):
        self.client_auth_follower = Client()
        self.client_auth_followed = Client()
        self.user_follower = User.objects.create_user(
            username='test_follower'
        )
        self.user_followed = User.objects.create_user(
            username='test_following'
        )
        self.post = Post.objects.create(
            author=self.user_followed,
            text='Тестовая запись'
        )
        self.client_auth_follower.force_login(self.user_follower)
        self.client_auth_followed.force_login(self.user_followed)

    def test_follow(self):
        """Авт. пользователь может подписаться на других пользователей"""
        self.client_auth_follower.get(reverse('posts:profile_follow',
                                              kwargs={'username':
                                                      self.user_followed.
                                                      username}))
        self.assertEqual(Follow.objects.all().count(), 1)

    def test_unfollow(self):
        """Авт. пользователь может отписаться от других пользователей"""
        self.client_auth_follower.get(reverse('posts:profile_follow',
                                              kwargs={'username':
                                                      self.user_followed.
                                                      username}))
        self.client_auth_follower.get(reverse('posts:profile_unfollow',
                                      kwargs={'username':
                                              self.user_followed.username}))
        self.assertEqual(Follow.objects.all().count(), 0)

    def test_follow_feed(self):
        """запись появится в подписках"""
        Follow.objects.create(user=self.user_follower,
                              author=self.user_followed)
        response = self.client_auth_follower.get(
            reverse('posts:follow_index')
        )
        post_text_0 = response.context['page_obj'][0]
        self.assertEqual(post_text_0.text, 'Тестовая запись')
        response = self.client_auth_followed.get(
            reverse('posts:follow_index')
        )
        self.assertNotContains(response, 'Тестовая запись')
