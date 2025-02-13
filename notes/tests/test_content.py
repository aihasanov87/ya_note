from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from notes.forms import NoteForm
from notes.models import Note


User = get_user_model()


class TestHomePage(TestCase):

    @classmethod
    def setUpTestData(cls):

        cls.author = User.objects.create(username='Автор')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)

        cls.note = Note.objects.create(
            author=cls.author,
            title='Новость о том, что произошло',
            text='Просто текст.',
            slug='slugname')

        cls.reader = User.objects.create(username='Читатель')
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)

        cls.list_url = reverse('notes:list')
        cls.detail_url = reverse('notes:add')
        cls.edit_url = reverse('notes:edit', kwargs={'slug': cls.note.slug})

    def test_read_authorized_client(self):
        """Проверяем, что новость отображается и доступна только автору"""
        client_statuses = (
            (self.reader_client, False),
            (self.author_client, True),
        )
        for client, status in client_statuses:
            with self.subTest(client=client, status=status):
                response = client.get(self.list_url)
                object_list = response.context['object_list']
                self.assertIs(self.note in object_list, status)

    def test_authorized_client_has_form(self):
        """Проверяем, что авторизованный видит правильные формы"""
        urls = (
            (self.detail_url),
            (self.edit_url),
        )
        for url in urls:
            with self.subTest(url=url):
                response = self.author_client.get(url)
                self.assertIn('form', response.context)
                self.assertIsInstance(response.context['form'], NoteForm)
