from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post, User


class CacheViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='Автор')
        cls.user = User.objects.create_user(username='Пользователь')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='1234'
        )
        cls.post = Post.objects.create(
            author=cls.author,
            group=cls.group,
            text='Тестовый текст от автора',
        )

    def setUp(self):
        self.user_client = Client()
        self.user_client.force_login(self.user)

    def test_cache_works(self):
        response = self.user_client.get(reverse('posts:index_posts'))
        before_deletion = response.content
        self.post.delete()
        second_response = self.user_client.get(reverse('posts:index_posts'))
        after_deletion = second_response.content
        self.assertEqual(before_deletion, after_deletion)
        cache.clear()
        third_response = self.user_client.get(reverse('posts:index_posts'))
        after_cache = third_response.content
        self.assertNotEqual(before_deletion, after_cache)
