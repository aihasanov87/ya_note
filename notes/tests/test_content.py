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

    def test_read_only_author(self):
        """Проверяем, что новость отображается и доступна только автору"""
        users_statuses = (
            (self.reader_client, False),
            (self.author_client, True),
        )
        for name, args in users_statuses:
            with self.subTest(name=name, args=args):
                response = name.get(self.list_url)
                object_list = response.context['object_list']
                news_count = object_list.count()
                self.assertIs(news_count > 0, args)

    def test_authorized_client_has_form(self):
        """Проверяем, что авторизованный видит правильные формы"""
        response_add_form = self.author_client.get(self.detail_url)
        response_edit_form = self.author_client.get(self.edit_url)

        self.assertIn('form', response_add_form.context)
        self.assertIn('form', response_edit_form.context)

        # Проверим, что объект формы соответствует нужному классу формы.
        self.assertIsInstance(response_add_form.context['form'], NoteForm)
        self.assertIsInstance(response_edit_form.context['form'], NoteForm)
