from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from notes.forms import NoteForm
from notes.models import Note


User = get_user_model()


class TestHomePage(TestCase):

    LIST_URL = reverse('notes:list')

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
        cls.reader = User.objects.create(username='Читатель')
        cls.note = Note.objects.create(author=cls.author,
                                       title='Новость',
                                       text='Просто текст.',
                                       slug='slugname')
        cls.note_reader = Note.objects.create(author=cls.reader,
                                              title='Новость2',
                                              text='Просто текст2.',
                                              slug='slugname2')

    def test_news_count(self):
        """
        Проверяем отображение новостей.
        """
        # авторизуемся и идем на страницу постов
        self.client.force_login(self.author)
        response = self.client.get(self.LIST_URL)
        # Получаем список объектов из словаря контекста.
        object_list = response.context['object_list']
        # Определяем количество записей в списке.
        news_count = object_list.count()
        # Проверяем, что на странице есть новости.
        self.assertTrue(news_count > 0)

    def test_not_author_not_read_note(self):
        """
        Поверяем, что новости недоступны НЕ авторам
        """
        self.client.force_login(self.reader)
        response = self.client.get(self.LIST_URL)
        object_list = response.context['object_list']
        self.assertIsNot(self.note, object_list)


class TestDetailPage(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
        cls.news = Note.objects.create(
            author=cls.author,
            title='Заголовок',
            text='Текст статьи',
            slug='slugname'
        )
        cls.detail_url = reverse('notes:add')

    def test_anonymous_client_has_no_form(self):
        """
        Проверяем, что аноним не видит форму.
        """
        response = self.client.get(self.detail_url)
        self.assertIsNone(response.context)

    def test_authorized_client_has_form(self):
        """
        Проверяем, что авторизованный видит правильную форму.
        """
        self.client.force_login(self.author)
        response = self.client.get(self.detail_url)
        self.assertIn('form', response.context)
        # Проверим, что объект формы соответствует нужному классу формы.
        self.assertIsInstance(response.context['form'], NoteForm)
