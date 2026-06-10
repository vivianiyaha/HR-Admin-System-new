"""
HR/Admin Management System — Main Hub
Cardstel Solutions Limited
"""

import os
import sys

# ─── Path setup so sub-modules resolve correctly ───
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import streamlit as st


from utils.ui import inject_global_css, render_user_bar

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="HR/Admin Management System",
    page_icon="static/logo.png" if os.path.exists("static/logo.png") else "🏢",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─────────────────────────────────────────────
# AUTH GUARD
# ─────────────────────────────────────────────
require_auth("home")

# ─────────────────────────────────────────────
# UI
# ─────────────────────────────────────────────
inject_global_css()
render_user_bar()

# Logo
logo_path = os.path.join(ROOT, "static", "logo.png")
c1, c2, c3 = st.columns([1, 2, 1])
with c2:
    if os.path.exists(logo_path):
        st.image(logo_path, width=400)

st.markdown(
    '<div style="font-size:42px;font-weight:800;text-align:center;color:#111827;margin:10px 0 5px;">HR/ADMIN MANAGEMENT SYSTEM</div>',
    unsafe_allow_html=True
)
st.markdown(
    '<div style="text-align:center;color:#6b7280;font-size:18px;margin-bottom:35px;">Smart HR Operations & Employee Analytics Platform</div>',
    unsafe_allow_html=True
)

# ─────────────────────────────────────────────
# MODULE CARDS
# ─────────────────────────────────────────────

MODULES = [
    {
        "key": "attendance",
        "icon": "📅",
        "title": "Attendance Management",
        "desc": "Track employee attendance records, punctuality, daily check-ins, and workforce presence.",
        "url": os.environ.get("ATTENDANCE_URL", "https://staff-attendance.streamlit.app/"),
        "btn": "Open Attendance System",
    },
    {
        "key": "business_appraisal",
        "icon": "💼",
        "title": "Business Department Appraisal",
        "desc": "Tracks business department productivity, targets, efficiency, and overall departmental performance.",
        "url": os.environ.get("BUSINESS_APPRAISAL_URL", "https://business-department.streamlit.app/"),
        "btn": "Open Business Department Appraisal",
    },
    {
        "key": "staff_appraisal",
        "icon": "📝",
        "title": "Staff Performance Appraisal",
        "desc": "Analyze employee productivity, conduct staff appraisals, reviews, and assessment processes efficiently.",
        "url": os.environ.get("STAFF_APPRAISAL_URL", "https://staff-performance.streamlit.app/"),
        "btn": "Open Staff Performance Appraisal",
    },
    {
        "key": "admin_panel",
        "icon": "🛠️",
        "title": "Admin Panel",
        "desc": "Manage high-level administrative tasks, operational setups, and office activities.",
        "url": os.environ.get("ADMIN_PANEL_URL", "https://management-panel.streamlit.app/"),
        "btn": "Open Admin Panel",
    },
]

left_col, right_col = st.columns(2)

for i, mod in enumerate(MODULES):
    col = left_col if i % 2 == 0 else right_col

    with col:
        # Only show modules the user's role can access
        if has_access(mod["key"]):
            st.markdown(f"""
            <div class="card">
                <h3>{mod['icon']} {mod['title']}</h3>
                <p>{mod['desc']}</p>
            </div>
            """, unsafe_allow_html=True)
            st.link_button(mod["btn"], mod["url"], use_container_width=True)
        else:
            st.markdown(f"""
            <div class="card" style="opacity:0.45;border-left-color:#d1d5db;">
                <h3>{mod['icon']} {mod['title']}</h3>
                <p>{mod['desc']}</p>
                <p style="color:#9ca3af;font-size:13px;margin-top:8px;">⛔ Not available for your role</p>
            </div>
            """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
user = get_current_user()
role_label = ROLES.get(user["role"], {}).get("label", "") if user else ""
st.markdown(
    f'<div style="text-align:center;color:#9ca3af;font-size:12px;">'
    f'Logged in as <strong>{user["name"]}</strong> · {role_label} · '
    f'© 2024 Cardstel Solutions Limited</div>',
    unsafe_allow_html=True
)
