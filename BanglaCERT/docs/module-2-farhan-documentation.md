# Module 2 Documentation: Farhan Part

## 1. Purpose

This file explains Farhan's Module 2 implementation in a separate document.

It covers:

- structured incident reporting
- incident category handling
- evidence upload and storage
- admin category reclassification
- incident status review

It also explains:

- which file was changed
- what was done in that file
- the important line ranges in simple language

## 2. What was already there and what was added now

### 2.1 Already implemented before this update

These parts already existed in the project:

- incident title field
- incident category field
- incident description field
- incident date field
- incident status field
- admin status update flow
- incident comments

Main files:

- `incidents/models.py`
- `incidents/forms.py`
- `incidents/views.py`
- `incidents/staff_views.py`

### 2.2 Added now for Farhan's missing part

These parts were added now:

- evidence upload model linked to incidents
- evidence validation for file type and file size
- file upload support in report forms
- evidence display in user detail page
- evidence display in admin detail page
- admin category reclassification
- tests for upload and reclassification
- migration for the new evidence table

## 3. Requirement traceability

| Requirement | Status | Main files |
| --- | --- | --- |
| Report incident with title, type/category, description, date | Implemented | `incidents/models.py`, `incidents/forms.py`, `incidents/views.py` |
| Validate fields and allow admin reclassification | Implemented | `incidents/forms.py`, `incidents/staff_views.py`, `incidents/admin_urls.py` |
| Upload evidence and link it to the incident | Implemented | `incidents/models.py`, `incidents/forms.py`, `incidents/views.py` |
| Status workflow with admin-only updates | Already implemented | `incidents/models.py`, `incidents/staff_views.py` |

## 4. File-by-file explanation

## 4.1 `incidents/models.py`

Purpose: define the database structure.

### What was done in this file

- added evidence validation rules
- added upload path helper
- kept incident and comment models
- added a new `IncidentEvidence` model

### Important line ranges

- Lines 1-6:
  - import `Path`, `uuid4`, Django settings, `ValidationError`, and `models`
  - these are needed for file validation and unique filenames

- Lines 9-10:
  - define allowed evidence formats and max file size
  - allowed: `.png`, `.jpg`, `.jpeg`, `.pdf`
  - size limit: 5 MB

- Lines 13-18:
  - `validate_evidence_file(uploaded_file)`
  - checks the file extension
  - checks the file size
  - raises an error if the file is unsafe or too large

- Lines 21-24:
  - `incident_evidence_upload_to(instance, filename)`
  - builds the storage path for uploaded evidence files
  - uses a random id so filenames do not clash

- Lines 27-72:
  - `Incident` model
  - stores:
    - title
    - category
    - description
    - incident date
    - anonymity flag
    - status
    - reporter email
    - creator
    - created time
    - updated time

- Lines 75-89:
  - `IncidentComment` model
  - stores comments linked to an incident

- Lines 92-114:
  - `IncidentEvidence` model
  - Line 93 links evidence to an incident
  - Line 94 stores the uploaded file and validates it
  - Line 95 stores the original filename
  - Lines 96-98 keep the uploader if available
  - Line 99 stores upload time
  - Lines 104-107 fill the original filename automatically if needed
  - Lines 109-111 provide a clean display name for templates

### Easy explanation

This file is the main database design.

- `Incident` = the report
- `IncidentComment` = discussion under the report
- `IncidentEvidence` = proof file attached to the report

## 4.2 `incidents/forms.py`

Purpose: control what data is allowed from the browser.

### What was done in this file

- added multi-file evidence input support
- added evidence field to report forms
- added staff category form for reclassification

### Important line ranges

- Lines 6-7:
  - `MultipleEvidenceFileInput`
  - allows one file field to accept multiple files

- Lines 10-19:
  - `MultipleEvidenceFileField`
  - normalizes the uploaded data into a list
  - makes the code easier when saving files

- Lines 22-28:
  - `IncidentEvidenceMixin`
  - defines the reusable `evidence_files` field
  - this field is optional
  - it uses the validator from `models.py`

