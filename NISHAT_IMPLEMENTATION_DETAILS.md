# Nishat Part - Implementation Details

This document explains the implementation for these requirements:

1. Users can sign in and register with email/password.
2. Authentication uses Django built-in auth.
3. Passwords are hashed (not stored as plain text).
4. Role-based access separates normal users and admins.
5. Admins can review incidents and take decisions (approve/reject/request clarification).
6. Normal users can report incidents, see only their incidents, and comment.
7. Admin decisions are documented in the system.

Date checked: March 6, 2026.

---

## 1) Authentication and Registration (Email + Password)

### File: `BanglaCERT/accounts/forms.py`

#### A) Registration form

- Line 4: `UserCreationForm` is used so Django handles password rules and hashing automatically.
- Line 10: `UserRegistrationForm` extends Django's form instead of rebuilding auth logic.
- Line 11: Optional `full_name` is added for profile quality.
- Line 12: Required `email` enforces email-based registration.
- Lines 14-16: Form `Meta` binds to Django `User` model and limits input to `email/password1/password2`.
- Lines 18-44: `__init__` sets placeholders/autocomplete for usability and browser-safe password handling.
- Lines 46-52: `clean_email()` normalizes email (`strip().lower()`), rejects empty values, blocks duplicates (`email__iexact`) for case-insensitive uniqueness.
- Lines 54-64: `_build_unique_username()` creates a valid unique username from email local-part because Django auth still requires a unique username field.
- Lines 66-78: `save()` calls parent save with `commit=False`, sets normalized email + generated username, splits `full_name` into first/last names, then saves.

Why this design:
- Reuses secure built-in password flow.
- Prevents duplicate emails.
- Keeps compatibility with Django's username-based backend while letting users type email.

#### B) Login form (email or username)

- Line 81: `EmailLoginForm` handles login data separately from registration.
- Line 82: Field named `email` accepts email or username.
- Line 83: Password uses `PasswordInput` so input is masked.
- Lines 87-90: Stores `request` and a user cache for validated login.
- Lines 91-102: Adds useful placeholders/autocomplete metadata.
- Lines 104-110: `clean()` exits early if any required value is missing.
- Lines 112-115: Resolves user by username first, then email (both case-insensitive).
- Lines 116-117: Invalid identifier returns a generic error to avoid account enumeration details.
- Lines 119-123: Calls Django `authenticate()` (built-in auth backend path).
- Lines 124-127: Invalid/inactive users are rejected.
- Line 129: Stores authenticated user in `self.user_cache`.
- Lines 132-133: `get_user()` returns validated user to the view.

Why this design:
- Supports both email and username sign-in.
- Keeps authentication in Django's standard mechanism (`authenticate`).
- Preserves secure error behavior.

### File: `BanglaCERT/accounts/views.py`

#### C) Login and register flow

- Lines 8-11: `_redirect_by_role()` routes staff to admin dashboard (`admin:index`) and normal users to `incidents:my_incidents`.
- Lines 14-17: `login_view()` sends already logged-in users directly to the correct area.
- Lines 18-20: POST login binds `EmailLoginForm`.
- Lines 20-24: On valid credentials, uses Django `login()` to start session, shows success message, redirects by role.
- Lines 25-27: GET request shows empty login form.
- Lines 30-33: `register()` also redirects already-authenticated users by role.
- Lines 34-37: Valid registration creates user through `UserRegistrationForm.save()`.
- Lines 39-41: Hard-sets public registrations as non-admin (`is_staff=False`, `is_superuser=False`) for RBAC safety.
- Lines 42-44: Logs in new user and redirects to normal-user incidents area.

Why this design:
- Keeps role routing consistent.
- Prevents privilege escalation through open registration.
- Uses Django session auth without custom session logic.

### Password hashing proof

1. `UserCreationForm` (accounts/forms.py:4, 10) calls Django's secure password set flow.
2. Test assertion in `accounts/tests.py`:
   - Line 24: Stored password is not plain text.
   - Line 25: `check_password()` validates correct hashing behavior.
3. Django auth stack is enabled in settings (`django.contrib.auth` app + middleware).

---

## 2) Role-Based Access Control (Admin vs Normal User)

### File: `BanglaCERT/incidents/views.py`

#### D) Portal endpoint restrictions for normal users

- Line 14: `@login_required` protects home route.
- Lines 16-18: Staff users are redirected to Django admin; normal users continue in user portal.
- Lines 21-25: Staff cannot submit incident reports from user endpoint.
- Lines 27-34: Normal user report flow creates incident and sets `created_by=request.user`.
- Lines 40-43: Staff blocked from "My Incidents".
- Line 45: Query filtered to `created_by=request.user`, enforcing per-user visibility.
- Lines 49-52: Staff blocked from incident detail page in user portal.
- Line 54: `get_incident_for_user()` returns 404 if incident does not belong to current user.
- Lines 68-71: Comment endpoint is POST-only.
- Lines 73-74: Staff blocked from comment endpoint.
- Line 76: Same ownership check before commenting.
- Lines 79-83: Comment is saved with incident + creator and marked `is_admin_note=False`.

Why this design:
- Enforces least privilege at view layer.
- Prevents horizontal access to other users' records.
- Ensures normal-user comments are distinguishable from admin notes.

### File: `BanglaCERT/accounts/views.py`

#### E) Role-aware navigation entry point

- Lines 8-11: Single helper centralizes role redirects.
- Lines 16, 24, 32: Both login and register flows consistently use role logic.

Why this design:
- Avoids role drift from duplicated redirect code.

