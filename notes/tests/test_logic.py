from http import HTTPStatus

from pytest_django.asserts import assertFormError
from pytils.translit import slugify
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from notes.forms import WARNING
from notes.models import Note


User = get_user_model()


class TestPostsCreation(TestCase):

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
            title='Заголовок',
            text='Текст новой заметки',
            slug='slugname')

        cls.form_data = {
            'title': 'Заголовок 2',
            'text': 'Текст новой заметки 2',
            'slug': 'slugname2'
        }

        cls.add_url = reverse('notes:add')
        cls.edit_url = reverse('notes:edit', args=(cls.news.slug,))
        cls.delete_url = reverse('notes:delete', args=(cls.news.slug,))

    def test_user_can_create_post(self):
        """Создаем пост после авторизации и редиректим"""
        posts_before = Note.objects.count()
        response = self.auth_client.post(self.add_url, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        posts_after = Note.objects.count()
        self.assertTrue(posts_after > posts_before)
        new_post = Note.objects.filter(slug=self.form_data['slug']).get()
        self.assertEqual(new_post.title, self.form_data['title'])
        self.assertEqual(new_post.text, self.form_data['text'])
        self.assertEqual(new_post.slug, self.form_data['slug'])

    def test_not_create_post_anonymous_user(self):
        """Пытаемся создать пост анонимом"""
        posts_before = Note.objects.count()
        response = self.client.post(self.add_url, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        posts_after = Note.objects.count()
        self.assertTrue(posts_after == posts_before)

    def test_duplication_slug_create_post(self):
        """Пытаемся создать пост с имеющимся slug"""
        form_data = self.form_data
        form_data['slug'] = self.news.slug
        posts_before = Note.objects.count()
        response = self.auth_client.post(self.add_url, data=form_data)
        posts_after = Note.objects.count()
        assertFormError(
            response, 'form', 'slug', errors=(self.news.slug + WARNING))
        self.assertTrue(posts_after == posts_before)

    def test_automatic_creat_post_not_slug(self):
        """Пытаемся создать пост без slug"""
        self.form_data.pop('slug')
        response = self.auth_client.post(self.add_url, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertTrue(
            Note.objects.filter(title=self.form_data['title']).exists())
        new_post = Note.objects.filter(title=self.form_data['title']).get()
        self.assertEqual(new_post.slug, slugify(self.form_data['title']))

    def test_edit_other_autor(self):
        """Проверяем, что не можем править чужой пост"""
        response = self.auth_reader.post(self.edit_url, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertNotEqual(self.news.title, self.form_data['title'])
        self.assertNotEqual(self.news.text, self.form_data['text'])
        self.assertNotEqual(self.news.slug, self.form_data['slug'])

    def test_delite_other_autor(self):
        """Проверяем, что не можем удалить чужой пост"""
        response = self.auth_reader.post(self.delete_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTrue(self.news.title)
        self.assertTrue(self.news.text)
        self.assertTrue(self.news.slug)
