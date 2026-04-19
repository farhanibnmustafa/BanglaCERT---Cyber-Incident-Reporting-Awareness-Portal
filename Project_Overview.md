# BanglaCERT: Complete System Documentation & Code Anatomy

This document provides a highly detailed, file-by-file breakdown of the BanglaCERT platform. It is designed to act as a comprehensive reference guide to help developers, students, and reviewers understand exactly how the system is structured, how the backend communicates with the frontend, and how data moves throughout the deployment architecture.

---

## 1. Complete Technology Stack
### Frontend
* **React.js**: Used for interactive, client-side UI components (Navbar, Dynamic Post Cards).
* **Vite**: The build tool that compiles and bundles the React code into compressed assets for the browser.
* **Vanilla HTML/CSS/JS**: Used for standard Django views and server-rendered templates.
* **AJAX (Asynchronous JavaScript and XML)**: Used for seamless page updates without full reloads (e.g., Live Search).

### Backend
* **Python**: The core programming language.
* **Django**: The high-level Python web framework handling routing, business logic, ORM mapping, and the admin dashboard.
* **Whitenoise**: Middleware used for serving static assets optimally.
* **Django-Storages**: A library used to bridge Django with cloud storage providers.

### Database & Cloud Storage
* **Supabase (PostgreSQL)**: Serves as the remote, persistent relational database.
* **Supabase Storage (S3-Compatible)**: Handles all media and evidence uploads. This is required because Vercel's serverless environment is **read-only**, meaning files cannot be saved to a local folder.

### Infrastructure & Deployment
* **Vercel**: The cloud platform hosting the application via Serverless Functions.

---

## 2. Directory & File Anatomy (In Detail)

### A. Root Level & Configuration Files
These files govern the deployment and environment of the entire system.
* **`Pipfile` & `Pipfile.lock`**: The primary dependency management files. Vercel's `@vercel/python` builder prioritizes these. They ensure that libraries like `django-storages` and `boto3` are installed in the production environment.
* **`requirements.txt`**: A redundancy file listing all Python dependencies. It is used by the `build_files.sh` script to ensure local tools and static collections have the necessary libraries.
* **`build_files.sh`**: The instruction script run by Vercel before deployment.
    * *What it does*:
        1. Navigates into `frontend/` to run `npm install` and `npm run build`.
        2. Generates the React UI assets.
        3. Runs `pip install` for backend dependencies.
        4. Executes `collectstatic` to gather all CSS/JS files into a single location for Whitenoise.
* **`vercel.json`**: The core Vercel configuration.
    * *What it does*: It defines the "builds" for the Python WSGI app and the static assets. It also handles the routing rules that forward traffic to the Django backend.
* **`.env`**: Contains sensitive keys (Secret Key, Database URL, Supabase S3 keys). These are mirrored in the Vercel Dashboard for production.
* **`notifications/` (The Notification App)**:
    * **`models.py`**: Defines the `Notification` model which links alerts to specific users or incidents.
    * **`views.py`**: Provides API endpoints (`/api/latest/`, `/api/mark-read/`) that serve JSON data to the React frontend.
    * **`urls.py`**: Maps the notification API routes.

---

## 3. Comprehensive File-by-File Anatomy

This section details every critical file in the system and its specific responsibility.

### I. Root Configuration & Deployment
*   **`vercel.json`**: The heart of the deployment. It tells Vercel how to handle the Django app (WSGI) and where to serve static files from. It handles URL routing between the backend and frontend.
*   **`build_files.sh`**: A shell script that runs during the Vercel build phase. It installs project dependencies, builds the React frontend, and runs Django tasks like `migrate` and `collectstatic`.
*   **`Pipfile` & `Pipfile.lock`**: Modern dependency management files for Python. They ensure that every developer and production server uses the exact same versions of libraries like `django-storages` and `boto3`.
*   **`requirements.txt`**: A standard list of Python packages. It serves as a fallback for tools that don't support `Pipfile` and is used in the `build_files.sh` process.
*   **`manage.py`**: The standard Django command-line utility for administrative tasks (starting the server, creating migrations, creating superusers).

### II. The Frontend Directory (`/frontend`)
*   **`package.json`**: Tracks all JavaScript dependencies (React, Vite, Lucide Icons) and defines build scripts (`npm run build`).
*   **`vite.config.js`**: Configures the Vite build engine. It is specifically set up to output the final React bundle into the `BanglaCERT/static/react/` folder so Django can serve it.
*   **`src/main.jsx`**: The main entry point for the React application. It finds a specific `div` in the HTML and injects the interactive components.
*   **`src/components/Navbar.jsx`**: A sophisticated, interactive navigation bar. It handles user authentication states, mobile navigation, and the real-time notification polling logic.
*   **`src/components/Navbar.css`**: Contains all the responsive styles and premium "Cybersecurity" aesthetics (glassmorphism, gradients) for the top navigation.
*   **`src/App.jsx`**: The root component where global React state or layout structures are defined.
*   **`index.html`**: A standard HTML wrapper used by Vite during local development.

### III. The Django Core & Shared Apps (`/BanglaCERT`)

