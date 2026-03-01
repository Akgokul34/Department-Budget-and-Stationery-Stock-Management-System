from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, F, Sum
from django.contrib import messages
from .models import StationeryItem, StationeryRequest
from users.models import Department
from budget.models import DepartmentBudget

@login_required
def request_item(request):
    items = StationeryItem.objects.all()
    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        if not item_id:
            messages.error(request, 'Please select an item.')
            return redirect('request_item')
            
        try:
            quantity = int(request.POST.get('quantity', 0))
        except (ValueError, TypeError):
            messages.error(request, 'Invalid quantity provided.')
            return redirect('request_item')
        
        if quantity <= 0:
            messages.error(request, 'Quantity must be greater than zero.')
            return redirect('request_item')

        try:
            item = StationeryItem.objects.get(id=item_id)
        except (ValueError, TypeError, StationeryItem.DoesNotExist):
            messages.error(request, 'Selected item is invalid.')
            return redirect('request_item')
        
        req = StationeryRequest.objects.create(
            user=request.user,
            item=item,
            quantity=quantity,
            status='Pending'
        )
        # Notify HOD
        from users.models import CustomUser, Notification
        hods = CustomUser.objects.filter(department=request.user.department, role='HOD')
        for hod in hods:
            Notification.objects.create(user=hod, message=f"New stationery request from {request.user.username} for {quantity} {item.name}.")
            
        messages.success(request, f'Request for {quantity} {item.name}(s) submitted successfully.')
        return redirect('dashboard')
        
    return render(request, 'stock/request_item.html', {'items': items})

