from django.contrib import admin
from .models import BudgetCategory, DepartmentBudget, SectionAllocation, ExpenseTransaction

admin.site.register(BudgetCategory)
admin.site.register(DepartmentBudget)
admin.site.register(SectionAllocation)
admin.site.register(ExpenseTransaction)
