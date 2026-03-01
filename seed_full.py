"""
Seed script: Populates the STM-SYS database with 10+ years of realistic data.
Run:  .\venv\Scripts\python.exe seed_full.py
"""
import os, sys, random, decimal
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import django
django.setup()

from users.models import CustomUser, Department, Notification
from stock.models import StationeryItem, StationeryRequest
from budget.models import BudgetCategory, DepartmentBudget, SectionAllocation, ExpenseTransaction
from django.utils import timezone

random.seed(42)

# ============================================================
# 1) DEPARTMENTS
# ============================================================
DEPT_NAMES = [
    'Computer Science & Engineering',
    'Electrical & Electronics',
    'Mechanical Engineering',
    'Civil Engineering',
    'Electronics & Communication',
    'Mathematics',
    'Physics',
    'Management Studies',
    'Applied Sciences & Humanities',
    'Administration',
]
departments = []
for name in DEPT_NAMES:
    d, _ = Department.objects.get_or_create(name=name)
    departments.append(d)
print(f'✅  {len(departments)} departments created')

# ============================================================
# 2) USERS  (keep existing admin/principal/ceo, add HODs + Staff)
# ============================================================
created_users = 0

# Assign existing users to first department if not set
for uname in ['admin', 'principal', 'ceo']:
    try:
        u = CustomUser.objects.get(username=uname)
        if not u.department:
            u.department = departments[0]
            u.save()
    except CustomUser.DoesNotExist:
        pass

# Create one HOD per department
hods = []
for dept in departments:
    uname = f'hod_{dept.name.split()[0].lower()}'
    u, created = CustomUser.objects.get_or_create(
        username=uname,
        defaults={'role': 'HOD', 'department': dept}
    )
    if created:
        u.set_password('password123')
        u.save()
        created_users += 1
    hods.append(u)

# Create 3 staff per department
staff_users = []
for dept in departments:
    prefix = dept.name.split()[0].lower()
    for i in range(1, 4):
        uname = f'staff_{prefix}_{i}'
        u, created = CustomUser.objects.get_or_create(
            username=uname,
            defaults={'role': 'Staff', 'department': dept}
        )
        if created:
            u.set_password('password123')
            u.save()
            created_users += 1
        staff_users.append(u)

print(f'✅  {created_users} new users created  (total: {CustomUser.objects.count()})')

# ============================================================
# 3) STATIONERY ITEMS
# ============================================================
ITEMS = [
    ('A4 Paper (Ream)',        'Paper Products',    200, 50),
    ('A3 Paper (Ream)',        'Paper Products',    80,  20),
    ('Blue Ballpoint Pens',    'Writing',           500, 100),
    ('Black Ballpoint Pens',   'Writing',           400, 80),
    ('Red Ballpoint Pens',     'Writing',           150, 30),
    ('Gel Pens (Assorted)',    'Writing',           200, 40),
    ('Whiteboard Markers',     'Writing',           180, 40),
    ('Permanent Markers',      'Writing',           100, 25),
    ('Pencils HB',             'Writing',           300, 60),
    ('Erasers',                'Writing',           250, 50),
    ('Staplers',               'Office Equipment',  60,  15),
    ('Stapler Pins (Box)',     'Office Supplies',   300, 80),
    ('Paper Clips (Box)',      'Office Supplies',   250, 60),
    ('Binder Clips (Box)',     'Office Supplies',   150, 30),
    ('Scotch Tape',            'Office Supplies',   120, 30),
    ('Glue Sticks',            'Office Supplies',   100, 25),
    ('Scissors',               'Office Equipment',  80,  20),
    ('Rulers (30cm)',          'Office Supplies',   100, 20),
    ('File Folders',           'Filing',            400, 100),
    ('Lever Arch Files',       'Filing',            150, 40),
    ('Envelopes (White)',      'Mailing',           500, 100),
    ('Envelopes (Brown A4)',   'Mailing',           200, 50),
    ('Sticky Notes (Pad)',     'Office Supplies',   300, 60),
    ('Correction Fluid',      'Writing',           80,  20),
    ('Printer Toner (Black)',  'Printer Supplies',  30,  8),
    ('Printer Toner (Color)',  'Printer Supplies',  20,  5),
    ('CD/DVD Spindle (50pk)',  'Media',             15,  5),
    ('USB Flash Drive 32GB',   'Media',             40,  10),
    ('Desk Calendar',          'Office Supplies',   50,  15),
    ('Attendance Register',    'Registers',         80,  20),
]
items = []
for name, desc, stock, threshold in ITEMS:
    it, _ = StationeryItem.objects.get_or_create(
        name=name,
        defaults={'description': desc, 'total_stock': stock, 'reorder_threshold': threshold}
    )
    items.append(it)
print(f'✅  {len(items)} stationery items created')

# ============================================================
# 4) BUDGET CATEGORIES
# ============================================================
CATEGORIES = [
    'Lab Equipment',
    'Infrastructure Maintenance',
    'Department Stationery',
    'Technical Events',
    'Research Grants',
    'Faculty Development',
    'Library & Journals',
    'Software Licenses',
]
categories = []
for name in CATEGORIES:
    c, _ = BudgetCategory.objects.get_or_create(name=name)
    categories.append(c)
print(f'✅  {len(categories)} budget categories created')

# ============================================================
# 5) BUDGETS + ALLOCATIONS + EXPENSES  (FY 2016-2017 → 2026-2027)
# ============================================================
STATUS_FLOW = ['Pending', 'Principal_Approved', 'CEO_Approved']
approvers = list(CustomUser.objects.filter(role__in=['Principal', 'CEO']))

budget_count = 0
alloc_count = 0
expense_count = 0

