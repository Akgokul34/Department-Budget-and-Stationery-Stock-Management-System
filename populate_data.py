import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from users.models import CustomUser, Department
from stock.models import StationeryItem
from budget.models import BudgetCategory

def populate():
    # Create Departments
    cs, _ = Department.objects.get_or_create(name="Computer Science")
    ce, _ = Department.objects.get_or_create(name="Civil Engineering")

    users_data = [
        ('ceo_user', 'ceo@admin.com', 'admin123', 'CEO', None, True), 
        ('principal_user', 'pr@test.com', 'admin123', 'Principal', None, False),
        ('hod_cs', 'hod@cs.com', 'admin123', 'HOD', cs, False),
        ('staff_cs', 'staff@cs.com', 'admin123', 'Staff', cs, False),
    ]

    for username, email, password, role, dept, is_staff in users_data:
        if not CustomUser.objects.filter(username=username).exists():
            u = CustomUser.objects.create_user(username=username, email=email, password=password)
            u.role = role
            u.department = dept
            u.is_staff = is_staff
            if role == 'CEO':
                u.is_superuser = True
            u.save()

    items = [
        ("Log Book (Theory)", 50),
        ("Log Book (Practical)", 50),
        ("A4 Sheets (Bundle)", 100),
        ("Whiteboard Marker (Black)", 20),
        ("Chalk (White) Boxes", 30),
        ("Correction Pen", 15)
    ]
    for name, stock in items:
        StationeryItem.objects.get_or_create(name=name, defaults={'total_stock': stock})

    cats = [
        "Laboratory equipment",
        "Software",
        "Laboratory consumable",
        "Maintenance and spares",
        "R & D",
        "Training and Travel",
        "Miscellaneous expenses"
    ]
    for cat in cats:
        BudgetCategory.objects.get_or_create(name=cat)

    print("Database populated successfully with test accounts and items!")

if __name__ == '__main__':
    populate()
