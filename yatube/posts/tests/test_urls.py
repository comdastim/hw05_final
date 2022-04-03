from http import HTTPStatus

from django.test import Client, TestCase

from posts.models import Group, Post, User


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='HasNoName')
        cls.author = User.objects.create_user(username='HasNoName_2')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='1234'
        )
        cls.post = Post.objects.create(
            author=cls.author,
            group=cls.group,
            text='Тестовый текст',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_author_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_author_client.force_login(self.author)

    def test_public_urls(self):
        """Проверка доступности адресов для guest client"""
        urls_list = {'/': HTTPStatus.OK,
                     f'/group/{self.group.slug}/': HTTPStatus.OK,
                     f'/profile/{self.author.username}/': HTTPStatus.OK,
                     f'/posts/{self.post.pk}/': HTTPStatus.OK,
                     '/unexisting_page/': HTTPStatus.NOT_FOUND, }
        for adress, status in urls_list.items():
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                self.assertEqual(response.status_code, status)

    def test_urls_authorized(self):
        """Проверка доступности адресов для авторизованных"""
        urls_list = {'/': HTTPStatus.OK,
                     f'/group/{self.group.slug}/': HTTPStatus.OK,
                     f'/profile/{self.author.username}/': HTTPStatus.OK,
                     f'/posts/{self.post.pk}/': HTTPStatus.OK,
                     '/unexisting_page/': HTTPStatus.NOT_FOUND,
                     '/create/': HTTPStatus.OK, }
        for adress, status in urls_list.items():
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertEqual(response.status_code, status)

    def test_post_edit_url_exists_at_desired_location(self):
        """Страница /edit/ доступна автору поста.
         """
        response = self.authorized_author_client.get(
            f'/posts/{self.post.pk}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

# Проверка редиректов

    def test_create_url_redirect_guest_on_login(self):
        """Страница /create/ перенаправит неавторизованного
        пользователя на страницу авторизации.
        """
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_edit_url_redirect_guest_on_login(self):
        """При попытке редактирования поста неавторизованный пользователь
        будет перенаправлен на страницу авторизации.
        """
        response = self.guest_client.get(
            f'/posts/{self.post.pk}/edit/', follow=True)
        self.assertRedirects(
            response, f'/auth/login/?next=/posts/{self.post.pk}/edit/')

    def test_edit_url_redirect_auth_not_author_on_post_page(self):
        """При попытке редактирования поста авторизованный пользователь,
         не являющийся его автором, будет перенаправлен на страницу поста.
        """
        response = self.authorized_client.get(
            f'/posts/{self.post.pk}/edit/', follow=True)
        self.assertRedirects(response, (f'/posts/{self.post.pk}/'))

    def test_add_comment_redirect_guest_on_login(self):
        """При попытке добавления комментария неавторизованный пользователь
        будет перенаправлен на страницу авторизации.
        """
        response = self.guest_client.get(
            f'/posts/{self.post.pk}/comment/', follow=True)
        self.assertRedirects(
            response, f'/auth/login/?next=/posts/{self.post.pk}/comment/')

# Проверка шаблонов

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Шаблоны по адресам
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user.username}/': 'posts/profile.html',
            f'/posts/{self.post.pk}/': 'posts/post_detail.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_correct_template_authorized_create(self):
        """Проверка использования верного шаблона для запроса
         posts/create/ авторизованного пользователя.
         """
        response = self.authorized_client.get('/create/')
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_correct_template_author_edit(self):
        """URL-адрес использует соответствующий шаблон для запросов post/edit/ автора.
        """
        response = self.authorized_author_client.get(
            f'/posts/{self.post.pk}/edit/')
        self.assertTemplateUsed(response, 'posts/create_post.html')
