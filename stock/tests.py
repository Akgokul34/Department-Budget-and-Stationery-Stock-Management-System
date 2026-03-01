from django.test import TestCase
from django.urls import reverse

from users.models import CustomUser, Department
from .models import StationeryItem


class StockValidationTests(TestCase):
    def setUp(self):
        self.dept = Department.objects.create(name='IT')
        self.hod = CustomUser.objects.create_user(
            username='hod_user',
            password='pass1234',
            role='HOD',
            department=self.dept,
        )
        self.staff = CustomUser.objects.create_user(
            username='staff_user',
            password='pass1234',
            role='Staff',
            department=self.dept,
        )
        self.item = StationeryItem.objects.create(
            name='Pen',
            total_stock=10,
            reorder_threshold=2,
        )

    def _message_texts(self, response):
        return [str(m) for m in response.context['messages']]

    def test_add_stock_item_invalid_numeric_values_show_error(self):
        self.client.login(username='hod_user', password='pass1234')
        response = self.client.post(
            reverse('add_stock_item'),
            {
                'name': 'Notebook',
                'description': 'A5',
                'total_stock': 'abc',
                'reorder_threshold': '5',
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('Invalid stock values provided.', self._message_texts(response))

    def test_restock_zero_quantity_shows_error(self):
        self.client.login(username='hod_user', password='pass1234')
        response = self.client.post(
            reverse('restock_item', args=[self.item.id]),
            {'quantity': '0'},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'Quantity cannot be zero. Please enter a positive or negative amount.',
            self._message_texts(response),
        )

    def test_request_item_invalid_item_shows_error(self):
        self.client.login(username='staff_user', password='pass1234')
        response = self.client.post(
            reverse('request_item'),
            {'item_id': 'bad-id', 'quantity': '1'},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('Selected item is invalid.', self._message_texts(response))
