# BanglaCERT Project Structure (Easy Guide)

This file explains what each folder/file is for, and what you should put there.

## Quick Map (Top Level)
```
BanglaCERT/
  BanglaCERT/        # Django backend project + apps
  frontend/          # React frontend (optional)
  Pipfile            # Python dependencies
  Pipfile.lock       # Locked dependency versions
  README.md          # Short project title
  STRUCTURE.md       # This guide
```

## Backend Root: `BanglaCERT/`
This is the Django backend. You will spend most time here.

### Project Config: `BanglaCERT/BanglaCERT/`
This is the Django **project** folder (settings and global config).

- `BanglaCERT/BanglaCERT/settings.py`
  Put global settings here (database, installed apps, static/media paths).
- `BanglaCERT/BanglaCERT/urls.py`
  Main URL router. Connects each app’s `urls.py`.
- `BanglaCERT/BanglaCERT/asgi.py`
  ASGI entry point (for async servers).
- `BanglaCERT/BanglaCERT/wsgi.py`
  WSGI entry point (for classic servers).

### Project Runner
- `BanglaCERT/manage.py`
  Command line entry for Django (runserver, migrations, create superuser).

### Shared Templates/Static/Media
- `BanglaCERT/templates/`
  Global templates (base layout, shared HTML).
- `BanglaCERT/static/`
  Global static files (CSS/JS/images shared by all apps).
- `BanglaCERT/media/`
  User uploads (evidence files, incident attachments).

### Core Apps (Each app has its own folder)
Each app follows the same basic files:
- `apps.py` – App config (Django boilerplate).
- `models.py` – Database tables.
- `views.py` – Request/response logic.
- `urls.py` – App routes.
- `templates/<app_name>/` – HTML templates for this app.
- `static/<app_name>/` – CSS/JS/images for this app.
- `tests.py` – Tests.
- `migrations/` – Auto‑generated DB migrations.

### Apps You Have
- `BanglaCERT/accounts/`
  Login, registration, user roles. Use this for auth and profile logic.
- `BanglaCERT/incidents/`
  Main incident reporting logic (create, update, status workflow).
- `BanglaCERT/incidents/evidence/`
  Evidence attached to incidents (files, validation rules).
- `BanglaCERT/incidents/comments/`
  Comments and discussion attached to incidents.
- `BanglaCERT/awareness/`
  Verified incident posts shown to public users.
- `BanglaCERT/analytics/`
  Reports, charts, and stats.
- `BanglaCERT/analytics/dashboard/`
  Dashboard views and templates inside analytics (not a separate app).
- `BanglaCERT/auditlog/`
  Records admin actions for accountability.
- `BanglaCERT/notifications/`
  Email/status notifications and async tasks.
- `BanglaCERT/search/`
  Search and filter incidents, including “check report status”.
- `BanglaCERT/core/`
  Shared helpers, permissions, constants, and utilities used by other apps.

## Frontend: `frontend/`
React client (optional). Use if you want a separate SPA.

- `frontend/public/`
  Public static assets (favicon, index.html).
- `frontend/src/`
  All React source code.
- `frontend/src/components/`
  Reusable UI components.
- `frontend/src/pages/`
  Page-level components.
- `frontend/src/routes/`
  Route definitions.
- `frontend/src/services/`
  API calls to backend.
- `frontend/src/store/`
  State management (Redux/Zustand, etc).
- `frontend/src/styles/`
  Global styles.
- `frontend/src/hooks/`
  Custom React hooks.
- `frontend/src/utils/`
  Helper functions.

## What To Do Next (Simple Steps)
1. Add models inside each app’s `models.py`.
2. Add views and URLs in each app’s `views.py` and `urls.py`.
3. Create templates in `templates/<app_name>/`.
4. Add static files in `static/<app_name>/`.
5. Run migrations with `python manage.py makemigrations` and `python manage.py migrate`.
6. If using React, connect it to the Django API.

## Notes
- `__pycache__` folders can be ignored (do not commit).
- If an app grows too large, split it into modules (like `incidents/evidence`).

Noted:
All app urls.py files are currently empty (urlpatterns = []), so you’ll get 404s for those paths until you add routes. This is expected for a skeleton.
If you want media/ to be used for uploads, you still need to set MEDIA_ROOT and MEDIA_URL later in settings.py.