#### `BanglaCERT/BanglaCERT/` (Project Config)
*   **`settings.py`**: The central brain. Configures database connections (Supabase), storage backends (S3), security keys, and installed applications.
*   **`urls.py`**: The root routing table. It directs traffic to the specific apps (Incidents, Accounts, etc.) based on the URL path.
*   **`wsgi.py`**: Web Server Gateway Interface. Used by Vercel's Python runtime to serve the Django application.

#### `BanglaCERT/incidents/` (The Primary Engine)
*   **`models.py`**: Defines `Incident`, `IncidentComment`, and `IncidentEvidence`. This is where the core data structure of the platform lives.
*   **`views.py`**: Handles user-facing logic such as reporting an incident, viewing details, and anonymous tracking.
*   **`staff_views.py`**: Contains the complex logic used only by BanglaCERT staff (Admins), such as adding official notes and changing incident statuses.
*   **`forms.py`**: Defines the data validation rules for reporting incidents and posting comments.
*   **`admin_urls.py`**: Specialized routing for the custom Staff Dashboard.
*   **`templates/incidents/`**: Houses all the HTML for reporting, detail views, and the customized admin interfaces.
*   **`staff_tools.py`**: Utility functions specifically for staff operations, like generating report summaries.

#### `BanglaCERT/notifications/` (The Alert System)
*   **`models.py`**: Defines the `Notification` model which tracks internal alerts (Who, What, Where, and Read State).
*   **`views.py`**: Provides the API endpoints that power the real-time notification bell in the React Navbar.
*   **`services.py`**: Specialized logic for generating and sending notifications to the right users at the right time.

#### `BanglaCERT/analytics/` (Data & Insights)
*   **`services.py`**: Calculates complex statistics (e.g., incidents by category, monthly trends) used to build the dashboard visualizations.
*   **`views.py`**: Serves the data that powers the graphical charts on the landing page and staff dashboard.

#### `BanglaCERT/awareness/` (Public Knowledge Base)
*   **`models.py`**: Manages "Verified Posts"—the public-facing educational content and confirmed incident summaries.
*   **`views.py`**: Handles how public users search and interact with verified security alerts.

#### `BanglaCERT/accounts/` (User & Security)
*   **`models.py`**: Extends the standard Django user model if specialized fields (like staff roles) are needed.
*   **`views.py`**: Manages secure login, registration, and staff authentication flows.

#### `BanglaCERT/auditlog/` (System Integrity)
*   **`models.py`**: Records every major action taken within the system (who edited what and when) to ensure accountability and a clear paper trail for incident handling.

#### `BanglaCERT/search/` (Live Data Filtering)
*   **`filters.py`**: Defines the logic for the AJAX-based live search on the platform, allowing users to find specific verified incidents instantly.
*   **`services.py`**: Optimizes search queries against the PostgreSQL database for maximum performance.

#### `BanglaCERT/core/` (Shared Infrastructure)
*   **`urls.py`**: Shared routing logic for the homepage and general platform utilities.
*   **`templates/base/`**: Contains `site.html`, the **Master Layout**. Every page on the site inherits from this file to ensure a consistent header, footer, and styling.
*   **`static/core/`**: Shared assets used across all apps, including the primary BangorCERT logos and global CSS variables.

### IV. Static Assets & Media Infrastructure
*   **`staticfiles/`**: The collection point for all CSS, JS, and Images once they are processed by Django's `collectstatic` command. Whitenoise serves files from here in production.
*   **`static/`**: The source directory for global static files (separate from individual apps).
*   **`media/`**: Local storage for uploaded files during development.
    *   **`incident_evidence/`**: Temporarily stores evidence before any S3 migration is fully active (locally).

### B. The Frontend Directory (`/frontend`)
* **`vite.config.js`**: Configures Vite to export compressed assets directly into Django’s static directory, ensuring seamless integration between React and Python.
* **`src/main.jsx`**: The React entry point which "hydrates" the HTML provided by Django with interactive components.
* **`src/components/Navbar.jsx`**: Houses the **Notification Bell**. It uses React's `useEffect` to poll the backend every 60 seconds for new alerts and displays a dynamic badge count.

### C. The Django Backend (`/BanglaCERT`)

#### `BanglaCERT/BanglaCERT/` (Core Configuration)
* **`settings.py`**: The "Brain" of the project.
    * *Key Logic*: Contains the **Storage Migration Logic**. It detects if Supabase S3 credentials are present. If they are (Production), it switches the entire site to use `S3Boto3Storage`. If not (Local Development), it falls back to the local `FileSystemStorage`.
* **`wsgi.py`**: The bridge between the web server and the Django code.