for start_year in range(2016, 2027):  # 11 financial years
    fy = f'{start_year}-{start_year + 1}'
    # Older years are fully approved; current year may be pending
    if start_year < 2025:
        status = 'CEO_Approved'
    elif start_year == 2025:
        status = 'Principal_Approved'
    else:
        status = random.choice(['Pending', 'CEO_Approved'])

    for dept in departments:
        budget, created = DepartmentBudget.objects.get_or_create(
            department=dept,
            financial_year=fy,
            defaults={
                'status': status,
                'approved_by': random.choice(approvers) if status != 'Pending' else None,
            }
        )
        if not created:
            continue
        budget_count += 1

        # Allocate 4-7 random categories per budget
        num_cats = random.randint(4, min(7, len(categories)))
        chosen_cats = random.sample(categories, num_cats)

        for cat in chosen_cats:
            allocated = decimal.Decimal(random.randint(20000, 500000))
            # Older years: spend 40-95%; recent years: spend less
            if start_year < 2024:
                spend_pct = random.uniform(0.40, 0.95)
            elif start_year < 2026:
                spend_pct = random.uniform(0.10, 0.60)
            else:
                spend_pct = random.uniform(0.0, 0.25)

            spent = round(decimal.Decimal(float(allocated) * spend_pct), 2)

            alloc, _ = SectionAllocation.objects.get_or_create(
                department_budget=budget,
                category=cat,
                defaults={'amount_allocated': allocated, 'amount_spent': spent}
            )
            alloc_count += 1

            # Create 1-5 expense transactions per allocation (only if spent > 0)
            if spent > 0 and status != 'Pending':
                num_txns = random.randint(1, 5)
                remaining_to_distribute = spent
                hod_for_dept = next((h for h in hods if h.department == dept), hods[0])

                for t in range(num_txns):
                    if t == num_txns - 1:
                        txn_amount = remaining_to_distribute
                    else:
                        txn_amount = round(remaining_to_distribute * decimal.Decimal(random.uniform(0.1, 0.5)), 2)
                        remaining_to_distribute -= txn_amount

                    if txn_amount <= 0:
                        continue

                    # Random date within the financial year
                    fy_start = datetime(start_year, 7, 1)
                    fy_end = datetime(start_year + 1, 6, 28)
                    rand_days = random.randint(0, (fy_end - fy_start).days)
                    txn_date = timezone.make_aware(fy_start + timedelta(days=rand_days))

                    descriptions = [
                        f'Purchase of {cat.name} materials',
                        f'Quarterly {cat.name} expense',
                        f'{cat.name} - vendor payment',
                        f'Annual {cat.name} renewal',
                        f'{cat.name} maintenance cost',
                    ]

                    ExpenseTransaction.objects.create(
                        allocation=alloc,
                        amount=txn_amount,
                        description=random.choice(descriptions),
                        date=txn_date,
                        recorded_by=hod_for_dept,
                    )
                    expense_count += 1

print(f'✅  {budget_count} budgets, {alloc_count} allocations, {expense_count} expense transactions')

# ============================================================
# 6) STATIONERY REQUESTS  (spread over 10 years)
# ============================================================
STATUS_CHOICES = ['Pending', 'HOD_Approved', 'Principal_Approved', 'CEO_Approved', 'Rejected', 'Issued']
request_count = 0

all_staff = list(CustomUser.objects.filter(role='Staff'))
all_approvers = list(CustomUser.objects.filter(role__in=['HOD', 'Principal', 'CEO']))

for year in range(2016, 2027):
    # More requests in recent years
    num_requests = random.randint(30, 80) if year < 2024 else random.randint(80, 150)

    for _ in range(num_requests):
        user = random.choice(all_staff)
        item = random.choice(items)
        qty = random.randint(1, 50)

        # Older requests are more likely to be fully processed
        if year < 2024:
            status = random.choices(
                STATUS_CHOICES,
                weights=[2, 3, 5, 15, 5, 70],  # mostly Issued
                k=1
            )[0]
        elif year < 2026:
            status = random.choices(
                STATUS_CHOICES,
                weights=[5, 10, 15, 20, 10, 40],
                k=1
            )[0]
        else:
            status = random.choices(
                STATUS_CHOICES,
                weights=[30, 20, 15, 10, 5, 20],
                k=1
            )[0]

        # Random date in that year
        start_date = datetime(year, 1, 1)
        end_date = min(datetime(year, 12, 31), datetime(2026, 12, 31))
        rand_days = random.randint(0, (end_date - start_date).days)
        req_date = timezone.make_aware(start_date + timedelta(days=rand_days))

        req = StationeryRequest(
            user=user,
            item=item,
            quantity=qty,
            status=status,
            approved_by=random.choice(all_approvers) if status not in ['Pending', 'Rejected'] else None,
        )
        req.save()
        # Override auto_now_add
        StationeryRequest.objects.filter(pk=req.pk).update(request_date=req_date)
        request_count += 1

print(f'✅  {request_count} stationery requests created')

# ============================================================
# 7) NOTIFICATIONS (a few recent ones)
# ============================================================
notif_msgs = [
    'Your stationery request has been approved by HOD.',
    'Budget for FY 2026-2027 has been submitted for approval.',
    'New expense logged against Lab Equipment.',
    'Your request for A4 Paper has been issued.',
    'Low stock alert: Printer Toner (Black) is below threshold.',
    'Budget FY 2025-2026 approved by CEO.',
]
notif_count = 0
for user in CustomUser.objects.all()[:10]:
    for msg in random.sample(notif_msgs, k=random.randint(1, 3)):
        Notification.objects.create(user=user, message=msg, is_read=random.choice([True, False]))
        notif_count += 1

print(f'✅  {notif_count} notifications created')
print(f'\n🎉  Database fully seeded! Login at http://localhost:8000/login/')
