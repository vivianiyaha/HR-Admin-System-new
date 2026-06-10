"""
Shared UI utilities used across all app pages.
"""

import streamlit as st
import os
import sys

# Ensure auth is importable from sub-apps
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from auth import get_current_user, logout, ROLES


# ─────────────────────────────────────────────
# GLOBAL CSS
# ─────────────────────────────────────────────

GLOBAL_CSS = """
<style>
/* ── Reset & base ───────────────────────────── */
.stApp { background-color: #ffffff; }
.block-container { padding-top: 1rem; }

/* ── Typography ─────────────────────────────── */
h1, h2, h3 { color: #111827; }

/* ── Top user bar ───────────────────────────── */
.user-bar {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    gap: 14px;
    padding: 8px 0 16px;
    border-bottom: 1px solid #f3f4f6;
    margin-bottom: 20px;
}

.user-badge {
    background: #fff7ed;
    border: 1.5px solid #fed7aa;
    color: #9a3412;
    font-size: 13px;
    font-weight: 600;
    padding: 4px 12px;
    border-radius: 999px;
}

.role-badge {
    background: #f3f4f6;
    color: #374151;
    font-size: 12px;
    padding: 4px 10px;
    border-radius: 999px;
    font-weight: 500;
}

/* ── Cards ──────────────────────────────────── */
.card {
    background: #ffffff;
    padding: 25px;
    border-radius: 18px;
    border-left: 5px solid #ff6b00;
    box-shadow: 0 4px 15px rgba(0,0,0,0.07);
    margin-bottom: 15px;
    border: 1px solid #f3f4f6;
    border-left: 5px solid #ff6b00;
    transition: transform 0.2s, box-shadow 0.2s;
}
.card:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 24px rgba(0,0,0,0.11);
}
.card h3 { color: #111827; margin-bottom: 10px; }
.card p  { color: #4b5563; line-height: 1.6; font-size: 15px; }

/* ── Primary buttons ────────────────────────── */
div.stLinkButton > a,
.stButton > button[kind="primary"] {
    background: #ff6b00 !important;
    color: white !important;
    border-radius: 10px !important;
    border: none !important;
    padding: 12px 18px !important;
    font-weight: 700 !important;
    width: 100% !important;
    text-decoration: none !important;
}

/* ── Sidebar ────────────────────────────────── */
section[data-testid="stSidebar"] {
    background-color: #111827 !important;
}
section[data-testid="stSidebar"] * {
    color: #f9fafb !important;
}
section[data-testid="stSidebar"] .stRadio > label {
    color: #d1d5db !important;
}

/* ── Metrics ────────────────────────────────── */
[data-testid="stMetricValue"] {
    color: #ff6b00 !important;
    font-weight: 800;
}

/* ── Alerts ─────────────────────────────────── */
.stAlert p { color: #111827 !important; }
</style>
"""


def inject_global_css():
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# USER HEADER BAR
# ─────────────────────────────────────────────

def render_user_bar():
    """Renders the top-right user info + logout bar."""
    user = get_current_user()
    if not user:
        return

    role_label = ROLES.get(user["role"], {}).get("label", user["role"])

    col1, col2, col3 = st.columns([6, 2, 1])
    with col2:
        st.markdown(
            f'<div style="text-align:right;padding-top:6px;">'
            f'<span class="user-badge">👤 {user["name"]}</span> '
            f'<span class="role-badge">{role_label}</span>'
            f'</div>',
            unsafe_allow_html=True
        )
    with col3:
        if st.button("Sign Out", type="secondary", use_container_width=True):
            logout()
            st.rerun()


# ─────────────────────────────────────────────
# PAGE HEADER
# ─────────────────────────────────────────────

def render_page_header(title: str, subtitle: str = "", logo: bool = True):
    """Renders the standard Cardstel page header."""
    inject_global_css()
    render_user_bar()

    if logo:
        logo_path = os.path.join(ROOT, "static", "logo.png")
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            if os.path.exists(logo_path):
                st.image(logo_path, width=380)

    st.markdown(f'<div style="font-size:38px;font-weight:800;text-align:center;color:#111827;margin:8px 0 4px;">{title}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div style="text-align:center;color:#6b7280;font-size:17px;margin-bottom:28px;">{subtitle}</div>', unsafe_allow_html=True)
