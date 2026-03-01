# Institutional Customization Guide

This document explains how to customize the institution's identity (Name, Logo, and Address) throughout the **STM-SYS** application.

## 1. Institution Name & Logo (Sidebar)

To change the name and the "logo" text displayed in the sidebar:
- **File:** `core/templates/base.html`
- **Location:** Look for the `<div class="sidebar-logo">` tag.
- **Action:** Update the text inside the `<span>` and the prefix (e.g., `INST`).

## 2. Report Headers & Footers (Printing)

When generating PDFs or printing reports (Stock, Budget, Transactions), the header and footer display institutional details.
- **Files:**
  - `stock/templates/stock/stock_report.html`
  - `stock/templates/stock/request_detail.html`
  - `budget/templates/budget/transaction_detail.html`
  - `budget/templates/budget/budget_report.html`
  - `budget/templates/budget/budget_detail.html`
- **Action:** 
  - Update the `<span>` inside `.sidebar-logo` for the header.
  - Update the address in the `<p class="text-muted mt-2">` tag.
  - Update management names/titles in the footer (usually a `<p>` tag with "Management:").

## 3. Login Page

- **File:** `users/templates/users/login.html`
- **Action:** Update the institutional name in the header/logo section.

## 4. Seed Data (Development)

To change the default users and department structures for clean installations:
- **File:** `seed_full.py` (Root directory)
- **Action:** Update the `DEPT_NAMES` list and the default usernames/emails in Section 2.
