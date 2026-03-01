from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import DepartmentBudget, SectionAllocation, BudgetCategory
from django.contrib import messages
from decimal import Decimal, InvalidOperation
import re
@login_required
def enter_budget(request):
    if request.user.role not in ['HOD', 'Principal', 'CEO']:
        return redirect('dashboard')
        
    if request.method == 'POST':
        financial_year = (request.POST.get('financial_year') or '').strip()
        if not financial_year:
            messages.error(request, "Financial year is required.")
            return redirect('enter_budget')
        if not re.fullmatch(r"\d{4}-\d{4}", financial_year):
            messages.error(request, "Financial year must be in YYYY-YYYY format (e.g., 2025-2026).")
            return redirect('enter_budget')
        start_year = int(financial_year[:4])
        end_year = int(financial_year[5:])
        if end_year != start_year + 1:
            messages.error(request, "Financial year range must be consecutive (e.g., 2025-2026).")
            return redirect('enter_budget')
        
        budget, created = DepartmentBudget.objects.get_or_create(
            department=request.user.department,
            financial_year=financial_year
        )
        if created:
            messages.success(request, f'Budget created for {financial_year}. Now allocate to sections.')
        return redirect('allocate_sections', budget_id=budget.id)
        
    return render(request, 'budget/enter_budget.html')

@login_required
def allocate_sections(request, budget_id):
    budget = get_object_or_404(DepartmentBudget, id=budget_id)
    categories = BudgetCategory.objects.all()
    allocations = budget.allocations.all()
    
    if request.method == 'POST':
        category_id = request.POST.get('category_id')
        
        if not category_id:
            messages.error(request, "Please select a category first.")
            return redirect('allocate_sections', budget_id=budget.id)

        try:
            amount = Decimal(request.POST.get('amount', '0'))
        except (ValueError, TypeError, InvalidOperation):
            messages.error(request, "Invalid amount provided.")
            return redirect('allocate_sections', budget_id=budget.id)
        
        cat = get_object_or_404(BudgetCategory, id=category_id)
        alloc, created = SectionAllocation.objects.get_or_create(
            department_budget=budget,
            category=cat
        )
        
        new_total = alloc.amount_allocated + amount
        if new_total < alloc.amount_spent:
            messages.error(request, f"Cannot reduce allocation below what has already been spent (₹{alloc.amount_spent}).")
        elif new_total < 0:
             messages.error(request, "Allocation amount cannot be negative.")
        else:
            alloc.amount_allocated = new_total
            alloc.save()
            action = "Added to" if amount >= 0 else "Subtracted from"
            messages.success(request, f'Successfully {action.lower()} {cat.name} allocation. New total: ₹{alloc.amount_allocated}')
            
        return redirect('allocate_sections', budget_id=budget.id)
        
    return render(request, 'budget/allocate_sections.html', {
        'budget': budget,
        'categories': categories,
        'allocations': allocations
    })

@login_required
def budget_overview(request):
    user = request.user
    if user.role == 'HOD':
        budgets = DepartmentBudget.objects.filter(department=user.department)
    elif user.role in ['Principal', 'CEO']:
        budgets = DepartmentBudget.objects.all()
    else:
        return redirect('dashboard')
        
    fy_filter = request.GET.get('fy', '')
    status_filter = request.GET.get('status', '')

    if fy_filter:
        budgets = budgets.filter(financial_year=fy_filter)
    if status_filter:
        budgets = budgets.filter(status=status_filter)
        
    # Get distinct years for the filter dropdown
    years = DepartmentBudget.objects.values_list('financial_year', flat=True).distinct().order_by('-financial_year')
        
    return render(request, 'budget/budget_overview.html', {
        'budgets': budgets,
        'fy_filter': fy_filter,
        'status_filter': status_filter,
        'years': years
    })

@login_required
def process_budget_request(request, budget_id):
    budget = get_object_or_404(DepartmentBudget, id=budget_id)
    action = request.POST.get('action')
    user = request.user
    
    if action == 'reject':
        budget.status = 'Rejected'
        budget.approved_by = user
        budget.save()
        
        from users.models import CustomUser, Notification
        hods = CustomUser.objects.filter(department=budget.department, role='HOD')
        for hod in hods:
            Notification.objects.create(user=hod, message=f"Department budget for FY {budget.financial_year} was rejected by {user.role}.")
            
        messages.info(request, 'Department budget rejected.')
        return redirect('approval_list')
        
    if action == 'approve':
        from users.models import CustomUser, Notification
        if user.role == 'Principal':
            budget.status = 'Principal_Approved'
            hods = CustomUser.objects.filter(department=budget.department, role='HOD')
            for hod in hods:
                Notification.objects.create(user=hod, message=f"Department budget for FY {budget.financial_year} was approved by Principal.")
        elif user.role == 'CEO':
            budget.status = 'CEO_Approved'
            hods = CustomUser.objects.filter(department=budget.department, role='HOD')
            for hod in hods:
                Notification.objects.create(user=hod, message=f"Department budget for FY {budget.financial_year} received final approval from CEO.")
            
        budget.approved_by = user
        budget.save()
        messages.success(request, f'Department Budget marked as {budget.status}.')

    return redirect('approval_list')

