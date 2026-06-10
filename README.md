# HR/Admin Management System
**Cardstel Solutions Limited**

A secure, production-ready HR & Admin Management platform built with Streamlit. Consolidates Attendance Management, Business Department Appraisal, Staff Performance Appraisal, and Admin Panel into a single authenticated hub.

---

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Repository Structure](#repository-structure)
3. [Quick Start (Local Dev)](#quick-start-local-dev)
4. [Authentication & RBAC](#authentication--rbac)
5. [Deployment on Streamlit Community Cloud](#deployment-on-streamlit-community-cloud)
6. [Keep-Alive: Eliminating Cold Starts](#keep-alive-eliminating-cold-starts)
7. [Secrets Management](#secrets-management)
8. [Adding / Changing Users](#adding--changing-users)
9. [Sub-App Configuration](#sub-app-configuration)
10. [Security Notes](#security-notes)

---

## Architecture Overview

```
┌───────────────────────────────────────────────────────────────┐
│                   GitHub Repository                           │
│                                                               │
│  app.py  ──────────────────────  Main Hub (auth wall)         │
│  auth/   ──────────────────────  Auth engine + RBAC           │
│  utils/  ──────────────────────  Shared UI helpers            │
│  apps/                                                        │
│    ├── attendance/app.py  ─────  Attendance Management        │
│    ├── business_appraisal/app.py  Business KPI Appraisal      │
│    ├── staff_appraisal/app.py  ─  Staff Performance           │
│    └── admin_panel/app.py  ────   Admin Document Portal       │
│  .streamlit/config.toml  ──────  Theme & server settings      │
│  .github/workflows/keep_alive.yml  GitHub Actions pinger      │
└───────────────────────────────────────────────────────────────┘
```

Each sub-app enforces authentication independently — there is no unauthenticated route anywhere.

---

## Repository Structure

```
hr-management-system/
├── app.py                          # Main hub (entry point)
├── requirements.txt
├── keep_alive.py                   # Optional local keep-alive script
├── generate_users.py               # CLI tool to create hashed user accounts
│
├── auth/
│   ├── __init__.py
│   ├── auth.py                     # Login, session, RBAC logic
│   └── users.json                  # Dev user store (DO NOT commit in prod)
│
├── utils/
│   ├── __init__.py
│   └── ui.py                       # Shared CSS, user bar, page headers
│
├── apps/
│   ├── attendance/
│   │   └── app.py
│   ├── business_appraisal/
│   │   └── app.py
│   ├── staff_appraisal/
│   │   └── app.py
│   └── admin_panel/
│       └── app.py
│
├── static/
│   └── logo.png                    # Cardstel logo (add your file here)
│
├── data/                           # Business appraisal CSV files (gitignored)
├── daily-attendance/               # Attendance CSV files (gitignored)
├── leave-management/               # Leave CSV files (gitignored)
├── reports/                        # Staff report monthly folders (gitignored)
│
├── .streamlit/
│   ├── config.toml                 # Theme + server settings
│   └── secrets.toml.example        # Template — copy & fill, never commit
│
├── .github/
│   └── workflows/
│       └── keep_alive.yml          # Scheduled pinger (every 14 min)
│
└── .gitignore
```

---

## Quick Start (Local Dev)

```bash
# 1. Clone
git clone https://github.com/your-org/hr-management-system.git
cd hr-management-system

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up secrets
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edit secrets.toml with your PASSWORD_SALT and other values

# 5. Add your logo
cp /path/to/cardstel_logo.png static/logo.png

# 6. Run the hub
streamlit run app.py

# 7. Run a specific sub-app directly
streamlit run apps/attendance/app.py
```

**Default dev credentials** (change before deploying):

| Username | Password | Role |
|---|---|---|
| admin | Admin@2024! | Administrator |
| hr.manager | HR@2024! | HR Manager |
| dept.manager | Dept@2024! | Department Manager |

---

## Authentication & RBAC

### How it works
- Every page calls `require_auth(page_key)` as the first action
- If not logged in → login page shown, app stops
- If logged in but wrong role → "Access Denied" shown, app stops
- Sessions expire after 8 hours of inactivity (configurable)
- 5 failed login attempts triggers a 5-minute lockout

### Role Permissions

| Module | admin | hr_manager | dept_manager | employee |
|---|:---:|:---:|:---:|:---:|
| Home Hub | ✅ | ✅ | ✅ | ✅ |
| Attendance | ✅ | ✅ | ❌ | ❌ |
| Business Appraisal | ✅ | ❌ | ✅ | ❌ |
| Staff Appraisal | ✅ | ✅ | ❌ | ❌ |
| Admin Panel | ✅ | ❌ | ❌ | ❌ |

---

## Deployment on Streamlit Community Cloud

### Step 1 — Push to GitHub
```bash
git add .
git commit -m "Initial production deployment"
git push origin main
```

> **Critical:** Ensure `auth/users.json` and `.streamlit/secrets.toml` are in `.gitignore` — never push real credentials.

### Step 2 — Deploy each app
Go to [share.streamlit.io](https://share.streamlit.io) and deploy:

| App | Main file path |
|---|---|
| Main Hub | `app.py` |
| Attendance | `apps/attendance/app.py` |
| Business Appraisal | `apps/business_appraisal/app.py` |
| Staff Appraisal | `apps/staff_appraisal/app.py` |
| Admin Panel | `apps/admin_panel/app.py` |

### Step 3 — Add Secrets in Streamlit Cloud
In each app's Settings → Secrets, paste:
```toml
PASSWORD_SALT = "your-long-random-secret-string"
SESSION_TIMEOUT_MINUTES = "480"
USER_ACCOUNTS = '{"admin":{"password_hash":"<hash>","role":"admin","name":"Admin","email":"admin@cardstel.com"}}'
```

Generate hashes using:
```bash
python generate_users.py
```

---

## Keep-Alive: Eliminating Cold Starts

Streamlit Community Cloud **free tier** puts apps to sleep after ~7 days of inactivity. There are two solutions:

### Option A — GitHub Actions (Recommended, Free)
The included workflow `.github/workflows/keep_alive.yml` pings all apps every 14 minutes via GitHub's scheduler.

**Setup:**
1. Go to your repo → Settings → Secrets and variables → Actions
2. Add these secrets:
   - `MAIN_APP_URL` = your main hub URL
   - `ATTENDANCE_URL`, `BUSINESS_URL`, `STAFF_URL`, `ADMIN_URL`
3. Enable Actions in your repo
4. The workflow runs automatically on schedule

### Option B — Streamlit Teams/Enterprise
Upgrade to Streamlit Teams ($) for always-on apps with no cold starts.

### Option C — Self-host on Railway/Render
Deploy as a container on Railway (free tier available) — no sleeping.
```dockerfile
# Dockerfile (add to root if using Railway/Render)
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

---

## Secrets Management

### Never commit
- `.streamlit/secrets.toml`
- `auth/users.json` (production version with real password hashes)
- `employee.csv` and any data CSVs (contain PII)

### In production
Store all secrets in **Streamlit Cloud Secrets** (per-app) or as environment variables. The auth module reads from:
1. `os.environ.get("USER_ACCOUNTS")` — JSON string of all users
2. `os.environ.get("PASSWORD_SALT")` — password hashing salt
3. Falls back to `auth/users.json` for local development only

---

## Adding / Changing Users

### In development
Edit `auth/users.json` directly (it's gitignored).

### In production
```bash
# Run the interactive user generator
python generate_users.py
```

Copy the output JSON into Streamlit Cloud Secrets as `USER_ACCOUNTS`.

### Manually compute a hash
```python
import hashlib
salt = "your-PASSWORD_SALT-value"
password = "NewUser@2024!"
print(hashlib.sha256(f"{salt}{password}".encode()).hexdigest())
```

---

## Sub-App Configuration

When running as separate Streamlit apps (multi-app mode), set these environment variables or Streamlit secrets so the hub links correctly:

```toml
ATTENDANCE_URL         = "https://staff-attendance.streamlit.app/"
BUSINESS_APPRAISAL_URL = "https://business-department.streamlit.app/"
STAFF_APPRAISAL_URL    = "https://staff-performance.streamlit.app/"
ADMIN_PANEL_URL        = "https://management-panel.streamlit.app/"
```

---

## Security Notes

1. **No public routes** — every page enforces `require_auth()` before any content renders
2. **Brute-force protection** — 5 failed attempts = 5-minute lockout
3. **Session expiry** — auto-logout after configurable inactivity period
4. **Constant-time comparison** — `hmac.compare_digest` prevents timing attacks
5. **Secrets via env** — no hardcoded credentials in source code
6. **XSRF protection** — enabled in `.streamlit/config.toml`
7. **Data files gitignored** — CSVs with employee PII never enter version control
8. **Password hashing** — SHA-256 with server-side salt (upgrade to bcrypt for higher security needs)

---

*© 2024 Cardstel Solutions Limited — Internal Use Only*
