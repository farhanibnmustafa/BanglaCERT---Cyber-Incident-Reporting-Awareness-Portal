# Shreya Feature Implementation README

## Goal
This document explains exactly how Shreya's two requirements were implemented:

1. Users can submit cyber incidents anonymously without login.
2. Users get email alerts whenever incident status changes, with async delivery when possible.

## Requirement Mapping

1. Anonymous report without login
- Public incident report endpoint was added.
- Reporter identity can be hidden (`is_anonymous=True`). 
- Personal user identity is not shown in anonymous reports (admin list shows `Anonymous`).

2. Status change email alerts
- On incident status update in admin, notification service runs.
- Recipient selection priority: `reporter_email` first, then `created_by.email`.
- Delivery mode:
`NOTIFICATION_EMAIL_ASYNC=false` -> synchronous (default reliable mode)
`NOTIFICATION_EMAIL_ASYNC=true` -> asynchronous (threaded) with sync fallback.

## Step-by-Step: What Was Done

1. Extended the `Incident` model with anonymity and reporter email fields.
2. Added a public report form for non-authenticated users.
3. Added report and success views and wired URLs.
4. Added simple templates for public reporting flow.
5. Added DB migration for new fields (safe for existing DB and new DB).
6. Updated incident admin to preserve anonymity and trigger status email.
7. Added notification service functions to build/send status emails.
8. Added SMTP/email settings and `.env` loading so VS Code and terminal both work.
9. Added admin warning messages when email is not sent (no silent failure).

## Files Changed for Shreya Feature

1. `BanglaCERT/incidents/models.py`
2. `BanglaCERT/incidents/forms.py`
3. `BanglaCERT/incidents/views.py`
4. `BanglaCERT/incidents/urls.py`
5. `BanglaCERT/incidents/templates/incidents/report_incident.html`
6. `BanglaCERT/incidents/templates/incidents/report_success.html`
7. `BanglaCERT/incidents/migrations/0002_incident_anonymous_and_reporter_email.py`
8. `BanglaCERT/notifications/services.py`
9. `BanglaCERT/incidents/admin.py`
10. `BanglaCERT/BanglaCERT/settings.py`

## Line-by-Line Explanation

Notes:
- Line numbers below refer to current files.
- Only lines related to Shreya feature are explained.

### 1) `BanglaCERT/incidents/models.py`

- Line 32: `is_anonymous = models.BooleanField(default=False)`  
Adds a flag to mark whether report should hide user identity.
- Line 33: `reporter_email = models.EmailField(blank=True)`  
Stores email for status update alerts.
- Line 44: `@property`  
Defines a computed property for display.
- Line 45: `def reporter_display_name(self) -> str:`  
Creates unified reporter name logic.
- Line 46: `if self.is_anonymous or not self.created_by:`  
If anonymous or no user linked, never show real username.
- Line 47: `return "Anonymous"`  
For privacy, display generic identity.
- Line 48: `return self.created_by.username`  
Otherwise show real creator username.

### 2) `BanglaCERT/incidents/forms.py`

- Line 1: `from django import forms`  
Imports Django form utilities.
- Line 3: `from .models import Incident`  
Uses `Incident` model for form mapping.
- Line 6: `class IncidentPublicReportForm(forms.ModelForm):`  
Defines public incident submission form.
- Line 7: `class Meta:`  
Configures model form options.
- Line 8: `model = Incident`  
Binds form to `Incident` model.
- Line 9: `fields = (...)`  
Exposes only fields needed for public reporting.
- Line 10: `widgets = {`  
Custom HTML input widgets.
- Line 11: date widget  
Shows browser date picker.
- Line 12: textarea widget  
Gives larger description input.
- Line 14: `labels = {`  
Improves user-friendly field labels.
- Line 15: reporter email label  
Clarifies purpose of email field.
- Line 16: anonymous label  
Makes anonymity choice explicit.
- Line 18: `help_texts = {`  
Extra helper text for noob-friendly UI.
- Line 19: help text string  
Explains email usage scope.
- Line 22: `def __init__(...)`  
Initializes form defaults.
- Line 23: `super().__init__...`  
Runs base form setup.
- Line 24: `is_anonymous` default true  
Privacy-first default behavior.
- Line 25: `reporter_email` required  
Ensures status email can be sent.

### 3) `BanglaCERT/incidents/views.py`

- Line 1: import `redirect, render`  
Needed for form page + success redirection.
- Line 3: import public form  
Uses newly added form class.
- Line 6: `def public_report_incident(request):`  
Public endpoint for incident reporting.
- Line 7: POST check  
Handles form submit case.
- Line 8: form bind with `request.POST`  
Reads submitted values.
- Line 9: `if form.is_valid():`  
Validation guard before save.
- Line 10: `form.save(commit=False)`  
Allows setting anonymity/creator before DB write.
- Line 11: check authenticated + not anonymous  
Only assign user when reporter is not anonymous.
- Line 12: `incident.created_by = request.user`  
Links reporter identity for non-anonymous case.
- Line 13: `else:`  
Anonymous or unauthenticated path.
- Line 14: `incident.created_by = None`  
Removes identity link.
- Line 15: `incident.is_anonymous = True`  
Enforces anonymous flag for safety.
- Line 16: `incident.save()`  
Persists incident.
- Line 17: redirect success  
Prevents form re-submit on refresh.
- Line 18: `else:` (GET request)  
Shows empty form.
- Line 19: `form = IncidentPublicReportForm()`  
Initial blank form.
- Line 21: render report template  
Returns report page.
- Line 24: `def public_report_success(request):`  
Simple success page endpoint.
- Line 25: render success template  
Returns confirmation page.