@login_required
def budget_report(request):
    user = request.user
    if user.role == 'HOD':
        budgets = DepartmentBudget.objects.filter(department=user.department)
    elif user.role in ['Principal', 'CEO']:
        budgets = DepartmentBudget.objects.all()
    else:
        return redirect('dashboard')
        
    return render(request, 'budget/budget_report.html', {'budgets': budgets})

@login_required
def log_expense(request, alloc_id):
    alloc = get_object_or_404(SectionAllocation, id=alloc_id)
    
    if request.method == 'POST':
        try:
            amount = Decimal(request.POST.get('amount', '0'))
        except (ValueError, TypeError, InvalidOperation):
            messages.error(request, 'Invalid amount provided.')
            return redirect('budget_overview')
            
        description = request.POST.get('description', '')
        
        if alloc.department_budget.status not in ['Principal_Approved', 'CEO_Approved']:
            messages.error(request, 'You cannot log expenses against an unapproved budget.')
        elif amount <= 0:
            messages.error(request, 'Expense amount must be greater than zero.')
        elif amount > alloc.remaining_budget:
            messages.error(request, 'Expense exceeds the remaining allocated budget for this section.')
        else:
            from .models import ExpenseTransaction
            ExpenseTransaction.objects.create(
                allocation=alloc,
                amount=amount,
                description=description,
                recorded_by=request.user
            )
            alloc.amount_spent += amount
            alloc.save()
            messages.success(request, f'Successfully logged ₹{amount} expense for {alloc.category.name}.')
            return redirect('budget_overview')
            
    return render(request, 'budget/log_expense.html', {'alloc': alloc})

@login_required
def transaction_logs(request):
    from .models import ExpenseTransaction
    from django.core.paginator import Paginator
    from django.db.models import Q
    from users.models import Department
    
    user = request.user
    if user.role == 'HOD':
        transactions = ExpenseTransaction.objects.filter(allocation__department_budget__department=user.department).order_by('-date')
    elif user.role in ['Principal', 'CEO']:
        transactions = ExpenseTransaction.objects.all().order_by('-date')
    else:
        return redirect('dashboard')
        
    query = request.GET.get('q', '')
    dept_filter = request.GET.get('department', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    if query:
        transactions = transactions.filter(
            Q(description__icontains=query) |
            Q(allocation__department_budget__department__name__icontains=query) |
            Q(recorded_by__username__icontains=query)
        )
    if dept_filter:
        transactions = transactions.filter(allocation__department_budget__department_id=dept_filter)
    if date_from:
        transactions = transactions.filter(date__date__gte=date_from)
    if date_to:
        transactions = transactions.filter(date__date__lte=date_to)
        
    departments = Department.objects.all().order_by('name')
    paginator = Paginator(transactions, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
        
    return render(request, 'budget/transaction_logs.html', {
        'page_obj': page_obj,
        'query': query,
        'dept_filter': dept_filter,
        'date_from': date_from,
        'date_to': date_to,
        'departments': departments,
    })

@login_required
def export_budget_csv(request):
    import csv
    from django.http import HttpResponse
    user = request.user
    if user.role == 'HOD':
        budgets = DepartmentBudget.objects.filter(department=user.department)
    elif user.role in ['Principal', 'CEO']:
        budgets = DepartmentBudget.objects.all()
    else:
        return redirect('dashboard')
        
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="budget_report.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Department', 'Financial Year', 'Status', 'Total Allocated', 'Total Spent'])
    
    for b in budgets:
        writer.writerow([
            b.department.name,
            b.financial_year,
            b.status,
            b.total_allocated,
            b.total_spent
        ])
    return response

@login_required
def transaction_detail(request, pk):
    from .models import ExpenseTransaction
    transaction = get_object_or_404(ExpenseTransaction, id=pk)
    # Permission: HOD of dept, Principal, CEO
    can_view = False
    if request.user.role == 'HOD' and request.user.department == transaction.allocation.department_budget.department:
        can_view = True
    elif request.user.role in ['Principal', 'CEO']:
        can_view = True
        
    if not can_view:
        messages.error(request, 'You do not have permission to view this transaction record.')
        return redirect('dashboard')
        
    return render(request, 'budget/transaction_detail.html', {'transaction': transaction})

@login_required
def budget_detail(request, pk):
    budget = get_object_or_404(DepartmentBudget, id=pk)
    # Permission: HOD of dept, Principal, CEO
    can_view = False
    if request.user.role == 'HOD' and request.user.department == budget.department:
        can_view = True
    elif request.user.role in ['Principal', 'CEO']:
        can_view = True
        
    if not can_view:
        messages.error(request, 'You do not have permission to view this budget report.')
        return redirect('dashboard')
        
    return render(request, 'budget/budget_detail.html', {'budget': budget})
