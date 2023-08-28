from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from http import HTTPStatus

from notes.models import Note

User = get_user_model()


class NoteTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword'
        )
        self.note = Note.objects.create(
            title='Test Note',
            text='Test Note Text',
            author=self.user
        )

    def _get_test_pages(self):
        return {
            'List Page': reverse('notes:list'),
            'Add Page': reverse('notes:add'),
            'Success Page': reverse('notes:success'),
            'Detail Page': reverse('notes:detail', args=[self.note.slug]),
            'Edit Page': reverse('notes:edit', args=[self.note.slug]),
            'Delete Page': reverse('notes:delete', args=[self.note.slug]),
        }

    def test_anonymous_user_can_access_home_page(self):
        """
        Проверка, что анонимный пользователь может
        получить доступ к домашней странице.
        """
        response = self.client.get(reverse('notes:home'))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_authenticated_user_can_access_notes_pages(self):
        """
        Проверка, что аутентифицированный пользователь может
        получить доступ к страницам заметок.
        """
        self.client.login(username='testuser', password='testpassword')
        test_pages = self._get_test_pages()

        for page_name, page_url in test_pages.items():
            with self.subTest(page=page_name):
                response = self.client.get(page_url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_anonymous_user_redirected_to_login_page(self):
        """
        Проверка, что анонимный пользователь
        перенаправляется на страницу входа.
        """
        login_url = reverse('users:login') + '?next='
        test_pages = self._get_test_pages()

        for page_name, page_url in test_pages.items():
            with self.subTest(page=page_name):
                response = self.client.get(page_url)
                self.assertRedirects(response, login_url + page_url)

    def test_user_can_access_registration_page(self):
        """
        Проверка, что пользователь может
        получить доступ к странице регистрации.
        """
        response = self.client.get(reverse('users:signup'))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_user_can_access_login_page(self):
        """
        Проверка, что пользователь может получить доступ к странице входа.
        """
        response = self.client.get(reverse('users:login'))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_user_can_logout(self):
        """
        Проверка, что пользователь может выйти из учетной записи.
        """
        self.client.login(username='testuser', password='testpassword')

        response = self.client.get(reverse('users:logout'))
        self.assertEqual(response.status_code, HTTPStatus.OK)

        self.assertNotIn('_auth_user_id', self.client.session)

    def test_user_can_edit_delete_detail_page(self):
        """
        Проверка, что пользователь не может просматривать,
        редактировать и удалять чужие заметки.
        """
        test_pages = {
            'Edit Page': (
                reverse('notes:edit', args=[self.note.slug]),
                HTTPStatus.FOUND
            ),
            'Delete Page': (
                reverse('notes:delete', args=[self.note.slug]),
                HTTPStatus.FOUND
            ),
            'Detail Page': (
                reverse('notes:detail', args=[self.note.slug]),
                HTTPStatus.FOUND
            ),
        }

        self.client.login(username='user2', password='testpassword2')

        for page_name, (page_url, expected_status) in test_pages.items():
            with self.subTest(page=page_name):
                response = self.client.get(page_url)
                self.assertEqual(response.status_code, expected_status)