### File: `BanglaCERT/templates/base/site.html`

#### F) UI-level role separation

- Lines 29-31: Normal users see "Report Incident" and "My Reports".
- Lines 33-34: Staff users see "Admin Dashboard" link.
- Lines 37-47: Authenticated vs anonymous navigation shown correctly.

Why this design:
- Makes role boundaries visible in UI, not only backend checks.

---

## 3) Admin Review/Decision Workflow + Documentation of Decisions

### File: `BanglaCERT/incidents/models.py`

#### G) Incident status lifecycle

- Lines 6-11: Status constants define business states.
- Lines 13-20: `STATUS_CHOICES` provides human-readable status values.
- Line 34: Default new incident status is `PENDING`.
- Lines 35-37: `created_by` tracks reporter identity.

Why this design:
- Encodes admin workflow states in data model.
- Preserves reporter ownership.

### File: `BanglaCERT/auditlog/models.py`

#### H) Decision logging model

- Lines 6-11: Action constants represent create/update/review/clarification/approve/reject.
- Lines 13-20: Action choice labels for admin display.
- Lines 22-24: Actor (`user`) is stored with nullable FK for resilience if user is deleted.
- Lines 25-29: Action + target (`object_type`, `object_id`) + message + timestamp persist decision metadata.

Why this design:
- Creates an immutable audit trail structure for admin decisions.

### File: `BanglaCERT/incidents/admin.py`

#### I) Admin actions and audit writes

- Lines 18-25: `log_admin_action()` writes one audit row per event.
- Lines 28-37: `get_status_action()` maps incident status to audit action type.
- Lines 44-53: `build_audit_message()` attaches actor + timestamp context.
- Lines 55-62: `build_status_change_message()` includes before/after status text.
- Lines 65-68: `log_status_change()` is a reusable status-change logger.

- Lines 71-78: `approve_incidents` bulk action sets status `VERIFIED` and logs.
- Lines 80-87: `mark_under_review` sets `UNDER_REVIEW` and logs.
- Lines 89-96: `reject_incidents` sets `REJECTED` and logs.
- Lines 98-105: `request_clarification_incidents` sets `NEEDS_CLARIFICATION` and logs.

Why this design:
- Guarantees every admin decision writes an audit entry.
- Supports both single-edit and bulk action workflows.

#### J) Admin permission boundaries

- Lines 165-167: No incident creation from admin (`has_add_permission=False`).
- Lines 169-171: Staff can change incidents.
- Lines 173-175: Delete restricted to specific incident manager username.
- Lines 177-179: Staff can view incidents.

Why this design:
- Admins are focused on review/decision flow, not creating user incidents.
- Deletes are tightly controlled.

#### K) In-admin audit visibility

- Lines 181-205: `audit_log_entries()` renders latest 20 logs for incident inside admin detail view.
- Lines 208-232: `save_model()` logs:
  - create event on new object,
  - status-change action when status changes,
  - generic update otherwise.

Why this design:
- Decision history is visible where admins work.
- Manual field edits are also auditable.

### File: `BanglaCERT/auditlog/admin.py`

#### L) Read-only audit viewer

- Lines 25-33: add/change/delete are disabled in audit admin.
- Line 35: only staff can view logs.
- Lines 37-54: incident metadata and clickable incident link in logs.
- Lines 56-65: shows actor and localized timestamp fields.

Why this design:
- Audit data cannot be tampered with through admin UI.
- Enables review traceability.

---

## 4) Verification (Tests)

### File: `BanglaCERT/accounts/tests.py`

- Lines 10-27: Registration test confirms:
  - user created,
  - non-staff/non-superuser,
  - password not stored in plain text,
  - hash checks correctly,
  - user logged in.
- Lines 28-46: Duplicate email registration blocked.
- Lines 47-77: Staff login redirects to `/admin/` (email and username cases).
- Lines 79-92: Normal login redirects to `/incidents/mine/`.

### File: `BanglaCERT/incidents/tests.py`

- Lines 23-39: Normal users can report incidents; status starts `PENDING`.
- Lines 40-61: Users cannot view incidents of others (404).
- Lines 63-85: Staff are redirected to admin from user-portal endpoints.
- Lines 87-116: Users can comment only on their own incidents.
- Lines 118-135: Staff cannot comment through user endpoint.

### Test execution used

```bash
source .venv/bin/activate
python BanglaCERT/manage.py test accounts incidents --settings=BanglaCERT.settings_test -v 2
```

Result: 10/10 tests passed.

---

## 5) Requirement-to-Code Traceability

1. "Users sign in/register with email+password":
   - `accounts/forms.py` (`UserRegistrationForm`, `EmailLoginForm`)
   - `accounts/views.py` (`login_view`, `register`)
2. "Use Django built-in auth":
   - `authenticate()` + `login()` in accounts form/view
   - `UserCreationForm` for registration/password handling
3. "Passwords hashed":
   - inherited Django `UserCreationForm` behavior
   - test proof in `accounts/tests.py` lines 24-25
4. "Role-based admin vs normal":
   - `is_staff` checks in accounts/incidents views
   - role redirect helper `_redirect_by_role`
   - role-based navigation in `templates/base/site.html`
5. "Admins can review/approve/reject/request clarification/manage records":
   - `incidents/admin.py` actions + `ModelAdmin` controls
6. "Ordinary users report/view own/comment":
   - `incidents/views.py` ownership filtering and comment flow
7. "Admin decisions documented":
   - `auditlog/models.py` persistence
   - `incidents/admin.py` logging hooks
   - `auditlog/admin.py` read-only viewer