- Lines 31-38:
  - `IncidentReportForm`
  - normal logged-in user report form
  - includes title, category, description, incident date
  - also includes evidence upload through the mixin

- Lines 66-69:
  - `IncidentStaffStatusForm`
  - staff can update only the status from this form

- Lines 72-75:
  - `IncidentStaffCategoryForm`
  - staff can update only the category from this form
  - this is the new admin reclassification form

- Lines 87-104:
  - `IncidentPublicReportForm`
  - anonymous/public report form
  - includes report details, reporter email, and evidence upload

### Easy explanation

This file decides what each page is allowed to send.

- user report page can send evidence
- guest report page can send evidence
- admin category form can change only category
- admin status form can change only status

## 4.3 `incidents/views.py`

Purpose: handle the user-side and public-side incident submission flow.

### What was done in this file

- added helper to save evidence after incident creation
- changed report views to read uploaded files
- passed evidence to the user detail template

### Important line ranges

- Lines 14-21:
  - `_save_evidence_files(incident, uploaded_by, files)`
  - loops over uploaded files
  - creates one `IncidentEvidence` row for each file

- Lines 31-51:
  - `report_incident(request)`
  - Line 38 now reads `request.POST` and `request.FILES`
  - Lines 40-45 prepare the incident
  - Line 46 saves evidence files after the incident is saved

- Lines 54-67:
  - `public_report_incident(request)`
  - Line 56 now reads uploaded files too
  - Lines 58-61 save anonymous report data
  - Line 62 saves public evidence files linked to the incident

- Lines 83-101:
  - `incident_detail(request, incident_id)`
  - Line 90 loads evidence files for display
  - Lines 95-99 send them to the template

### Easy explanation

This file handles the actual save process:

1. save the incident
2. save the evidence files
3. link the evidence to that incident

## 4.4 `incidents/staff_views.py`

Purpose: handle the admin/staff review side.

### What was done in this file

- passed evidence files into admin detail page
- added admin category update logic
- kept existing admin status update logic

### Important line ranges

- Lines 133-147:
  - `incident_detail(request, incident_id)`
  - Line 141 loads evidence files
  - Line 143 creates the category form
  - Line 144 creates the status form

- Lines 216-246:
  - `update_incident_category(request, incident_id)`
  - checks request method
  - loads the incident
  - validates the new category
  - saves the category if it changed
  - writes an audit log entry
  - redirects back to the admin detail page

- Lines 249-277:
  - `update_incident_status(request, incident_id)`
  - this already existed
  - staff-only status update remains in place

### Easy explanation

This file is where staff review incidents.

Now staff can:

- see evidence
- fix the category
- update the status

## 4.5 `incidents/admin_urls.py`

Purpose: connect admin URLs to admin views.

### What was done in this file

- added a new URL for category update

### Important line ranges

- Lines 7-14:
  - custom admin routes
  - Line 12 is the new category update endpoint
  - Line 13 is the status update endpoint

### Easy explanation

This file gives the admin category form somewhere to submit.

## 4.6 `incidents/templates/incidents/report_incident.html`

Purpose: logged-in user report page.

### What was done in this file

- changed the form to support file upload

### Important line ranges

- Lines 8-10:
  - added `enctype="multipart/form-data"`
  - this is required for file uploads

### Easy explanation

Without this, the browser cannot send files to Django.

## 4.7 `incidents/templates/incidents/public_report_incident.html`

Purpose: anonymous/public report page.

### What was done in this file

- changed the form to support file upload
- added evidence field display

### Important line ranges

- Line 8:
  - added `multipart/form-data`

- Lines 37-42:
  - render the evidence field
  - show label, input, errors, and help text

### Easy explanation

This lets a guest upload proof files together with the anonymous report.

## 4.8 `incidents/templates/incidents/incident_detail.html`

Purpose: show one incident to the reporting user.

### What was done in this file

- added evidence file list

### Important line ranges

- Lines 14-26:
  - show evidence files if they exist
  - otherwise show a simple empty message

