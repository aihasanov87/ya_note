import uuid
from http import HTTPStatus
from pytils.translit import slugify

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from notes.models import Note


User = get_user_model()


class TestPostsCreation(TestCase):

    COMMENT_TITLE = 'Заголовок'
    COMMENT_TEXT = 'Текст новой заметки.'
    COMMENT_SLUG = 'slugname'

    @classmethod
    def setUpTestData(cls):
        # Автор постов
        cls.author = User.objects.create(username='Автор')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.author)

        # Еще один автор для проверок невозможности редактирования и удаления
        cls.reader = User.objects.create(username='Не автор')
        cls.auth_reader = Client()
        cls.auth_reader.force_login(cls.reader)

        # Новость нужна для теста на создание поста с дублирующим слаг
        cls.news = Note.objects.create(
            author=cls.author,
            title=cls.COMMENT_TITLE,
            text=cls.COMMENT_TEXT,
            slug=cls.COMMENT_SLUG)

    def base_form_data(self,
                       title=COMMENT_TITLE,
                       text=COMMENT_TEXT,
                       slug=None):
        """Для сбора значений в form_data для тестовых сценариев"""
        if slug:
            form_data = {
                'title': title,
                'text': text,
                'slug': slug
            }
        else:
            form_data = {
                'title': title,
                'text': text
            }
        return form_data

    def test_user_can_create_post(self):
        """Создаем пост после авторизации и редиректим"""
        form_data = self.base_form_data(slug=f'slugname{uuid.uuid4()}')

        response = self.auth_client.post(reverse('notes:add'), data=form_data)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertTrue(Note.objects.filter(slug=form_data['slug']).exists())

    def test_not_create_post_anonymous_user(self):
        """Пытаемся создать пост анонимом"""

        form_data = self.base_form_data(slug=f'slugname{uuid.uuid4()}')

        response = self.client.post(reverse('notes:add'), data=form_data)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertFalse(Note.objects.filter(slug=form_data['slug']).exists())

    def test_duplication_slug_create_post(self):
        """Пытаемся создать пост с имеющимся slug"""

        form_data = self.base_form_data(title=uuid.uuid4(),
                                        slug=self.COMMENT_SLUG)

        self.auth_client.post(reverse('notes:add'), data=form_data)
        self.assertFalse(Note.objects.filter(
            title=form_data['title']).exists())

    def test_automatic_creat_post_not_slug(self):
        """Пытаемся создать пост без slug"""

        form_data = self.base_form_data(title=f'Тестовый пост {uuid.uuid4()}')

        response = self.auth_client.post(reverse('notes:add'), data=form_data)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertTrue(Note.objects.filter(title=form_data['title']).exists())
        post = Note.objects.get(title=form_data['title'])
        self.assertEqual(post.slug, slugify(form_data['title']))

    def test_edit_other_autor(self):
        """Проверяем, что не можем править чужой пост"""

        form_data = self.base_form_data(title=uuid.uuid4())

        response = self.auth_reader.post(
            reverse('notes:edit', args=(self.news.slug,)), data=form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_delite_other_autor(self):
        """Проверяем, что не можем удалить чужой пост"""
        response = self.auth_reader.post(
            reverse('notes:delete', args=(self.news.slug,)))
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
