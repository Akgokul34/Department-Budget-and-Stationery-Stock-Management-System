from django.test import TestCase
from django.urls import reverse

from users.models import CustomUser, Department
from .models import BudgetCategory, DepartmentBudget, SectionAllocation


class BudgetValidationTests(TestCase):
    def setUp(self):
        self.dept = Department.objects.create(name='Finance')
        self.hod = CustomUser.objects.create_user(
            username='hod_budget',
            password='pass1234',
            role='HOD',
            department=self.dept,
        )
        self.category = BudgetCategory.objects.create(name='Operations')
        self.budget = DepartmentBudget.objects.create(
            department=self.dept,
            financial_year='2025-2026',
            status='CEO_Approved',
        )
        self.alloc = SectionAllocation.objects.create(
            department_budget=self.budget,
            category=self.category,
            amount_allocated='1000.00',
            amount_spent='0.00',
        )

    def _message_texts(self, response):
        return [str(m) for m in response.context['messages']]

    def test_log_expense_invalid_decimal_shows_error(self):
        self.client.login(username='hod_budget', password='pass1234')
        response = self.client.post(
            reverse('log_expense', args=[self.alloc.id]),
            {'amount': 'bad-amount', 'description': 'invalid'},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('Invalid amount provided.', self._message_texts(response))

    def test_allocate_sections_invalid_decimal_shows_error(self):
        self.client.login(username='hod_budget', password='pass1234')
        response = self.client.post(
            reverse('allocate_sections', args=[self.budget.id]),
            {'category_id': str(self.category.id), 'amount': 'not-a-number'},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('Invalid amount provided.', self._message_texts(response))
