# BanglaCERT: System Architecture & Deployment Documentation

This document explains how the BanglaCERT system is built, how the backend works, and how it is deployed on Vercel using a serverless architecture.

---

## 1. Overall Concept: Serverless Architecture
Unlike traditional websites that run on a permanent computer (server) 24/7, BanglaCERT uses a **Serverless** approach. 
- **What it means:** The code only runs when someone visits the site. 
- **Benefit:** It is very fast, scales automatically, and costs much less to maintain.

---

## 2. The Backend (Django)
The backend is built with **Django**. In this project, Django acts as the "brain".
- **Serverless Functions:** When you visit a URL (like `/incidents/`), Vercel starts a small "function" that runs the Django code just for that specific request.
- **WSGI Integration:** We use a file called `BanglaCERT/BanglaCERT/wsgi.py`. This is the bridge that connects Vercel to Django.
- **Python Runtime:** Vercel installs the necessary Python packages from `requirements.txt` to make sure Django has all its tools.

---

## 3. The Frontend (React)
The "skin" or user interface of the site is built with **React** (located in the `frontend` folder).
- **Static Files:** React is "built" into single JavaScript (`app.js`) and CSS (`app.css`) files.
- **Vite:** We use a tool called Vite to turn the complex React code into these simple files.
- **CDN Serving:** Vercel serves these files from its **Edge Network**. This means if a user is in Bangladesh, they get the files from the nearest server for maximum speed.

---

## 4. The Deployment Process (How it gets to Vercel)
Two main files control how the project is "born" on Vercel:

### A. `vercel.json` (The Map)
This file tells Vercel:
1. **Builds:** 
   - Use Python for the Django part.
   - Use the `build_files.sh` script to set everything up.
2. **Routes:** 
   - If someone asks for a file in `/static/`, look in the static folder.
   - Everything else should go to the Django "brain" (`wsgi.py`).

### B. `build_files.sh` (The Instruction Manual)
Before the site goes live, Vercel runs these commands:
1. **Frontend Build:** It goes into the `frontend` folder, installs dependencies (`npm install`), and compiles the React code (`npm run build`).
2. **Backend Setup:** It installs Python packages (`pip install`).
3. **Static Collection:** It runs Django's `collectstatic` command. This gathers all files (React builds, Django CSS/JS) into one place (`staticfiles`) so Vercel can find them.

---

## 5. Database & Storage
- **Database:** Since serverless functions don't have a permanent hard drive, we use **Supabase** (PostgreSQL) as an external database. It stores all the incidents, users, and comments.
- **Media:** Images or evidence files uploaded by users are stored separately (usually on a cloud storage like S3 or Supabase Storage) so they don't disappear when the serverless function turns off.

---

## 6. Summary: How a Request Works
1. **User** clicks a link on `banglacert.vercel.app`.
2. **Vercel** checks if it's a static file (image/CSS). If yes, it sends it immediately.
3. If it's a page (like the Dashboard), **Vercel wakes up Django**.
4. **Django** talks to **Supabase** to get the data.
5. **Django** sends the page back to the user.
6. **React** takes over in the browser to make the UI interactive (like the Navbar and Charts).

---

*This document was generated to explain the modern, scalable infrastructure of the BanglaCERT portal.*