### Easy explanation

The reporting user can now open the incident and see the attached proof files.

## 4.9 `incidents/templates/incidents/admin_incident_detail.html`

Purpose: staff review screen.

### What was done in this file

- added category update form
- added evidence display section

### Important line ranges

- Lines 39-44:
  - new category form for admin reclassification

- Lines 62-79:
  - evidence list for staff
  - shows link, upload time, and uploader when available

### Easy explanation

This is the main page where staff review an incident.
Now they can see proof files and correct the category.

## 4.10 `BanglaCERT/settings.py`

Purpose: project configuration.

### What was done in this file

- added media storage settings

### Important line ranges

- Lines 149-150:
  - `MEDIA_URL` defines the browser path for uploaded files
  - `MEDIA_ROOT` defines the folder where uploaded files are stored

### Easy explanation

Evidence files need a place to live.
This file gives Django that location.

## 4.11 `BanglaCERT/urls.py`

Purpose: top-level routing.

### What was done in this file

- added media serving in debug mode

### Important line ranges

- Lines 17-18:
  - import `settings` and `static`

- Lines 37-38:
  - serve uploaded media files in development

### Easy explanation

This makes uploaded files openable from the browser while developing locally.

## 4.12 `incidents/migrations/0005_incidentevidence.py`

Purpose: database migration for the new evidence table.

### What was done in this file

- created the `IncidentEvidence` table

### Important line ranges

- Lines 11-14:
  - migration dependencies

- Lines 16-30:
  - create the new model in the database
  - file field
  - original name
  - upload time
  - incident relation
  - uploader relation

### Easy explanation

This file is why `manage.py migrate` had a new migration to apply.

## 4.13 `incidents/tests.py`

Purpose: verify the new behavior works.

### What was done in this file

- added upload test
- added invalid file format test
- added admin category reclassification test

### Important line ranges

- Lines 23-45:
  - create a temporary media folder for tests

- Lines 83-102:
  - test valid evidence upload

- Lines 104-121:
  - test invalid file type rejection

- Lines 293-317:
  - test admin category reclassification

### Easy explanation

These tests prove the new feature works and is safe enough for the class project.

## 4.14 `BanglaCERT/test_settings.py`

Purpose: test-only settings.

### What was done in this file

- added a simple SQLite-based settings file for verification

### Important line ranges

- Lines 4-9:
  - use in-memory SQLite

- Lines 13-15:
  - simplify incident test verification

### Easy explanation

This file is only for easier testing.
It is not part of the user-facing feature.

## 5. Exact line-by-line guide

This appendix gives stricter line-by-line notes for the main Farhan-related code.

It focuses on the actual feature lines, so you can explain them in class more easily.

## 5.1 `incidents/models.py` exact line notes