### 4) `BanglaCERT/incidents/urls.py`

- Line 3: `from . import views`  
Imports the new public report views.
- Line 7: URL list start  
Defines routes under `/incidents/`.
- Line 8: `report/` route  
Public submission URL.
- Line 9: `report/success/` route  
Post-submit confirmation URL.

### 5) `BanglaCERT/incidents/templates/incidents/report_incident.html`

- Lines 1-6: HTML document setup and title.
- Lines 7-72: page styling for clean public form.
- Line 76: page heading for report flow.
- Line 77: privacy note (no login + anonymous support).
- Line 78: form start.
- Line 79: `{% csrf_token %}` for CSRF security.
- Lines 81-85: title field label/input/errors.
- Lines 87-91: category field label/input/errors.
- Lines 93-97: description field label/input/errors.
- Lines 99-103: incident date field label/input/errors.
- Lines 105-110: reporter email field + helper note.
- Lines 112-116: anonymous checkbox + errors.
- Line 118: submit button.

### 6) `BanglaCERT/incidents/templates/incidents/report_success.html`

- Lines 1-6: HTML setup + page title.
- Lines 7-34: basic success page styling.
- Line 38: success heading.
- Line 39: submit success message.
- Line 40: email alert message.
- Line 41: link to submit another report.

### 7) `BanglaCERT/incidents/migrations/0002_incident_anonymous_and_reporter_email.py`

- Line 13: `SeparateDatabaseAndState`  
Separates SQL operations from Django model state operations.
- Lines 15-21: add `is_anonymous` column safely (`IF NOT EXISTS`).
- Lines 22-28: add `reporter_email` column safely (`IF NOT EXISTS`).
- Lines 29-35: remove temporary default for cleaner schema.
- Lines 38-42: reflect `is_anonymous` in Django state.
- Lines 43-47: reflect `reporter_email` in Django state.

### 8) `BanglaCERT/notifications/services.py`

- Line 1: imports `logging` for error logs.
- Line 2: imports `Thread` for optional async send.
- Lines 4-5: imports settings and Django send_mail.
- Line 8: module logger.
- Line 11: `_status_label(...)` helper starts.
- Line 12: converts status value to human readable label.
- Line 15: `_build_status_change_email(...)` starts.
- Lines 16-17: gets old/new labels.
- Line 18: creates email subject.
- Lines 19-27: creates email body text.
- Line 28: returns `(subject, message)`.
- Line 31: `_get_notification_email(...)` starts.
- Lines 32-33: prefer `reporter_email`.
- Lines 34-35: fallback to creator account email.
- Line 36: return empty if none exists.
- Line 39: `_send_status_change_email(...)` starts.
- Lines 40-46: calls Django SMTP send.
- Line 49: `_send_sync(...)` starts.
- Lines 50-52: sync send success path.
- Lines 53-55: sync send failure path with reason.
- Line 58: `_send_async(...)` starts.
- Lines 59-64: thread target function with logging.
- Lines 65-67: queue async thread success.
- Lines 68-70: async queue failure returns reason.
- Line 73: public helper with reason starts.
- Lines 74-75: no status change -> no email.
- Lines 77-79: no recipient -> no email.
- Line 81: build email content.
- Line 83: checks async mode config.
- Lines 84-87: async send then sync fallback if needed.
- Line 89: sync send default path.
- Line 92: backward-compatible bool wrapper.
- Lines 93-94: returns only success flag.

### 9) `BanglaCERT/incidents/admin.py` (Shreya-related lines only)

- Line 2: imports `messages` to show warning in admin UI.
- Line 7: imports notification service with reason text.
- Lines 70-75: wrapper to call notification service.
- Lines 85-91: show warning for failed email in approve action.
- Lines 101-107: show warning for failed email in under-review action.
- Lines 117-123: show warning for failed email in reject action.
- Line 138: adds `is_anonymous` and `submitted_by` in admin list.
- Line 141: allows filter by anonymous/non-anonymous.
- Line 148: includes `is_anonymous` in form layout.
- Line 164: makes `is_anonymous` read-only in edit mode.
- Lines 172-175: `submitted_by` uses privacy-safe display property.
- Line 224: only attach `created_by` on create when not anonymous.
- Lines 236-244: status change triggers email; failure shown as warning.

### 10) `BanglaCERT/BanglaCERT/settings.py` (Shreya-related lines only)

- Lines 20-33: loads `.env` file into process environment.
- Line 153: reads email backend from env.
- Line 154: reads SMTP host from env.
- Line 155: reads SMTP port from env.
- Line 156: reads TLS toggle from env.
- Line 157: reads SMTP username from env.
- Line 158: reads SMTP password from env and strips spaces.
- Line 159: sets sender email.
- Line 162: toggles async mode (`true/false`).

## How to Verify Shreya Feature

1. Run migration:
`python manage.py migrate incidents`

2. Run server:
`python manage.py runserver`

3. Submit anonymous report:
Open `http://127.0.0.1:8000/incidents/report/`

4. Confirm anonymity:
In admin incident list, anonymous report should show `Submitted by: Anonymous`.

5. Test email:
- Ensure SMTP env is valid.
- Change incident status in admin.
- Email should be sent to `reporter_email` or fallback `created_by.email`.

6. If email fails:
Admin shows warning like:
`Status email not sent for Incident #X: <reason>`

## Important Security Note

If SMTP app password was ever exposed, revoke it immediately and create a new one.
