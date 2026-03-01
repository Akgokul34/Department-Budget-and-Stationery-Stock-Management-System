from django.test import TestCase
from django.urls import reverse

from .models import CustomUser, Department


class UsersValidationTests(TestCase):
    def setUp(self):
        self.ceo = CustomUser.objects.create_user(
            username='ceo_user',
            password='pass1234',
            role='CEO'
        )

    def _message_texts(self, response):
        return [str(m) for m in response.context['messages']]

    def test_login_invalid_credentials_shows_message(self):
        response = self.client.post(
            reverse('login'),
            {'username': 'unknown', 'password': 'bad-pass'},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid username or password. Please try again.')

    def test_manage_departments_duplicate_name_shows_error(self):
        self.client.login(username='ceo_user', password='pass1234')
        Department.objects.create(name='Accounts')

        response = self.client.post(
            reverse('manage_departments'),
            {'name': 'Accounts'},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('Department "Accounts" already exists.', self._message_texts(response))

    def test_manage_users_invalid_department_shows_error(self):
        self.client.login(username='ceo_user', password='pass1234')

        response = self.client.post(
            reverse('manage_users'),
            {
                'username': 'staff_1',
                'password': 'pass1234',
                'confirm_password': 'pass1234',
                'role': 'Staff',
                'department': '999999',
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('Selected department is invalid.', self._message_texts(response))