- Line 1: imports `Path` so the code can read file extensions safely.
- Line 2: imports `uuid4` so every stored evidence file can get a unique name.
- Line 4: imports Django `settings`.
- Line 5: imports `ValidationError` for upload validation errors.
- Line 6: imports Django `models`.
- Line 9: defines the allowed evidence extensions.
- Line 10: defines maximum evidence size as 5 MB.
- Line 13: starts the `validate_evidence_file` function.
- Line 14: reads the uploaded file extension.
- Line 15: checks whether the extension is allowed.
- Line 16: raises an error for invalid file format.
- Line 17: checks the uploaded file size.
- Line 18: raises an error if the file is too large.
- Line 21: starts the upload-path helper.
- Line 22: keeps the original file suffix.
- Line 23: uses the incident id inside the storage path when possible.
- Line 24: returns the final path string for the stored file.
- Line 27: starts the `Incident` model.
- Lines 28-33: define the available status constants.
- Lines 35-42: define visible status labels for forms and templates.
- Lines 44-50: define valid category values.
- Line 52: stores incident title.
- Line 53: stores incident category.
- Line 54: stores incident description.
- Line 55: stores incident date.
- Line 56: stores anonymity flag.
- Line 57: stores status.
- Line 58: stores reporter email.
- Lines 59-61: link incident to the user when there is one.
- Line 62: stores creation time automatically.
- Line 63: stores update time automatically.
- Line 65: starts the incident string method.
- Line 66: returns a readable incident string.
- Line 68: starts the reporter-display property.
- Line 69: checks if the reporter should be hidden.
- Line 70: condition for anonymous or missing user.
- Line 71: returns `"Anonymous"` in that case.
- Line 72: otherwise returns the real username.
- Line 75: starts the `IncidentComment` model.
- Line 76: links comment to incident.
- Lines 77-79: link comment to author.
- Line 80: stores comment text.
- Line 81: stores admin-note flag.
- Line 82: stores comment time.
- Lines 84-85: define comment ordering.
- Line 87: starts comment string method.
- Line 88: gets author display name.
- Line 89: returns readable comment text.
- Line 92: starts the new `IncidentEvidence` model.
- Line 93: links evidence to incident.
- Line 94: stores uploaded file and runs validation.
- Line 95: stores original filename.
- Lines 96-98: link evidence to uploader when available.
- Line 99: stores upload time.
- Lines 101-102: sort evidence newest first.
- Line 104: starts custom save method.
- Line 105: checks if original filename is still empty.
- Line 106: copies the uploaded file name into `original_name`.
- Line 107: saves the model normally.
- Line 109: starts `display_name` property.
- Line 110: returns original name when available.
- Line 111: otherwise falls back to file name.
- Line 113: starts evidence string method.
- Line 114: returns readable evidence label.

## 5.2 `incidents/forms.py` exact line notes

- Line 1: imports Django forms.
- Line 3: imports incident models and the evidence validator.
- Line 6: starts `MultipleEvidenceFileInput`.
- Line 7: allows multiple file selection.
- Line 10: starts `MultipleEvidenceFileField`.
- Line 11: tells the field to use the multi-file widget.
- Line 13: starts custom `clean(...)`.
- Line 14: keeps Django's normal single-file clean function.
- Line 15: returns empty list if nothing was uploaded.
- Line 16: explicit empty-list return.
- Line 17: checks whether multiple files were submitted.
- Line 18: cleans each uploaded file one by one.
- Line 19: wraps a single file into a list.
- Line 22: starts reusable `IncidentEvidenceMixin`.
- Line 23: creates the `evidence_files` field.
- Line 24: makes evidence optional.
- Line 25: applies file validation.
- Line 26: sets the label text.
- Line 27: sets the help text.
- Line 31: starts the logged-in user report form.
- Lines 32-38: configure model, form fields, date widget, and description widget.
- Line 41: starts normal user comment form.
- Lines 42-47: configure the comment field and textarea widget.
- Line 50: starts staff filter form.
- Lines 51-55: create search field.
- Lines 56-59: create status dropdown.
- Lines 60-63: create category dropdown.
- Line 66: starts staff status form.
- Lines 67-69: allow staff to edit only the incident status.
- Line 72: starts staff category form.
- Lines 73-75: allow staff to edit only the incident category.
- Line 78: starts staff comment form.
- Lines 79-84: allow staff to add an internal note.
- Line 87: starts public report form.
- Lines 88-100: configure public report fields, widgets, labels, and help text.
- Line 102: starts constructor for the public form.
- Line 103: runs normal form setup.
- Line 104: makes `reporter_email` required.

## 5.3 `incidents/views.py` exact line notes

