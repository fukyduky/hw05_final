from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Group, Post
from django.core.files.uploadedfile import SimpleUploadedFile

User = get_user_model()


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title=('Заголовок'),
            slug='test_slug',
            description='Тестовое описание'
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='test_author')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Создается новая запись в базе данных"""
        count_posts = Post.objects.count()
        form_data = {
            'text': 'Тестовая запись',
            'group': self.group.id
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        post_1 = Post.objects.get(id=self.group.id)
        author_1 = User.objects.get(username='test_author')
        group_1 = Group.objects.get(title='Заголовок')
        self.assertEqual(Post.objects.count(), count_posts + 1)
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': 'test_author'}))
        self.assertEqual(post_1.text, 'Тестовая запись')
        self.assertEqual(author_1.username, 'test_author')
        self.assertEqual(group_1.title, 'Заголовок')

    def test_edit_post(self):
        """При post_edit происходит изменение поста"""
        form_data = {
            'text': 'Тестовая запись',
            'group': self.group.id
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        post_2 = Post.objects.get(id=self.group.id)
        self.client.get(f'/{post_2.id}/edit/')
        form_data = {
            'text': 'Исправленная запись',
            'group': self.group.id
        }
        response_edit = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': post_2.id}),
            data=form_data,
            follow=True,
        )
        post_2 = Post.objects.get(id=self.group.id)
        self.assertEqual(response_edit.status_code, 200)
        self.assertEqual(post_2.text, 'Исправленная запись')

    def test_post_with_picture(self):
        """проверяем, что создаётся запись в базе данных"""
        count_posts = Post.objects.count()
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
            'text': 'Запись с картинкой',
            'group': self.group.id,
            'image': uploaded
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertEqual(Post.objects.count(), count_posts + 1)
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': 'test_author'}))
        self.assertTrue(
            Post.objects.filter(
                text='Запись с картинкой',
                image__isnull=False,
                group=self.group.id
            ).exists())
        # закомментирован был первый вариант теста,
        # в котором так и не получилось
        # увидеть картинку, в итоге забыл удалить коммент,
        # этот удалю в следующем пуше
