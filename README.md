# Department Budget and Stationery Stock Management System (STM-SYS) 🏢📊📦

A role-based Django web application for managing departmental budgets, stationery inventory, approval workflows, expense tracking, and institutional reporting.

## ✨ Core Capabilities

- Role-based access control for `Staff`, `HOD`, `Principal`, and `CEO`
- Multi-stage stationery request approvals
- Department budget creation, category-wise allocation, and approval workflow
- Expense logging against approved allocations with overspend protection
- Inventory management with restock/adjust operations
- Low-stock / critical-stock notification alerts
- Notification center in UI (with mark-as-read)
- Search, filter, and pagination for major listing screens
- CSV export for stock and budget reports
- Printable report/detail pages (template-based)

## 🛠️ Tech Stack

- Python 3.x
- Django 6.0.2
- SQLite (default)
- HTML templates + custom CSS/JS
- ReportLab (used by `generate_pdf.py` utility script)

## 🧩 Application Modules

- `users`: authentication, roles, departments, user management, notifications
- `stock`: stationery items, requests, approvals, issuing, inventory, reports
- `budget`: budget categories, department budgets, allocations, expense transactions
- `core`: project settings, root URLs, base templates, static assets, template filters

## 👥 Role Matrix

- `Staff`
- Submit stationery requests
- Track own request history and statuses

- `HOD`
- Approve/reject department stationery requests
- Create/allocate departmental budgets
- Log expenses (only when budget is approved)
- View stock and budget reports

- `Principal`
- Approve escalated stationery requests
- Approve/reject department budgets
- View institution-wide reports and logs

- `CEO`
- Final authority for stationery and budget approvals
- Manage departments and users
- Global audit/report visibility

## 🔄 Approval Flows

### Stationery Request 📝

`Pending -> HOD_Approved -> Principal_Approved -> CEO_Approved -> Issued`

Possible alternate terminal state: `Rejected`

### Budget Approval 💰

`Pending -> Principal_Approved -> CEO_Approved`

Possible alternate terminal state: `Rejected`

## 🗂️ Data Model Overview

- `Department`
- `CustomUser` (extends Django `AbstractUser`, includes `role`, `department`)
- `Notification`
- `StationeryItem` (`total_stock`, `reorder_threshold`)
- `StationeryRequest` (status-based lifecycle)
- `BudgetCategory`
- `DepartmentBudget` (unique by `department + financial_year`)
- `SectionAllocation` (unique by `department_budget + category`)
- `ExpenseTransaction` (ordered newest first)

## 📁 Project Structure

```text
.
|- core/
|  |- settings.py
|  |- urls.py
|  |- templates/
|  |- static/
|- users/
|  |- models.py
|  |- views.py
|  |- urls.py
|  |- templates/users/
|- stock/
|  |- models.py
|  |- views.py
|  |- urls.py
|  |- templates/stock/
|- budget/
|  |- models.py
|  |- views.py
|  |- urls.py
|  |- templates/budget/
|- manage.py
|- seed_users.py
|- populate_data.py
|- seed_full.py
|- test_all_urls.py
|- CUSTOMIZATION_GUIDE.md
```

## 🚀 Quick Start (Local)

1. Create and activate a virtual environment.

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

2. Install dependencies.

```powershell
pip install django reportlab
```

3. Apply migrations.

```powershell
python manage.py migrate
```

4. Create admin manually (optional if using seed scripts).

```powershell
python manage.py createsuperuser
```

5. Run the server.

```powershell
python manage.py runserver
```

6. Open:

- `http://127.0.0.1:8000/login/`

## 🌱 Seed / Demo Data Options

### Option A: Minimal users only

```powershell
python seed_users.py
```

Creates common test accounts such as `admin`, `principal`, `ceo` (passwords defined in script).

### Option B: Basic sample data

```powershell
python populate_data.py
```

Creates a few departments, users, stationery items, and budget categories.

### Option C: Full historical dataset

```powershell
python seed_full.py
```

Populates:

- Multiple departments
- HOD and staff users
- Large stationery inventory
- Budget categories
- Department budgets (FY 2016-2017 through FY 2026-2027)
- Allocations, expense transactions, stationery requests, notifications

## ⚙️ Useful Management Commands

```powershell
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
python manage.py test
```

## 🌐 URL Groups

- Auth and dashboard: `/login/`, `/logout/`, `/`
- User management: `/manage/departments/`, `/manage/users/`
- Stock module: `/stock/request/`, `/stock/my-requests/`, `/stock/approvals/`, `/stock/inventory/`, `/stock/report/`
- Budget module: `/budget/enter/`, `/budget/overview/`, `/budget/report/`, `/budget/transactions/`

## 📤 Reports and Exports

- Stock CSV export: `/stock/export/`
- Budget CSV export: `/budget/export/`
- Detail pages for request, transaction, and budget support printing/report presentation in templates

## 🔔 Notifications

System-generated notifications are created for events such as:

- Request approval/rejection updates
- Budget approval/rejection updates
- Low/critical/out-of-stock alerts

Users can mark notifications as read from the topbar dropdown.

## 🎨 Customization

Refer to [`CUSTOMIZATION_GUIDE.md`](CUSTOMIZATION_GUIDE.md) for institutional branding updates:

- Sidebar institution name/logo text
- Report headers/footers and management labels
- Login page branding
- Seed defaults (`seed_full.py`)

## 📄 Utility Script

`generate_pdf.py` is a standalone ReportLab script that generates a PDF manual/architecture document:

```powershell
python generate_pdf.py
```

## ✅ Testing

- Django test suites exist in app-level `tests.py`
- URL smoke utility script:

```powershell
python test_all_urls.py
```

Note: `test_all_urls.py` expects specific seeded users to exist.

## ⚠️ Important Notes

- `core/settings.py` currently uses development defaults (`DEBUG=True`, SQLite, inline secret key).
- Before production use, update:
- `SECRET_KEY`
- `DEBUG=False`
- `ALLOWED_HOSTS`
- Production database and static/media serving strategy
- A proper dependency lock file (`requirements.txt` or equivalent)

## 📜 License

No license file is currently present in this repository. Add one if distribution/use terms are needed.
