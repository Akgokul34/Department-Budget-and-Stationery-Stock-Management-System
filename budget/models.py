from django.db import models
from users.models import Department
from django.conf import settings

class BudgetCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class DepartmentBudget(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Principal_Approved', 'Principal Approved'),
        ('CEO_Approved', 'CEO Approved'),
        ('Rejected', 'Rejected'),
    )

    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    financial_year = models.CharField(max_length=9)  # e.g. "2025-2026"
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='approved_budgets', null=True, blank=True, on_delete=models.SET_NULL)
    
    class Meta:
        unique_together = ('department', 'financial_year')

    @property
    def total_allocated(self):
        return sum(a.amount_allocated for a in self.allocations.all())

    @property
    def total_spent(self):
        return sum(a.amount_spent for a in self.allocations.all())

    @property
    def total_remaining(self):
        return self.total_allocated - self.total_spent

    def __str__(self):
        return f"{self.department.name} - {self.financial_year}"

class SectionAllocation(models.Model):
    department_budget = models.ForeignKey(DepartmentBudget, on_delete=models.CASCADE, related_name='allocations')
    category = models.ForeignKey(BudgetCategory, on_delete=models.CASCADE)
    amount_allocated = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    amount_spent = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    @property
    def remaining_budget(self):
        return self.amount_allocated - self.amount_spent

    class Meta:
        unique_together = ('department_budget', 'category')

    def __str__(self):
        return f"{self.department_budget} - {self.category.name}"

class ExpenseTransaction(models.Model):
    allocation = models.ForeignKey(SectionAllocation, on_delete=models.CASCADE, related_name='expenses')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.amount} spent on {self.allocation.category.name} ({self.date.date()})"