- Line 1: imports Django messages.
- Line 2: imports `login_required`.
- Line 3: imports `HttpResponseNotAllowed`.
- Line 4: imports shortcut helpers.
- Line 6: imports incident forms.
- Line 7: imports `Incident` and `IncidentEvidence`.
- Line 10: starts helper to fetch only the current user's incident.
- Line 11: returns 404 if the incident does not belong to that user.
- Line 14: starts helper to save evidence files.
- Line 15: loops over uploaded files.
- Lines 16-21: create one `IncidentEvidence` object per file.
- Line 24: starts home view.
- Lines 25-28: redirect staff to admin and users to their report list.
- Line 31: starts normal report view.
- Lines 33-35: block staff from reporting through user page.
- Line 37: checks for POST.
- Line 38: reads text form data plus uploaded files.
- Line 39: checks whether the form is valid.
- Lines 40-45: prepare the incident before save.
- Line 45: saves the incident.
- Line 46: saves evidence after incident save.
- Line 47: shows success message.
- Line 48: redirects to incident detail page.
- Lines 49-51: handle GET request with empty form.
- Line 54: starts public report view.
- Line 55: checks for POST.
- Line 56: reads text form data plus uploaded files.
- Lines 57-61: prepare and save anonymous incident.
- Line 62: save anonymous evidence files.
- Lines 63-64: show success and redirect.
- Lines 65-67: handle GET request with empty public form.
- Line 70: starts success-page view.
- Line 71: renders success template.
- Line 74: starts report-list view.
- Lines 75-80: block staff and list only current user's incidents.
- Line 83: starts user incident-detail view.
- Lines 84-86: block staff from user detail page.
- Line 88: load the user's own incident.
- Line 89: load comments.
- Line 90: load evidence files.
- Line 91: prepare comment form.
- Lines 92-101: render detail page with incident, comments, and evidence.
- Line 104: starts add-comment view.
- Lines 105-107: reject non-POST requests.
- Lines 109-110: block staff from normal comment endpoint.

## 5.4 `incidents/staff_views.py` exact line notes for the new work

- Line 133: starts admin incident-detail view.
- Line 135: loads the selected incident.
- Line 136: loads related comments.
- Line 137: starts the context dictionary.
- Line 141: adds evidence files to the admin detail page.
- Line 142: adds audit logs.
- Line 143: adds category-update form.
- Line 144: adds status-update form.
- Line 145: adds admin-note form.
- Line 147: renders admin detail template.
- Line 216: starts category-update view.
- Lines 218-219: reject non-POST methods.
- Line 221: loads the incident to edit.
- Line 222: saves previous category for comparison.
- Line 223: binds category form to submitted data.
- Lines 224-226: show error and redirect if form is invalid.
- Line 228: create unsaved updated incident object.
- Line 229: read the new category value.
- Lines 230-232: stop if category did not change.
- Line 234: copy the new category to the real incident object.
- Line 235: save category and update timestamp.
- Lines 236-244: write audit log entry for the category change.
- Line 245: show success message.
- Line 246: redirect back to admin detail page.
- Line 249: starts status-update view.
- Lines 251-252: reject non-POST methods.
- Line 254: load incident for status change.
- Line 255: save previous status.
- Line 256: bind status form to submitted data.
- Lines 257-259: handle invalid status submission.
- Line 261: create unsaved updated incident object.
- Line 262: read new status.
- Lines 263-265: stop if status did not change.
- Line 267: copy new status to real incident.
- Line 268: save status and update timestamp.
- Line 269: write audit log entry.
- Line 271: try sending notification.
- Lines 272-275: show success or warning message depending on email result.
- Line 277: redirect back to admin detail page.

## 5.5 Smaller files exact line notes

### `incidents/admin_urls.py`

- Line 1: imports `path`.
- Line 3: imports `staff_views`.
- Line 5: names this URL module `admin`.
- Line 7: starts the route list.
- Line 8: first-admin setup route.
- Line 9: admin dashboard route.
- Line 10: staff account route.
- Line 11: admin incident detail route.
- Line 12: new category update route.
- Line 13: status update route.
- Line 14: admin comment route.
- Line 15: closes the route list.

### `BanglaCERT/settings.py`

- Line 145: keeps static URL setting.
- Lines 146-148: keep static directory list.
- Line 149: defines browser URL for uploaded media.
- Line 150: defines disk folder for uploaded media.
- Lines 152-163: existing email settings remain active.

### `BanglaCERT/urls.py`

- Line 17: imports settings.
- Line 18: imports `static(...)` helper.
- Lines 19-20: import normal URL helpers.
- Lines 22-35: keep the main project routes.
- Line 37: checks `DEBUG`.
- Line 38: serves uploaded media in development.

