from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from notes.models import Note

User = get_user_model()


class TestRoutes(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Создаём двух пользователей с разными именами:
        cls.author = User.objects.create(username='Автор')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)

        cls.reader = User.objects.create(username='Не автор')
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)

        # От имени одного пользователя создаём новость
        cls.news = Note.objects.create(
            author=cls.author,
            title='Заголовок',
            text='Текст статьи',
            slug='slugname'
        )

        cls.home_url = reverse('notes:home')
        cls.add_url = reverse('notes:add')
        cls.list_url = reverse('notes:list')
        cls.success_url = reverse('notes:success')
        cls.edit_url = reverse(
            'notes:edit', kwargs={'slug': cls.news.slug})
        cls.delete_url = reverse(
            'notes:delete', kwargs={'slug': cls.news.slug})
        cls.detail_url = reverse(
            'notes:detail', kwargs={'slug': cls.news.slug})
        cls.login_url = reverse('users:login')
        cls.logout_url = reverse('users:logout')
        cls.signup_url = reverse('users:signup')

    def test_pages_availability(self):
        """
        Главная страница доступна анонимному пользователю.
        Страницы регистрации пользователей, входа в учётную
        запись и выхода из неё доступны всем пользователям
        """
        urls = (
            self.home_url,
            self.login_url,
            self.logout_url,
            self.signup_url,
        )
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_reader_pages_availability(self):
        """
        Аутентифицированному пользователю доступна страница со списком
        заметок notes/, страница успешного добавления заметки done/,
        страница добавления новой заметки add/
        """
        urls = (
            self.add_url,
            self.list_url,
            self.success_url
        )
        for url in urls:
            with self.subTest(url=url):
                response = self.reader_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_availability_for_news_edit_and_delete(self):
        """
        Страницы отдельной заметки, удаления и редактирования заметки
        доступны только автору заметки. Если на эти страницы попытается
        зайти другой пользователь — вернётся ошибка 404.
        """
        client_statuses = (
            (self.author_client, HTTPStatus.OK),
            (self.reader_client, HTTPStatus.NOT_FOUND),
        )
        for client, status in client_statuses:
            # Для каждой пары "пользователь - ожидаемый ответ"
            # перебираем имена тестируемых страниц:
            urls = (
                self.edit_url,
                self.delete_url,
                self.detail_url
            )
            for url in urls:
                with self.subTest(url=url):
                    response = client.get(url)
                    self.assertEqual(response.status_code, status)

    def test_redirect_for_anonymous_client(self):
        """
        При попытке перейти на страницу списка заметок, страницу успешного
        добавления записи, страницу добавления заметки, отдельной заметки,
        редактирования или удаления заметки анонимный пользователь
        перенаправляется на страницу логина.
        """
        # Сохраняем адрес страницы логина:
        login_url = self.login_url
        # В цикле перебираем имена страниц, с которых ожидаем редирект:
        urls = (
            self.edit_url,
            self.delete_url,
            self.detail_url,
            self.add_url,
            self.list_url,
            self.success_url,
        )
        for url in urls:
            with self.subTest(url=url):
                # Получаем адрес страницы редактирования или удаления
                redirect_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                # Проверяем, что редирект приведёт именно на указанную ссылку.
                self.assertRedirects(response, redirect_url)
