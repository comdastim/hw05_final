import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Follow, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='HasNoName')
        cls.author = User.objects.create_user(username='HasNoName_2')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='1234'
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
            author=cls.author,
            group=cls.group,
            text='Тестовый текст',
            image=cls.uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_author_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_author_client.force_login(self.author)

    def test_page_uses_correct_template(self):
        """URL-адрес использует верный шаблон."""
        templates_pages_names = {
            reverse('posts:index_posts'): 'posts/index.html',
            reverse('posts:follow_index'): 'posts/follow.html',
            reverse('posts:group',
                    kwargs={'slug': self.group.slug}): 'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={
                        'username': self.user.username}): 'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={
                        'post_id': self.post.pk}): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit',
                    kwargs={'post_id': self.post.pk}): 'posts/create_post.html'
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_author_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_page_shows_correct_context(self):
        """На страницах отображаются верные значения context."""
        url_names_for_index_group_profile = [
            reverse('posts:index_posts'),
            reverse('posts:group',
                    kwargs={'slug': self.group.slug}),
            reverse('posts:profile',
                    kwargs={'username': self.author.username}),
        ]
        for url in url_names_for_index_group_profile:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                first_object = response.context['page_obj'][0]
                fields_to_test = {
                    first_object.text: self.post.text,
                    first_object.author.username: self.author.username,
                    first_object.group.title: self.group.title,
                    first_object.image: self.post.image,
                }
            for field, expected in fields_to_test.items():
                with self.subTest(field=field):
                    self.assertEqual(field, expected)

    def test_post_detail_page_shows_correct_context(self):
        """Шаблон post detail содержит верные значения context."""
        response = self.authorized_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post.pk}))
        object = response.context['post']
        fields_to_test = {
            object.text: self.post.text,
            object.author.username: self.author.username,
            object.group.title: self.group.title,
            object.image: self.post.image,
        }
        for field, expected in fields_to_test.items():
            with self.subTest(field=field):
                self.assertEqual(field, expected)

    def test_post_create_show_correct_context(self):
        """Проверка контекста шаблона post create при создании поста"""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_show_correct_context(self):
        """Проверка контекста шаблона post edit при редактировании поста"""
        response = self.authorized_author_client.get(
            reverse('posts:post_edit',
                    kwargs={'post_id': self.post.pk}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_with_group_is_on_pages(self):
        """Проверка страниц на содержание поста с выбранной группой"""
        urls = [
            reverse('posts:index_posts'),
            reverse('posts:group',
                    kwargs={'slug': self.group.slug}),
            reverse('posts:profile',
                    kwargs={'username': self.author.username}),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.authorized_author_client.get(url)
                self.assertTrue(
                    self.post in response.context['page_obj'].object_list)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='1234'
        )
        cls.author = User.objects.create_user(username='HasNoName_2')
        for i in range(13):
            cls.post = Post.objects.create(
                author=cls.author,
                group=cls.group,
                text='Тестовый текст' + str(i),
            )

    def setUp(self):
        self.guest_client = Client()

    def test_first_page_contains_ten_records(self):
        """
        Проверка: количество постов на первой странице равно 10.
        """
        url_names_for_paginator = [
            reverse('posts:index_posts'),
            reverse('posts:group',
                    kwargs={'slug': self.group.slug}),
            reverse('posts:profile',
                    kwargs={'username': self.author.username}),
        ]
        for url in url_names_for_paginator:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_three_records(self):
        """
        Проверка: количество постов на второй странице равно 3.
        """
        url_names_for_paginator = [
            reverse('posts:index_posts'),
            reverse('posts:group',
                    kwargs={'slug': self.group.slug}),
            reverse('posts:profile',
                    kwargs={'username': self.author.username}),
        ]
        for url in url_names_for_paginator:
            with self.subTest(url=url):
                response = self.guest_client.get(url + '?page=2')
                self.assertEqual(len(response.context['page_obj']), 3)

class ErrorViewsTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_error_page(self):
        response = self.guest_client.get('nonexist-page')
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, 'core/404.html')               


class FollowViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='Автор')
        cls.user = User.objects.create_user(username='Подписчик_на_автора')
        cls.author_2 = User.objects.create_user(username='Автор_2')
        cls.user_2 = User.objects.create_user(username='Подписчик_на_автора_2')
        cls.follow = Follow.objects.create(
            author=cls.author,
            user=cls.user
        )
        cls.follow_2 = Follow.objects.create(
            author=cls.author_2,
            user=cls.user_2
        )
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='1234'
        )
        cls.post = Post.objects.create(
            author=cls.author,
            group=cls.group,
            text='Тестовый текст от автора',
        )
        cls.post_2 = Post.objects.create(
            author=cls.author,
            group=cls.group,
            text='Еще один текст от автора',
        )
        cls.another_post = Post.objects.create(
            author=cls.author_2,
            group=cls.group,
            text='Текст поста автора_2',
        )

    def setUp(self):
        self.authorized_author_client = Client()
        self.authorized_author_client_2 = Client()
        self.follower = Client()
        self.not_follower = Client()
        self.authorized_author_client.force_login(self.author)
        self.follower.force_login(self.user)
        self.not_follower.force_login(self.user_2)
        self.authorized_author_client_2.force_login(self.author_2)

    def test_create_follow(self):
        """Проверяем, может ли подписаться авторизованный пользователь,
        не подписанный на автора.
        """
        follow_count = Follow.objects.count()
        response = self.not_follower.post(
            reverse('posts:profile_follow', kwargs={'username': self.author})
        )
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': self.author})
        )
        self.assertEqual(Follow.objects.count(), follow_count + 1)
        self.assertTrue(
            Follow.objects.filter(
                user=self.user_2,
                author=self.author
            ).exists()
        )

    def test_delete_follow(self):
        """Проверяем, может ли подписчик отменить подписку"""
        follow_count = Follow.objects.count()
        response = self.follower.post(
            reverse('posts:profile_unfollow', kwargs={'username': self.author})
        )
        self.assertRedirects(response, reverse(
            'posts:profile',
            kwargs={'username': self.author})
        )
        self.assertEqual(Follow.objects.count(), follow_count - 1)
        self.assertFalse(
            Follow.objects.filter(
                user=self.user,
                author=self.author
            ).exists()
        )

    def test_follower_see_author_posts(self):
        """Проверяем, отображаются ли посты автора у подписчика."""
        response = self.follower.get(reverse('posts:follow_index'))
        first_object = response.context['page_obj'][0]
        second_object = response.context['page_obj'][1]
        self.assertEqual(first_object.text, self.post.text)
        self.assertEqual(second_object.text, self.post_2.text)

    def test_not_follower_see_author_posts(self):
        """Проверяем, что у подписчика автора_2, не подписанного на автора,
         отображается у пост автора_2 и не отображаются посты автора.
         """
        response = self.not_follower.get(reverse('posts:follow_index'))
        first_object = response.context['page_obj'][0]
        self.assertNotEqual(first_object.text, self.post.text)
        self.assertEqual(first_object.text, self.another_post.text)