@login_required
def approval_list(request):
    from django.core.paginator import Paginator
    from users.models import CustomUser, Notification
    
    user = request.user
    budget_requests = []
    
    # --- Bulk Actions Handle ---
    if request.method == 'POST':
        action = request.POST.get('action')
        request_ids = request.POST.getlist('request_ids')
        
        if request_ids and action in ['bulk_approve', 'bulk_reject']:
            reqs = StationeryRequest.objects.filter(id__in=request_ids)
            count = 0
            for req in reqs:
                if action == 'bulk_reject':
                    req.status = 'Rejected'
                    req.approved_by = user
                    req.save()
                    Notification.objects.create(user=req.user, message=f"Your request for {req.item.name} was rejected by {user.role}.")
                    count += 1
                elif action == 'bulk_approve':
                    if user.role == 'HOD':
                        req.status = 'HOD_Approved'
                        Notification.objects.create(user=req.user, message=f"Your request for {req.item.name} was approved by HOD. Awaiting Principal.")
                        principals = CustomUser.objects.filter(role='Principal')
                        for p in principals:
                            Notification.objects.create(user=p, message=f"New HOD-approved stationery request from {req.user.department.name} awaiting your approval.")
                    elif user.role == 'Principal':
                        req.status = 'Principal_Approved'
                        Notification.objects.create(user=req.user, message=f"Your request for {req.item.name} was approved by Principal.")
                        if req.approved_by:
                            Notification.objects.create(user=req.approved_by, message=f"The request you approved for {req.item.name} was also approved by Principal.")
                    elif user.role == 'CEO':
                        req.status = 'CEO_Approved'
                        Notification.objects.create(user=req.user, message=f"Your request for {req.item.name} received final approval from CEO.")
                    req.approved_by = user
                    req.save()
                    count += 1
                    
            if action == 'bulk_approve':
                messages.success(request, f'Successfully approved {count} requests.')
            else:
                messages.info(request, f'Successfully rejected {count} requests.')
                
            return redirect('approval_list')
    # -------------------------

    status_filter = request.GET.get('status', '')
    dept_filter = request.GET.get('department', '')
    search_query = request.GET.get('q', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    if user.role == 'HOD':
        requests = StationeryRequest.objects.filter(user__department=user.department).order_by('-request_date')
        role_view = 'HOD'
    elif user.role == 'Principal':
        requests = StationeryRequest.objects.filter(status__in=['HOD_Approved', 'Principal_Approved', 'Rejected', 'CEO_Approved', 'Issued']).order_by('-request_date')
        budget_requests = DepartmentBudget.objects.filter(status='Pending')
        role_view = 'Principal'
    elif user.role == 'CEO':
        requests = StationeryRequest.objects.all().order_by('-request_date')
        budget_requests = DepartmentBudget.objects.all().order_by('-financial_year')
        role_view = 'CEO'
    else:
        return redirect('my_requests')
        
    # Apply multi-filters
    if status_filter:
        requests = requests.filter(status=status_filter)
    if dept_filter:
        requests = requests.filter(user__department_id=dept_filter)
    if search_query:
        requests = requests.filter(
            Q(user__username__icontains=search_query) |
            Q(item__name__icontains=search_query)
        )
    if date_from:
        requests = requests.filter(request_date__date__gte=date_from)
    if date_to:
        requests = requests.filter(request_date__date__lte=date_to)
        
    # Pagination
    paginator = Paginator(requests, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get all departments for filter dropdown
    from users.models import Department
    departments = Department.objects.all().order_by('name')
        
    return render(request, 'stock/approval_list.html', {
        'page_obj': page_obj, 
        'budget_requests': budget_requests, 
        'role_view': role_view,
        'status_filter': status_filter,
        'dept_filter': dept_filter,
        'search_query': search_query,
        'date_from': date_from,
        'date_to': date_to,
        'departments': departments,
    })

@login_required
def my_requests(request):
    from django.core.paginator import Paginator
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('q', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    requests = StationeryRequest.objects.filter(user=request.user).order_by('-request_date')
    if status_filter:
        requests = requests.filter(status=status_filter)
    if search_query:
        requests = requests.filter(item__name__icontains=search_query)
    if date_from:
        requests = requests.filter(request_date__date__gte=date_from)
    if date_to:
        requests = requests.filter(request_date__date__lte=date_to)
        
    paginator = Paginator(requests, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'stock/my_requests.html', {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'search_query': search_query,
        'date_from': date_from,
        'date_to': date_to,
    })


@login_required
def process_request(request, req_id):
    req = get_object_or_404(StationeryRequest, id=req_id)
    action = request.POST.get('action')
    user = request.user
    
    if action == 'reject':
        req.status = 'Rejected'
        req.approved_by = user
        req.save()
        
        from users.models import Notification
        Notification.objects.create(user=req.user, message=f"Your request for {req.item.name} was rejected by {user.role}.")
        
        messages.info(request, 'Request rejected.')
        return redirect('approval_list')
        
    if action == 'approve':
        from users.models import CustomUser, Notification
        if user.role == 'HOD':
            req.status = 'HOD_Approved'
            Notification.objects.create(user=req.user, message=f"Your request for {req.item.name} was approved by HOD. Awaiting Principal.")
            # Notify Principals
            principals = CustomUser.objects.filter(role='Principal')
            for p in principals:
                Notification.objects.create(user=p, message=f"New HOD-approved stationery request from {req.user.department.name} awaiting your approval.")
                
        elif user.role == 'Principal':
            req.status = 'Principal_Approved'
            Notification.objects.create(user=req.user, message=f"Your request for {req.item.name} was approved by Principal.")
            if req.approved_by:
                Notification.objects.create(
                    user=req.approved_by,
                    message=f"The request you approved for {req.item.name} was also approved by Principal."
                ) # notify HOD
            
        elif user.role == 'CEO':
            req.status = 'CEO_Approved'
            Notification.objects.create(user=req.user, message=f"Your request for {req.item.name} received final approval from CEO.")
            
        req.approved_by = user
        req.save()
        messages.success(request, f'Request marked as {req.status}.')

    return redirect('approval_list')

@login_required
def issue_request(request, req_id):
    req = get_object_or_404(StationeryRequest, id=req_id)
    # Check if authorized to issue (e.g. HOD or anyone designated)
    if request.user.role in ['HOD', 'Principal', 'CEO']:
        if req.item.total_stock >= req.quantity:
            old_stock = req.item.total_stock
            req.item.total_stock -= req.quantity
            req.item.save()
            req.status = 'Issued'
            req.save()
            messages.success(request, f'Stock issued successfully! {req.quantity} subtracted from {req.item.name}.')
            
            # Low stock notification check
            new_stock = req.item.total_stock
            threshold = req.item.reorder_threshold
            
            # Trigger IF stock newly crosses threshold, OR hits exactly 1, OR hits exactly 0
            is_newly_low = (old_stock > threshold and new_stock <= threshold)
            is_critical = (new_stock == 1 and old_stock != 1) or (new_stock == 0 and old_stock != 0)
            
            if is_newly_low or is_critical:
                from users.models import CustomUser, Notification
                notify_users = CustomUser.objects.filter(role__in=['HOD', 'Principal', 'CEO'])
                
                if new_stock == 0:
                    alert_type = "OUT OF STOCK"
                elif new_stock == 1:
                    alert_type = "CRITICAL STOCK"
                else:
                    alert_type = "Low Stock Alert"
                
                for u in notify_users:
                    Notification.objects.create(
                        user=u, 
                        message=f"{alert_type}: {req.item.name} has dropped to {new_stock} units. Please restock soon.",
                        action_url=f"/stock/inventory/?adjust_item={req.item.id}"
                    )
        else:
            messages.error(request, 'Not enough stock available to issue.')
    else:
        messages.error(request, 'You do not have permission to issue stock.')
    return redirect('approval_list')

@login_required
def inventory_list(request):
    from django.core.paginator import Paginator
    from django.db.models import Q, F
    
    query = request.GET.get('q', '')
    stock_level = request.GET.get('stock_level', '')
    adjust_item_id = request.GET.get('adjust_item', '')
    items = StationeryItem.objects.all().order_by('name')
    
    if query:
        items = items.filter(
            Q(name__icontains=query) |
            Q(category__icontains=query)
        )
        
    if stock_level == 'Low':
        items = items.filter(total_stock__lte=F('reorder_threshold'))
    elif stock_level == 'Adequate':
        items = items.filter(total_stock__gt=F('reorder_threshold'))
        
    paginator = Paginator(items, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    auto_adjust_item = StationeryItem.objects.filter(id=adjust_item_id).first() if adjust_item_id else None
    
    return render(request, 'stock/inventory_list.html', {
        'page_obj': page_obj, 
        'query': query,
        'stock_level': stock_level,
        'auto_adjust_item': auto_adjust_item,
    })

@login_required
def stock_report(request):
    user = request.user
    if user.role not in ['HOD', 'Principal', 'CEO']:
        return redirect('dashboard')
        
    # --- Inventory Filters ---
    inv_q = request.GET.get('inv_q', '')
    inv_stock = request.GET.get('inv_stock', '')
    
    items = StationeryItem.objects.all().order_by('name')
    if inv_q:
        items = items.filter(
            Q(name__icontains=inv_q) |
            Q(category__icontains=inv_q)
        )
    if inv_stock == 'Low':
        items = items.filter(total_stock__lte=F('reorder_threshold'))
    elif inv_stock == 'Adequate':
        items = items.filter(total_stock__gt=F('reorder_threshold'))

    # Stat card data (computed from filtered items)
    total_items = items.count()
    low_stock_count = items.filter(total_stock__lte=F('reorder_threshold')).count()
    total_stock_units = items.aggregate(total=Sum('total_stock'))['total'] or 0

    items_paginator = Paginator(items, 10)
    items_page = items_paginator.get_page(request.GET.get('items_page'))

    # --- Consumption Filters ---
    cons_dept = request.GET.get('cons_dept', '')
    cons_status = request.GET.get('cons_status', '')
    
    recent_requests = StationeryRequest.objects.exclude(status='Pending').order_by('-request_date')
    
    if user.role == 'HOD':
        # HODs only see their department's requests
        recent_requests = recent_requests.filter(user__department=user.department)
        departments = Department.objects.filter(id=user.department_id)
    else:
        departments = Department.objects.all().order_by('name')
        if cons_dept:
            recent_requests = recent_requests.filter(user__department_id=cons_dept)
            
    if cons_status:
        recent_requests = recent_requests.filter(status=cons_status)

    requests_paginator = Paginator(recent_requests, 10)
    requests_page = requests_paginator.get_page(request.GET.get('req_page'))

    # Status choices for filter
    status_choices = [
        ('HOD_Approved', 'HOD Approved'),
        ('Principal_Approved', 'Principal Approved'),
        ('CEO_Approved', 'CEO Approved'),
        ('Rejected', 'Rejected'),
        ('Issued', 'Issued'),
    ]

    return render(request, 'stock/stock_report.html', {
        # Inventory Context
        'items_page': items_page,
        'items_total_pages': items_paginator.num_pages,
        'inv_q': inv_q,
        'inv_stock': inv_stock,
        
        # Consumption Context
        'requests_page': requests_page,
        'requests_total_pages': requests_paginator.num_pages,
        'cons_dept': cons_dept,
        'cons_status': cons_status,
        'departments': departments,
        'status_choices': status_choices,
        
        # Stats
        'total_items': total_items,
        'low_stock_count': low_stock_count,
        'total_stock_units': total_stock_units,
    })

@login_required
def restock_item(request, item_id):
    if request.user.role not in ['HOD', 'Principal', 'CEO']:
        messages.error(request, 'You do not have permission to restock items.')
        return redirect('dashboard')
        
    item = get_object_or_404(StationeryItem, id=item_id)
    
    if request.method == 'POST':
        try:
            add_quantity = int(request.POST.get('quantity', 0))
        except (ValueError, TypeError):
            messages.error(request, 'Invalid quantity provided.')
            return redirect('inventory_list')
            
        if add_quantity == 0:
            messages.error(request, 'Quantity cannot be zero. Please enter a positive or negative amount.')
            return redirect('inventory_list')
        if item.total_stock + add_quantity < 0:
            messages.error(request, f'Error: Cannot reduce stock below 0. Current stock is {item.total_stock}.')
            return redirect('inventory_list')
        else:
            old_stock = item.total_stock
            item.total_stock += add_quantity
            item.save()
            
            # Low stock notification check (trigger if they subtracted stock)
            new_stock = item.total_stock
            threshold = item.reorder_threshold
            
            # Only alert if stock newly dropped below threshold, or hit exactly 1, or hit exactly 0
            is_newly_low = (old_stock > threshold and new_stock <= threshold)
            is_critical = (new_stock == 1 and old_stock != 1) or (new_stock == 0 and old_stock != 0)
            
            if add_quantity < 0 and (is_newly_low or is_critical):
                from users.models import CustomUser, Notification
                notify_users = CustomUser.objects.filter(role__in=['HOD', 'Principal', 'CEO'])
                
                if new_stock == 0:
                    alert_type = "OUT OF STOCK"
                elif new_stock == 1:
                    alert_type = "CRITICAL STOCK"
                else:
                    alert_type = "Low Stock Alert"
                
                for u in notify_users:
                    Notification.objects.create(
                        user=u, 
                        message=f"{alert_type}: {item.name} has dropped to {new_stock} units after adjustment.",
                        action_url=f"/stock/inventory/?adjust_item={item.id}"
                    )
                    
            action = "Added" if add_quantity > 0 else "Removed"
            messages.success(request, f'Successfully {action.lower()} {abs(add_quantity)} units for {item.name}. New total: {item.total_stock}.')
            return redirect('inventory_list')
            
    # If we get a GET request (e.g. from an old notification link), 
    # redirect to the inventory list with the adjust_item parameter 
    # to trigger the auto-modal popup.
    return redirect(f"/stock/inventory/?adjust_item={item.id}")

@login_required
def export_stock_csv(request):
    import csv
    from django.http import HttpResponse
    if request.user.role not in ['HOD', 'Principal', 'CEO']:
        return redirect('dashboard')
        
    items = StationeryItem.objects.all()
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="stock_inventory.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Item Name', 'Total Stock', 'Reorder Threshold'])
    
    for i in items:
        writer.writerow([
            i.name,
            i.total_stock,
            i.reorder_threshold
        ])
    return response

@login_required
def request_detail(request, pk):
    req = get_object_or_404(StationeryRequest, id=pk)
    # Check permissions: User who requested, HOD of their dept, Principal, or CEO
    can_view = False
    if request.user == req.user:
        can_view = True
    elif request.user.role == 'HOD' and request.user.department == req.user.department:
        can_view = True
    elif request.user.role in ['Principal', 'CEO']:
        can_view = True
        
    if not can_view:
        messages.error(request, 'You do not have permission to view this request.')
        return redirect('dashboard')
        
    return render(request, 'stock/request_detail.html', {'req': req})

@login_required
def add_stock_item(request):
    if request.user.role not in ['HOD', 'Principal', 'CEO']:
        messages.error(request, 'You do not have permission to add new items.')
        return redirect('inventory_list')
        
    if request.method == 'POST':
        name = (request.POST.get('name') or '').strip()
        description = request.POST.get('description', '')
        try:
            total_stock = int(request.POST.get('total_stock', 0))
            reorder_threshold = int(request.POST.get('reorder_threshold', 10))
        except (ValueError, TypeError):
            messages.error(request, 'Invalid stock values provided.')
            return redirect('inventory_list')
        
        if not name:
            messages.error(request, 'Item name is required.')
            return redirect('inventory_list')

        if total_stock < 0:
            messages.error(request, 'Initial stock cannot be negative.')
            return redirect('inventory_list')

        if reorder_threshold <= 0:
            messages.error(request, 'Reorder threshold must be greater than zero.')
            return redirect('inventory_list')
            
        if StationeryItem.objects.filter(name__iexact=name).exists():
            messages.error(request, f'An item with the name "{name}" already exists.')
            return redirect('inventory_list')
            
        StationeryItem.objects.create(
            name=name,
            description=description,
            total_stock=total_stock,
            reorder_threshold=reorder_threshold
        )
        messages.success(request, f'Successfully added new item: {name}.')
        return redirect('inventory_list')
        
    return redirect('inventory_list')

@login_required
def edit_stock_item(request, item_id):
    if request.user.role not in ['HOD', 'Principal', 'CEO']:
        messages.error(request, 'You do not have permission to edit items.')
        return redirect('inventory_list')
        
    item = get_object_or_404(StationeryItem, id=item_id)
    
    if request.method == 'POST':
        name = (request.POST.get('name') or '').strip()
        description = request.POST.get('description', '')
        # We don't change total_stock via edit, use Adjust for that
        try:
            reorder_threshold = int(request.POST.get('reorder_threshold', 10))
        except (ValueError, TypeError):
            messages.error(request, 'Invalid reorder threshold provided.')
            return redirect(request.META.get('HTTP_REFERER', 'inventory_list'))
        
        if not name:
            messages.error(request, 'Item name is required.')
            return redirect(request.META.get('HTTP_REFERER', 'inventory_list'))

        if reorder_threshold <= 0:
            messages.error(request, 'Reorder threshold must be greater than zero.')
            return redirect(request.META.get('HTTP_REFERER', 'inventory_list'))
            
        if StationeryItem.objects.filter(name__iexact=name).exclude(id=item_id).exists():
            messages.error(request, f'Another item with the name "{name}" already exists.')
            return redirect(request.META.get('HTTP_REFERER', 'inventory_list'))
            
        item.name = name
        item.description = description
        item.reorder_threshold = reorder_threshold
            
        item.save()
        messages.success(request, f'Successfully updated item: {name}.')
        return redirect(request.META.get('HTTP_REFERER', 'inventory_list'))
        
    return redirect(request.META.get('HTTP_REFERER', 'inventory_list'))