### `incidents/migrations/0005_incidentevidence.py`

- Line 1: generated migration header.
- Lines 3-6: import migration requirements.
- Line 9: starts migration class.
- Lines 11-14: define dependencies.
- Line 16: starts operations list.
- Line 17: starts model creation.
- Line 18: names the model `IncidentEvidence`.
- Line 20: creates the primary key.
- Line 21: creates the evidence file field.
- Line 22: creates the original-name field.
- Line 23: creates timestamp field.
- Line 24: links evidence to incident.
- Line 25: links evidence to uploader.
- Lines 27-29: set ordering.
- Line 31: closes operations list.

### `incidents/templates/incidents/report_incident.html`

- Line 1: extends base template.
- Line 3: sets page title.
- Line 5: starts content block.
- Line 6: shows page heading.
- Line 7: shows helper text.
- Line 8: starts form and enables file upload.
- Line 9: adds CSRF token.
- Line 10: renders the form.
- Line 11: shows submit button.
- Line 12: closes form.
- Line 13: closes content block.

### `incidents/templates/incidents/public_report_incident.html`

- Line 1: extends base template.
- Line 3: sets page title.
- Line 5: starts content block.
- Line 6: shows page heading.
- Line 7: explains anonymous reporting.
- Line 8: starts form with file-upload support.
- Line 9: adds CSRF token.
- Line 10: shows non-field errors.
- Lines 11-15: title input.
- Lines 16-20: category input.
- Lines 21-25: description input.
- Lines 26-30: incident-date input.
- Lines 31-36: reporter-email input.
- Lines 37-42: evidence-files input.
- Line 43: submit button.
- Line 44: closes form.
- Line 45: closes content block.

### `incidents/templates/incidents/incident_detail.html`

- Line 1: extends base template.
- Line 2: loads timezone helper.
- Line 4: sets page title.
- Line 6: starts content block.
- Lines 7-12: show incident details.
- Line 14: evidence section heading.
- Line 15: checks whether evidence exists.
- Lines 16-23: loop through evidence files and show links.
- Lines 24-26: show empty-state text.
- Line 28: back link.
- Lines 30-60: existing comment section.
- Lines 62-67: existing add-comment form.
- Line 68: closes content block.

### `incidents/templates/incidents/admin_incident_detail.html`

- Lines 1-4: template setup and title.
- Lines 7-18: page header and navigation.
- Lines 20-36: incident details table.
- Lines 39-44: new category update form.
- Lines 46-51: status update form.
- Lines 53-58: admin note form.
- Lines 62-79: evidence display section.
- Lines 81-100: comments section.
- Lines 102-117: audit-log section.
- Line 119: closes content block.

### `BanglaCERT/test_settings.py`

- Line 1: import normal settings.
- Lines 4-9: replace DB with in-memory SQLite for tests.
- Line 11: use in-memory email backend.
- Lines 13-15: disable `incidents` migrations during local verification tests.

## 6. Simple flow explanation

1. User opens the report page.
2. User fills in title, category, description, and date.
3. User optionally uploads evidence.
4. Django validates file format and size.
5. Incident is saved.
6. Evidence files are saved and linked to that incident.
7. User can later see the evidence in the incident detail page.
8. Staff can open the incident in admin.
9. Staff can review the evidence.
10. Staff can correct the category if needed.
11. Staff can still update the status.

## 7. Verification

These checks were completed:

- `pipenv run python BanglaCERT/manage.py migrate`
  - result: `Applying incidents.0005_incidentevidence... OK`

- `pipenv run python BanglaCERT/manage.py check --settings=BanglaCERT.test_settings`
  - result: no system issues

- `pipenv run python BanglaCERT/manage.py test incidents --settings=BanglaCERT.test_settings`
  - result: tests passed

## 8. Short final summary

Farhan's Module 2 part is now documented in a separate file.

The project now supports:

- structured incident reporting
- evidence upload
- evidence validation
- evidence display
- admin category reclassification
- admin status review
