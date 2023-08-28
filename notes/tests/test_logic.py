from http import HTTPStatus

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from notes.models import Note
from pytils.translit import slugify

WARNING = ' - такой slug уже существует, придумайте уникальное значение!'


class NoteCreationTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', password='testpassword'
        )

    def test_logged_in_user_can_create_note(self):
        """
        Проверка, что залогиненный пользователь может создать заметку.
        """
        self.client.login(username='testuser', password='testpassword')
        data = {'title': 'Название заметки', 'text': 'Текст заметки'}
        response = self.client.post(reverse('notes:add'), data=data)
        self.assertRedirects(response, reverse('notes:success'))

        self.assertEqual(Note.objects.count(), 1)

        created_note = Note.objects.first()

        self.assertEqual(created_note.title, data['title'])
        self.assertEqual(created_note.text, data['text'])

    def test_anonymous_user_cannot_create_note(self):
        """
        Проверка, что анонимный пользователь не может создать заметку.
        """
        response = self.client.post(
            reverse('notes:add'),
            data={'title': 'Название заметки', 'text': 'Текст заметки'}
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(Note.objects.count(), 0)


class NoteSlugTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username='testuser', password='testpassword'
        )

    def test_duplicate_slug_not_allowed(self):
        """
        Проверка, что невозможно создать две заметки с одинаковым slug.
        """
        data = {
            'title': 'Заметка 1',
            'text': 'Текст заметки 1',
            'slug': 'zametka-1'
        }
        self.client.login(username='testuser', password='testpassword')

        response1 = self.client.post(reverse('notes:add'), data=data)
        self.assertEqual(response1.status_code, HTTPStatus.FOUND)

        data['slug'] = data['slug'].strip()

        response2 = self.client.post(reverse('notes:add'), data=data)

        self.assertEqual(response2.status_code, HTTPStatus.OK)

        expected_error = 'zametka-1' + f"{WARNING}"

        self.assertFormError(
            response2,
            'form',
            'slug',
            expected_error,
        )
        self.assertEqual(Note.objects.count(), 1)


class NoteSlugGenerationTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username='testuser', password='testpassword'
        )

    def test_slug_auto_generation(self):
        """
        Проверка, что slug формируется автоматически,
        если не заполнен при создании заметки.
        """
        data = {'title': 'Название заметки', 'text': 'Текст заметки'}
        self.client.login(username='testuser', password='testpassword')
        response = self.client.post(reverse('notes:add'), data=data)
        self.assertEqual(response.status_code, 302)

        note = Note.objects.get(title=data['title'])

        expected_slug = slugify(data['title'])
        self.assertEqual(note.slug, expected_slug)


class NoteAuthorizationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(
            username='user1', password='testpassword1'
        )
        self.user2 = User.objects.create_user(
            username='user2', password='testpassword2'
        )
        self.note = Note.objects.create(
            title='Заметка', text='Текст заметки', author=self.user1
        )
        self.NEW_TITLE = 'Новое название'
        self.NEW_TEXT = 'Новый текст'

    def test_user_can_edit_own_note(self):
        """
        Проверка, что пользователь может редактировать свою заметку.
        """
        self.client.login(username='user1', password='testpassword1')
        response = self.client.post(
            reverse('notes:edit', args=[self.note.slug]),
            data={'title': self.NEW_TITLE, 'text': self.NEW_TEXT}
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.note.refresh_from_db()

        self.assertEqual(self.note.title, self.NEW_TITLE)

        self.assertEqual(self.note.text, self.NEW_TEXT)

    def test_user_cannot_edit_other_user_note(self):
        """
        Проверка, что пользователь не может редактировать чужую заметку.
        """
        self.client.login(username='user2', password='testpassword2')
        response = self.client.post(
            reverse('notes:edit', args=[self.note.slug]),
            data={'title': self.NEW_TITLE, 'text': self.NEW_TEXT}
        )
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.note.refresh_from_db()

        self.assertNotEqual(self.note.title, self.NEW_TITLE)

        self.assertNotEqual(self.note.text, self.NEW_TEXT)

    def test_user_can_delete_own_note(self):
        """
        Проверка, что пользователь может удалить свою заметку.
        """
        self.client.login(username='user1', password='testpassword1')
        response = self.client.post(
            reverse('notes:delete', args=[self.note.slug])
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(Note.objects.count(), 0)

    def test_user_cannot_delete_other_user_note(self):
        """
        Проверка, что пользователь не может удалить чужую заметку.
        """
        self.client.login(username='user2', password='testpassword2')
        response = self.client.post(
            reverse('notes:delete', args=[self.note.slug])
        )
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(Note.objects.count(), 1)
