import os, sys, django
sys.path.insert(0, r'c:\Users\HP\OneDrive\Desktop\Department Budget and Stationery Stock Management System')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from users.models import CustomUser, Department

# Create a default department
dept, _ = Department.objects.get_or_create(name='Computer Science & Engineering')

# Superuser (admin)
if not CustomUser.objects.filter(username='admin').exists():
    u = CustomUser.objects.create_superuser(username='admin', password='admin123', email='admin@stm.edu')
    u.role = 'CEO'
    u.department = dept
    u.save()
    print('Created superuser: admin / admin123 (CEO)')

# Principal
if not CustomUser.objects.filter(username='principal').exists():
    u = CustomUser.objects.create_user(username='principal', password='password123', role='Principal', department=dept)
    u.is_staff = True
    u.save()
    print('Created user: principal / password123 (Principal)')

# CEO
if not CustomUser.objects.filter(username='ceo').exists():
    u = CustomUser.objects.create_user(username='ceo', password='password123', role='CEO', department=dept)
    u.is_staff = True
    u.save()
    print('Created user: ceo / password123 (CEO)')

print('\nAll users created successfully!')
print('Login at: http://localhost:8000/login/')
