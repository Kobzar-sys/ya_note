from http import HTTPStatus

from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse

from notes.models import Note
from notes.views import NoteCreate, NoteUpdate


class NoteTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user1 = User.objects.create_user(
            username='user1', password='password1'
        )
        cls.user2 = User.objects.create_user(
            username='user2', password='password2'
        )
        cls.note1 = Note.objects.create(
            title='Note 1', text='Note 1 Text', author=cls.user1
        )
        cls.note2 = Note.objects.create(
            title='Note 2', text='Note 2 Text', author=cls.user2
        )

    def setUp(self):
        """
        Дополнительная настройка данных для тестов NoteTestCase.
        """
        self.auth_client = Client()
        self.auth_client.force_login(self.user1)

    def test_note_in_object_list_for_authenticated_user(self):
        """
        Проверка, что заметка пользователя отображается в списке
        заметок для аутентифицированного пользователя.
        """
        response = self.auth_client.get(reverse('notes:list'))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, self.note1.title)

    def test_note_not_in_object_list_for_other_user(self):
        """
        Проверка, что заметка другого пользователя не отображается в списке
        заметок для аутентифицированного пользователя.
        """
        self.auth_client.logout()
        self.auth_client.login(username='user2', password='password2')

        response = self.auth_client.get(reverse('notes:list'))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertNotContains(response, self.note1.title)
        self.assertContains(response, self.note2.title)

    def test_note_form_in_note_create_page(self):
        """
        Проверка, что форма для создания заметки отображается
        на странице создания заметки для аутентифицированного пользователя.
        """
        response = self.auth_client.get(reverse('notes:add'))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIsInstance(response.context['form'], NoteCreate.form_class)

    def test_note_form_in_note_update_page(self):
        """
        Проверка, что форма для обновления заметки отображается
        на странице обновления заметки для аутентифицированного пользователя.
        """
        response = self.auth_client.get(reverse(
            'notes:edit',
            args=[self.note1.slug])
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIsInstance(response.context['form'], NoteUpdate.form_class)
