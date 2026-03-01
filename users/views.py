from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.contrib import messages

class CustomLoginView(LoginView):
    template_name = 'users/login.html'
    redirect_authenticated_user = True
    
    def form_invalid(self, form):
        messages.error(self.request, "Invalid username or password. Please try again.")
        return super().form_invalid(form)

@login_required
def dashboard(request):
    return render(request, 'users/dashboard.html', {'user': request.user})

@login_required
def mark_notification_read(request, notif_id):
    from .models import Notification
    from django.shortcuts import get_object_or_404
    from django.http import HttpResponseRedirect
    
    notif = get_object_or_404(Notification, id=notif_id, user=request.user)
    notif.is_read = True
    notif.save()
    
    # Redirect back to the page the user was on
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return HttpResponseRedirect(referer)
    return redirect('dashboard')

@login_required
def manage_departments(request):
    if request.user.role != 'CEO':
        return redirect('dashboard')
        
    from .models import Department
    if request.method == 'POST':
        name = (request.POST.get('name') or '').strip()
        if name:
            if Department.objects.filter(name__iexact=name).exists():
                messages.error(request, f'Department "{name}" already exists.')
            else:
                Department.objects.create(name=name)
                messages.success(request, f'Department "{name}" created.')
        else:
            messages.error(request, "Department name is required.")
        return redirect('manage_departments')
        
    departments = Department.objects.all()
    return render(request, 'users/manage_departments.html', {'departments': departments})

@login_required
def manage_users(request):
    if request.user.role != 'CEO':
        return redirect('dashboard')
        
    from django.core.paginator import Paginator
    from django.db.models import Q
    from .models import CustomUser, Department
    if request.method == 'POST':
        username = (request.POST.get('username') or '').strip()
        email = request.POST.get('email', '')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        role = request.POST.get('role')
        dept_id = request.POST.get('department')
        
        if username and password and role:
            if password != confirm_password:
                messages.error(request, "Passwords do not match!")
                return redirect('manage_users')

            if role not in dict(CustomUser.ROLE_CHOICES):
                messages.error(request, 'Invalid role selected.')
                return redirect('manage_users')

            try:
                dept = Department.objects.get(id=dept_id) if dept_id else None
            except (Department.DoesNotExist, ValueError, TypeError):
                messages.error(request, 'Selected department is invalid.')
                return redirect('manage_users')

            if CustomUser.objects.filter(username__iexact=username).exists():
                messages.error(request, f'User "{username}" already exists.')
            else:
                CustomUser.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    role=role,
                    department=dept
                )
                messages.success(request, f'User {username} created as {role}.')
        else:
            messages.error(request, "Please fill in all required fields (Username, Password, Role).")
        return redirect('manage_users')
        
    # Filtering
    query = request.GET.get('q', '')
    role_filter = request.GET.get('role', '')
    dept_filter = request.GET.get('department', '')
    users = CustomUser.objects.all().order_by('username')
    
    if query:
        users = users.filter(
            Q(username__icontains=query) |
            Q(email__icontains=query)
        )
    if role_filter:
        users = users.filter(role=role_filter)
    if dept_filter:
        users = users.filter(department_id=dept_filter)

    # Pagination
    paginator = Paginator(users, 10)  # Show 10 users per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    departments = Department.objects.all()
    return render(request, 'users/manage_users.html', {
        'page_obj': page_obj, 
        'departments': departments, 
        'query': query,
        'role_filter': role_filter,
        'dept_filter': dept_filter
    })

@login_required
def reset_password(request, user_id):
    if request.user.role != 'CEO':
        return redirect('dashboard')
        
    from .models import CustomUser
    from django.shortcuts import get_object_or_404
    u = get_object_or_404(CustomUser, id=user_id)
    
    if request.method == 'POST':
        new_pass = request.POST.get('password')
        conf_pass = request.POST.get('confirm_password')

        if not new_pass:
            messages.error(request, 'Password cannot be empty.')
        elif new_pass == conf_pass:
            u.set_password(new_pass)
            u.save()
            messages.success(request, f'Password for {u.username} has been reset.')
        else:
            messages.error(request, 'Passwords do not match.')
            
    return redirect('manage_users')
