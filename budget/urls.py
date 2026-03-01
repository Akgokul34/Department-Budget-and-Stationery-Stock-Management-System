from django.urls import path
from . import views

urlpatterns = [
    path('enter/', views.enter_budget, name='enter_budget'),
    path('allocate/<int:budget_id>/', views.allocate_sections, name='allocate_sections'),
    path('overview/', views.budget_overview, name='budget_overview'),
    path('process/<int:budget_id>/', views.process_budget_request, name='process_budget_request'),
    path('report/', views.budget_report, name='budget_report'),
    path('log-expense/<int:alloc_id>/', views.log_expense, name='log_expense'),
    path('transactions/', views.transaction_logs, name='transaction_logs'),
    path('export/', views.export_budget_csv, name='export_budget_csv'),
    path('transaction/<int:pk>/', views.transaction_detail, name='transaction_detail'),
    path('report/<int:pk>/', views.budget_detail, name='budget_detail'),
]
