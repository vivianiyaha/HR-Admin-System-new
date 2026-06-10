"""
Authentication & Authorization Module
Handles login, session management, and role-based access control.
"""

import streamlit as st
import hashlib
import hmac
import os
import json
import time
from datetime import datetime, timedelta
from typing import Optional

# ─────────────────────────────────────────────
# ROLE DEFINITIONS
# ─────────────────────────────────────────────

ROLES = {
    "admin": {
        "label": "Administrator",
        "access": ["home", "attendance", "business_appraisal", "staff_appraisal", "admin_panel"],
        "color": "#ff6b00"
    },
    "hr_manager": {
        "label": "HR Manager",
        "access": ["home", "attendance", "staff_appraisal"],
        "color": "#2563eb"
    },
    "department_manager": {
        "label": "Department Manager",
        "access": ["home", "business_appraisal"],
        "color": "#16a34a"
    },
    "employee": {
        "label": "Employee",
        "access": ["home"],
        "color": "#6b7280"
    }
}

# ─────────────────────────────────────────────
# PASSWORD UTILITIES
# ─────────────────────────────────────────────

def hash_password(password: str) -> str:
    """SHA-256 hash with salt from environment."""
    salt = os.environ.get("PASSWORD_SALT", "hr_system_default_salt_2024")
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()


def verify_password(plain: str, hashed: str) -> bool:
    """Constant-time comparison to prevent timing attacks."""
    return hmac.compare_digest(hash_password(plain), hashed)


# ─────────────────────────────────────────────
# USER STORE
# Reads from environment variable USER_ACCOUNTS (JSON string)
# Falls back to a local users.json file for dev
# ─────────────────────────────────────────────

def _load_users() -> dict:
    """Load user accounts from env or local file."""
    env_users = os.environ.get("USER_ACCOUNTS")
    if env_users:
        try:
            return json.loads(env_users)
        except json.JSONDecodeError:
            pass

    local_path = os.path.join(os.path.dirname(__file__), "users.json")
    if os.path.exists(local_path):
        with open(local_path) as f:
            return json.load(f)

    # Default dev accounts (change before production!)
    return {
        "admin": {
            "password_hash": hash_password("Admin@2024!"),
            "role": "admin",
            "name": "System Administrator",
            "email": "admin@cardstel.com"
        },
        "hr.manager": {
            "password_hash": hash_password("HR@2024!"),
            "role": "hr_manager",
            "name": "HR Manager",
            "email": "hr@cardstel.com"
        },
        "dept.manager": {
            "password_hash": hash_password("Dept@2024!"),
            "role": "department_manager",
            "name": "Department Manager",
            "email": "dept@cardstel.com"
        }
    }


def get_user(username: str) -> Optional[dict]:
    """Retrieve a user record by username (case-insensitive)."""
    users = _load_users()
    return users.get(username.lower().strip())


# ─────────────────────────────────────────────
# SESSION MANAGEMENT
# ─────────────────────────────────────────────

SESSION_TIMEOUT_MINUTES = int(os.environ.get("SESSION_TIMEOUT_MINUTES", "480"))  # 8 hours default


def _session_expired() -> bool:
    last_activity = st.session_state.get("last_activity")
    if not last_activity:
        return True
    elapsed = (datetime.now() - last_activity).total_seconds() / 60
    return elapsed > SESSION_TIMEOUT_MINUTES


def _refresh_session():
    st.session_state["last_activity"] = datetime.now()


def is_authenticated() -> bool:
    return (
        st.session_state.get("authenticated", False)
        and not _session_expired()
    )


def get_current_user() -> Optional[dict]:
    if is_authenticated():
        _refresh_session()
        return st.session_state.get("current_user")
    return None


def get_current_role() -> Optional[str]:
    user = get_current_user()
    return user["role"] if user else None


def has_access(page: str) -> bool:
    role = get_current_role()
    if not role:
        return False
    return page in ROLES.get(role, {}).get("access", [])


