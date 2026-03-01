import os
import django
from django.test import Client
from django.urls import get_resolver
from django.contrib.auth import get_user_model

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

# Allow 'testserver' in settings just for this script
from django.conf import settings
settings.ALLOWED_HOSTS.append('testserver')

User = get_user_model()
client = Client()

def test_urls_for_user(username, password):
    print(f"\n--- Testing as user: {username} ---")
    logged_in = client.login(username=username, password=password)
    if not logged_in:
        print(f"Failed to log in as {username}")
        return 0

    urls_to_test = [
        '/',
        '/login/',
        '/logout/',
        '/manage/departments/',
        '/manage/users/',
        '/stock/request/',
        '/stock/approvals/',
        '/stock/inventory/',
        '/stock/report/',
        '/stock/export/',
        '/budget/enter/',
        '/budget/overview/',
        '/budget/report/',
        '/budget/transactions/',
        '/budget/export/',
    ]

    from users.models import Notification, CustomUser
    from stock.models import StationeryItem, StationeryRequest
    from budget.models import DepartmentBudget, ExpenseTransaction, SectionAllocation
    
    # Grab some instances to test dynamic URLs
    user = CustomUser.objects.exclude(username=username).first()
    if user:
        urls_to_test.append(f'/manage/users/{user.id}/reset/')
        
    notif = Notification.objects.filter(user__username=username).first()
    if notif:
        urls_to_test.append(f'/notifications/{notif.id}/read/')
        
    req = StationeryRequest.objects.first()
    if req:
        urls_to_test.extend([
            f'/stock/approvals/process/{req.id}/',
            f'/stock/approvals/{req.id}/',
            f'/stock/issue/{req.id}/',
            f'/stock/request/{req.id}/'
        ])
        
    item = StationeryItem.objects.first()
    if item:
        urls_to_test.append(f'/stock/restock/{item.id}/')
        
    budget = DepartmentBudget.objects.first()
    if budget:
        urls_to_test.extend([
            f'/budget/allocate/{budget.id}/',
            f'/budget/process/{budget.id}/',
            f'/budget/report/{budget.id}/'
        ])
        
    alloc = SectionAllocation.objects.first()
    if alloc:
        urls_to_test.append(f'/budget/log-expense/{alloc.id}/')
        
    transaction = ExpenseTransaction.objects.first()
    if transaction:
        urls_to_test.append(f'/budget/transaction/{transaction.id}/')

    errors_found = 0
    for url in urls_to_test:
        response = client.get(url)
        if response.status_code >= 500:
            print(f"ERR {response.status_code} at {url}")
            errors_found += 1
        else:
            print(f"OK  {response.status_code} at {url}")
            
    return errors_found

def run_tests():
    total_errors = 0
    users_to_test = {
        'ceo': 'password123',
        'principal': 'password123',
        'hod_computer': 'password123',
        'staff_computer_1': 'password123',
    }
    for username, password in users_to_test.items():
        total_errors += test_urls_for_user(username, password)
    
    print(f"\nTotal 500 errors found: {total_errors}")

if __name__ == '__main__':
    run_tests()