#### `BanglaCERT/incidents/` (The Core Feature App)
* **`models.py`**: Defines the `Incident` and `IncidentEvidence` tables. `IncidentEvidence` uses a `FileField` which, thanks to our configuration, automatically knows whether to save to a local folder or a Supabase bucket.
* **`forms.py`**: Contains Django forms for reporting and editing. `IncidentReportForm` and `IncidentPublicReportForm` both use a mixin for multi-file evidence uploads.
* **`views.py`**: Contains the logic for processing incident reports. It handles the `InMemoryUploadedFile` objects sent by the browser and hands them over to the storage backend.
* **`templates/incidents/`**:
    * **`incident_detail.html`**: Detail view for registered users. Includes the **"Modify Report"** action.
    * **`public_report_status.html`**: Tracking page for anonymous users. Includes the **"Manage Details"** action and the **Discussion Feed**.
    * **`edit_incident.html`**: A dedicated, responsive form page shared by both registered and anonymous workflows to update report details and add new evidence.
    * **`admin_incident_detail.html`**: The admin view for reviewing incidents.
        * *Key Logic*: When an admin clicks "View File", the template calls `evidence.file.url`. Because we enabled **S3v4 Signatures**, Django generates a temporary, secure URL that allows the admin to view private files in the Supabase bucket.

---

## 3. Deep Dive Insights

### Storage Migration: Why S3 instead of Local?
In a standard server (like XAMPP), files are saved to a folder on the hard drive. However, Vercel uses **Serverless Functions**, which are temporary and **Read-Only**.
1. **The Problem**: If a user uploads a screenshot, Django tries to create a folder. Vercel blocks this, causing an `OSError`.
2. **The Solution**: We integrated `django-storages`. Now, when a file is uploaded, Django sends it via API to **Supabase Storage**.
3. **Security**: We use **Signed URLs**. This means that files in the bucket are private and cannot be accessed by anyone unless they have a temporary, cryptographically signed link generated by our Django admin panel.

### The Admin Workflow
1. **Submission**: A user submits an incident. The file is streamed directly to Supabase.
2. **Database Record**: Django creates a row in the database that stores the *path* to the file in Supabase.
3. **Admin Review**: A staff member opens the dashboard. Django looks up the file path, generates a secure v4 signature, and provides a clickable link.

### Internal Notification Engine
Unlike noisy email notifications, BanglaCERT uses a **Social Media Style Internal System**:
1. **Model-Driven**: Notifications are stored as database rows, allowing them to persist across sessions.
2. **Bidirectional Triggers**:
    * **To Staff**: Triggered whenever a user adds a comment or reply.
    * **To Users**: Triggered whenever a staff member adds an "Admin Note" to an incident.
3. **React Polling**: The React Navbar fetches unread notifications via AJAX every 60 seconds, updating the UI in real-time without full page reloads.

### Anonymous Tracking & Authentication
How does the system identify an anonymous user without a login?
1. **ID Generation**: When a report is submitted, `ensure_public_tracking_credentials()` generates a unique `tracking_id` (e.g., `BC-000001-A2B4`) and a 32-character `access_token` using Python's `secrets` module. 
2. **Session Storage**: These credentials are temporarily stored in `request.session` so the user can see their status page immediately after submission.
3. **Lookup Logic**: For future visits, the user enters their ID and Token. The backend uses `secrets.compare_digest` to prevent timing attacks while verifying access.

### The Editing System & Status Locking
To maintain the integrity of evidence for legal and investigation purposes:
1. **Dynamic Editing**: Users can modify their reports (Title, Category, Description) and upload **additional evidence** as the situation evolves.
2. **Status Locking**: The system implements a **Hard Lock**. Once an incident is marked as `VERIFIED`, `REJECTED`, or `CLOSED` by the BanglaCERT team, all editing actions are disabled. This prevents reporters from altering information after an official review has taken place.

---

## 4. Common Teacher/Viva Questions & Answers

**Q: "How did you solve the 'Read-Only File System' error on Vercel?"**
> **A:** "Vercel's serverless environment is read-only. I solved this by migrating the media storage to an S3-compatible bucket on Supabase using the `django-storages` library. This allows the application to store and retrieve files from the cloud instead of the local disk."

**Q: "Are the uploaded evidence files public or private?"**
> **A:** "They are stored securely. We configured the system to use 'Signed URLs' with S3v4 authentication. This ensures that only authorized staff members can view the evidence, and the links expire automatically after a short period."

**Q: "What is the difference between requirements.txt and Pipfile in this project?"**
> **A:** "The `Pipfile` is used by the Vercel Python runtime to build the environment, while `requirements.txt` is used by our manual build script (`build_files.sh`) to ensure static file collection and other build-time tasks have the correct libraries available."

**Q: "How do you handle notifications for anonymous reporters?"**
> **A:** "Instead of email, we use an internal notification system. When an admin adds a note, a notification record is linked to that specific incident. When the anonymous user checks their status page using their tracking credentials, the system detects these notifications and displays a prominent 'New Message' banner."

**Q: "How are the Tracking ID and Access Token generated?"**
> **A:** "We use the `secrets` module for cryptographically strong generation. The Tracking ID is a human-readable string based on the incident's ID and a random hex suffix, while the Access Token is a secure 32-character hex string generated at the moment of submission."

**Q: "Why is the editing feature locked after a report is verified?"**
> **A:** "It's a security best practice for incident response. Once the BanglaCERT team has reviewed the evidence and issued a verdict (Verified or Rejected), the report becomes an official record. Locking it prevents tampering or accidental changes to the timeline of the investigation."
