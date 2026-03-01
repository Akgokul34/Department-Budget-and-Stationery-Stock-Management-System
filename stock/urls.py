from django.urls import path
from . import views

urlpatterns = [
    path('request/', views.request_item, name='request_item'),
    path('my-requests/', views.my_requests, name='my_requests'),
    path('approvals/', views.approval_list, name='approval_list'),
    path('approvals/process/<int:req_id>/', views.process_request, name='process_request'),
    path('approvals/<int:req_id>/', views.process_request, name='approve_request'),
    path('issue/<int:req_id>/', views.issue_request, name='issue_request'),
    path('inventory/', views.inventory_list, name='inventory_list'),
    path('report/', views.stock_report, name='stock_report'),
    path('restock/<int:item_id>/', views.restock_item, name='restock_item'),
    path('export/', views.export_stock_csv, name='export_stock_csv'),
    path('request/<int:pk>/', views.request_detail, name='request_detail'),
    path('add/', views.add_stock_item, name='add_stock_item'),
    path('item/<int:item_id>/edit/', views.edit_stock_item, name='edit_stock_item'),
]
