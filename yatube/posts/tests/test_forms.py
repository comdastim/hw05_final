import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Comment, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Учеба',
            slug='1234',
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='Тестовый текст',
            image=cls.uploaded,
        )
        cls.comment = Comment.objects.create(
            text='Текст комментария',
            author=cls.user,
            post=cls.post,
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Проверка формы создания поста."""
        posts_count = Post.objects.count()
        form_data = {
            'text': self.post.text,
            'group': self.group.pk,
            'image': self.post.image,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'), data=form_data, follow=True)
        self.assertRedirects(response, reverse('posts:profile',
                             kwargs={'username': self.user.username}))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                group=self.group.pk,
                text=self.post.text,
                image=self.post.image
            ).exists()
        )

    def test_guest_create_post(self):
        """Проверка формы создания поста анонимом."""
        posts_count = Post.objects.count()
        form_data = {
            'text': self.post.text,
            'group': self.group.pk,
            'image': self.post.image,
        }
        response = self.guest_client.post(
            reverse('posts:post_create'), data=form_data, follow=True)
        self.assertRedirects(response, '/auth/login/?next=/create/')
        self.assertEqual(Post.objects.count(), posts_count)

    def test_edit_post(self):
        """Проверка формы редактирования поста"""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'тестовый измененный текст',
            'group': self.group.pk,
        }
        response = self.authorized_client.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.id}), data=form_data, follow=True)
        self.assertRedirects(response, reverse('posts:post_detail',
                             kwargs={'post_id': self.post.id}))
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(
            Post.objects.filter(
                group=self.group.pk,
                text='тестовый измененный текст',
            ).exists()
        )

    def test_create_comment(self):
        """Проверка формы создания комментария."""
        comments_count = Comment.objects.count()
        form_data = {
            'text': self.comment.text,
            'author': self.comment.author,
            'post': self.comment.post,
        }
        response = self.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': self.post.id}), data=form_data, follow=True)
        self.assertRedirects(response, reverse('posts:post_detail',
                             kwargs={'post_id': self.post.id}))
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertTrue(
            Post.objects.filter(
                group=self.group.pk,
                text=self.post.text,
                image=self.post.image
            ).exists()
        )

    def test_guest_comment_post(self):
        """Проверка формы комментирования поста анонимом."""
        comments_count = Comment.objects.count()
        form_data = {
            'text': self.comment.text,
            'author': self.comment.author,
            'post': self.comment.post,
        }
        response = self.guest_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': self.post.id}), data=form_data, follow=True)
        self.assertRedirects(
            response, f'/auth/login/?next=/posts/{self.post.pk}/comment/')
        self.assertEqual(Post.objects.count(), comments_count)
