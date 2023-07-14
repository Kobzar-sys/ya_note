from django.contrib.auth import get_user_model

from django.test import TestCase
from django.urls import reverse

from notes.models import Note

User = get_user_model()


class TestHomePage(TestCase):

    HOME_URL = reverse('notes:list')

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст',
            slug='test_slug',
            author=cls.author
        )

    def test_notes_count(self):
        response = self.client.get(self.HOME_URL)
        object_list = response.context['object_list']
        self.assertIn(object_list, cls.note)
        
    
