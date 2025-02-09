from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from notes.models import Note

User = get_user_model()


class TestRoutes(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Создаём двух пользователей с разными именами:
        cls.author = User.objects.create(username='Автор')
        cls.reader = User.objects.create(username='Не автор')
        # От имени одного пользователя создаём новость
        cls.news = Note.objects.create(
            author=cls.author,
            title='Заголовок',
            text='Текст статьи',
            slug='slugname'
        )

    def test_pages_availability(self):
        """Проверяем доступы до страниц без авторизации"""
        urls = (
            ('notes:home', None),
            ('users:login', None),
            ('users:logout', None),
            ('users:signup', None),
        )
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_author_pages_availability(self):
        """Проверяем, что автору доступны страницы notes, done, add"""
        self.client.force_login(self.author)
        URLS = ('notes:add',
                'notes:list',
                'notes:success',
                )
        for name in URLS:
            with self.subTest(name=name):
                url = reverse(name)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_availability_for_news_edit_and_delete_and_details(self):
        """
        Проверяем доступы до страниц с авторизацией.
        Проверяем  доступны до страниц только авторами.
        """
        users_statuses = (
            (self.author, HTTPStatus.OK),
            (self.reader, HTTPStatus.NOT_FOUND),
        )
        for user, status in users_statuses:
            # Логиним пользователя в клиенте:
            self.client.force_login(user)
            # Для каждой пары "пользователь - ожидаемый ответ"
            # перебираем имена тестируемых страниц:
            URLS = (('notes:edit', (self.news.slug,)),
                    ('notes:delete', (self.news.slug,)),
                    ('notes:detail', (self.news.slug,)),
                    )
            for name, args in URLS:
                with self.subTest(user=user, name=name):
                    url = reverse(name, args=args)
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, status)

    def test_redirect_for_anonymous_client(self):
        """Проверяем переадресацию на авторизацию"""
        # Сохраняем адрес страницы логина:
        login_url = reverse('users:login')
        # В цикле перебираем имена страниц, с которых ожидаем редирект:
        URLS = (('notes:edit', (self.news.slug,)),
                ('notes:delete', (self.news.slug,)),
                ('notes:detail', (self.news.slug,)),
                ('notes:add', None),
                ('notes:list', None),
                ('notes:success', None))
        for name, args in URLS:
            with self.subTest(name=name):
                # Получаем адрес страницы редактирования или удаления
                url = reverse(name, args=args)
                redirect_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                # Проверяем, что редирект приведёт именно на указанную ссылку.
                self.assertRedirects(response, redirect_url)