def login(username: str, password: str) -> tuple[bool, str]:
    """
    Attempt login. Returns (success, message).
    Implements a simple brute-force delay after failures.
    """
    # Track failed attempts in session
    attempts = st.session_state.get("login_attempts", 0)
    lockout_until = st.session_state.get("lockout_until", 0)

    if time.time() < lockout_until:
        remaining = int(lockout_until - time.time())
        return False, f"Too many failed attempts. Try again in {remaining}s."

    user = get_user(username)
    if user and verify_password(password, user["password_hash"]):
        st.session_state["authenticated"] = True
        st.session_state["current_user"] = {
            "username": username.lower().strip(),
            "name": user.get("name", username),
            "role": user["role"],
            "email": user.get("email", ""),
        }
        st.session_state["last_activity"] = datetime.now()
        st.session_state["login_attempts"] = 0
        return True, "Login successful"
    else:
        attempts += 1
        st.session_state["login_attempts"] = attempts
        if attempts >= 5:
            st.session_state["lockout_until"] = time.time() + 300  # 5 min lockout
            return False, "Account locked for 5 minutes due to too many failed attempts."
        remaining = 5 - attempts
        return False, f"Invalid username or password. {remaining} attempts remaining."


def logout():
    """Clear all session state."""
    for key in ["authenticated", "current_user", "last_activity", "login_attempts", "lockout_until"]:
        st.session_state.pop(key, None)


# ─────────────────────────────────────────────
# LOGIN UI COMPONENT
# ─────────────────────────────────────────────

def render_login_page():
    """Render the full-screen login page with Cardstel branding."""
    # Inject login CSS
    st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .block-container { padding-top: 0 !important; }

    .login-wrapper {
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 100vh;
        padding: 20px;
    }

    .login-card {
        background: white;
        padding: 48px 40px;
        border-radius: 20px;
        box-shadow: 0 8px 40px rgba(0,0,0,0.10);
        width: 100%;
        max-width: 420px;
        text-align: center;
    }

    .login-logo-area {
        margin-bottom: 32px;
    }

    .login-title {
        font-size: 22px;
        font-weight: 800;
        color: #111827;
        margin-bottom: 4px;
        letter-spacing: -0.3px;
    }

    .login-subtitle {
        color: #6b7280;
        font-size: 14px;
        margin-bottom: 32px;
    }

    .login-divider {
        height: 3px;
        background: linear-gradient(90deg, #ff6b00, #ff9a40);
        border-radius: 2px;
        margin: 0 auto 32px;
        width: 48px;
    }
    </style>
    """, unsafe_allow_html=True)

    # Center the form with columns
    _, center, _ = st.columns([1, 1.6, 1])

    with center:
        st.markdown('<div style="height: 60px;"></div>', unsafe_allow_html=True)

        # Logo
        logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "logo.png")
        if os.path.exists(logo_path):
            st.image(logo_path, width=240)
        else:
            st.markdown("""
            <div style="font-size:28px;font-weight:900;color:#ff6b00;margin-bottom:4px;">
                CARDSTEL
            </div>
            <div style="font-size:13px;color:#6b7280;margin-bottom:4px;">Solutions Limited</div>
            """, unsafe_allow_html=True)

        st.markdown("""
        <div style="font-size:20px;font-weight:800;color:#111827;margin:24px 0 4px;">
            HR/Admin Management System
        </div>
        <div style="color:#6b7280;font-size:14px;margin-bottom:8px;">
            Sign in to access your dashboard
        </div>
        <div style="height:3px;background:linear-gradient(90deg,#ff6b00,#ff9a40);
                    border-radius:2px;width:48px;margin:0 auto 32px;"></div>
        """, unsafe_allow_html=True)

        # Login form
        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submitted = st.form_submit_button("Sign In", use_container_width=True, type="primary")

        if submitted:
            if not username or not password:
                st.error("Please enter both username and password.")
            else:
                success, message = login(username, password)
                if success:
                    st.success("Welcome! Redirecting...")
                    st.rerun()
                else:
                    st.error(message)

        st.markdown("""
        <div style="margin-top:24px;color:#9ca3af;font-size:12px;">
            🔒 Secure access · Authorized personnel only
        </div>
        """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# ACCESS GUARD DECORATOR
# ─────────────────────────────────────────────

def require_auth(page_key: str = None):
    """
    Call at top of any app page. Shows login if not authenticated,
    or access denied if role doesn't permit.
    """
    if not is_authenticated():
        render_login_page()
        st.stop()

    if page_key and not has_access(page_key):
        user = get_current_user()
        st.error(f"⛔ Access Denied — your role ({ROLES[user['role']]['label']}) does not have permission to view this page.")
        st.stop()

    _refresh_session()
