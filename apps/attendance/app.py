"""
Attendance Management System
Cardstel Solutions Limited
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, time
import plotly.express as px

from auth import require_auth
from utils.ui import inject_global_css, render_user_bar

# ─── Page Config ──────────────────────────────
st.set_page_config(
    page_title="Attendance System",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─── Auth Guard ───────────────────────────────
require_auth("attendance")

# ─── CSS + Header ─────────────────────────────
inject_global_css()

st.markdown("""
<style>
.title { color: #ff6b00; font-size: 34px; font-weight: bold; }
.card-orange {
    background: #ff6b00;
    padding: 15px;
    border-radius: 12px;
    color: white;
    text-align: center;
}
section[data-testid="stSidebar"] { background-color: #111827 !important; }
section[data-testid="stSidebar"] * { color: #f9fafb !important; }
</style>
""", unsafe_allow_html=True)

render_user_bar()

# ─── Folders ──────────────────────────────────
Path("daily-attendance").mkdir(exist_ok=True)
Path("leave-management").mkdir(exist_ok=True)
employee_file = "employee.csv"

if not os.path.exists(employee_file):
    pd.DataFrame({"Name": []}).to_csv(employee_file, index=False)

# ─── Sidebar ──────────────────────────────────
st.sidebar.title("NAVIGATION BAR")
menu = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Attendance Reports", "Leave Management", "HR Analytics"]
)

# ─── Helpers ──────────────────────────────────
def load_employees():
    df = pd.read_csv(employee_file)
    df.columns = df.columns.str.strip()
    if "Name" not in df.columns:
        df["Name"] = ""
    return df

def get_files(folder):
    return [f for f in os.listdir(folder) if f.endswith(".csv")]

def load_attendance(file_path):
    df = pd.read_csv(file_path)
    df.columns = df.columns.str.strip().str.lower()
    df = df.rename(columns={
        "name": "Name", "time in": "Time in", "timein": "Time in",
        "clock in": "Time in", "time out": "Time out", "timeout": "Time out",
        "clock out": "Time out", "date (dd/mm/yy)": "Date"
    })
    return df

# ─── DASHBOARD ────────────────────────────────
if menu == "Dashboard":
    st.markdown('<div class="title">ATTENDANCE DASHBOARD</div>', unsafe_allow_html=True)

    employees  = load_employees()
    att_files  = get_files("daily-attendance")
    leave_files = get_files("leave-management")

    c1, c2, c3 = st.columns(3)
    for col, val, label in [
        (c1, len(employees), "Employees"),
        (c2, len(att_files), "Attendance Files"),
        (c3, len(leave_files), "Leave Files"),
    ]:
        col.markdown(
            f'<div class="card-orange"><h2>{val}</h2><p>{label}</p></div>',
            unsafe_allow_html=True
        )

    employees.index = range(1, len(employees) + 1)
    employees.index.name = "S/N"
    st.subheader("Employees")
    st.dataframe(employees, use_container_width=True)

# ─── ATTENDANCE REPORTS ───────────────────────
elif menu == "Attendance Reports":
    st.markdown('<div class="title">ATTENDANCE REPORTS</div>', unsafe_allow_html=True)

    files = get_files("daily-attendance")
    if not files:
        st.warning("No attendance files found")
    else:
        file = st.selectbox("Select File", files)
        path = os.path.join("daily-attendance", file)
        df = load_attendance(path)

        required = ["Name", "Time in", "Time out"]
        if any(c not in df.columns for c in required):
            st.error("Missing required columns")
            st.stop()

        st.subheader("📋 Attendance List")
        st.dataframe(df, use_container_width=True)

        df["Time in"]  = pd.to_datetime(df["Time in"],  errors="coerce")
        df["Time out"] = pd.to_datetime(df["Time out"], errors="coerce")

        if "Date" in df.columns:
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
            report_date = df["Date"].dropna().iloc[0].date() if not df["Date"].dropna().empty else datetime.today().date()
        else:
            report_date = datetime.today().date()

        AFTERNOON_START = time(12, 0, 0)
        df["Shift"] = np.where(df["Time in"].dt.time >= AFTERNOON_START, "Afternoon/Night Shift", "Day Shift")

        late     = df[(df["Shift"] == "Day Shift") & (df["Time in"].dt.time > time(8, 30))]
        overtime = df[(df["Shift"] == "Day Shift") & (df["Time out"].dt.time > time(19, 0))]

        # Leave check
        staff_on_leave = set()
        for lf in get_files("leave-management"):
            leave_df = pd.read_csv(os.path.join("leave-management", lf))
            if {"Name", "Start Date", "End Date", "Status"}.issubset(leave_df.columns):
                leave_df["Start Date"] = pd.to_datetime(leave_df["Start Date"]).dt.date
                leave_df["End Date"]   = pd.to_datetime(leave_df["End Date"]).dt.date
                approved = leave_df[
                    (leave_df["Status"].str.lower().str.strip() == "approved") &
                    (leave_df["Start Date"] <= report_date) &
                    (leave_df["End Date"] >= report_date)
                ]
                staff_on_leave.update(approved["Name"].astype(str))

        employees_df = load_employees()
        employees_df["Name"] = employees_df["Name"].astype(str).str.strip()
        df["Name"] = df["Name"].astype(str).str.strip()
        df["Time in"] = pd.to_datetime(df["Time in"], errors="coerce")

        staff_on_leave = set(pd.Series(list(staff_on_leave)).astype(str).str.strip().str.lower())
        present_staff  = set(df[df["Time in"].notna()]["Name"].astype(str).str.strip().str.lower().unique())
        all_staff      = set(employees_df["Name"].astype(str).str.strip().str.lower().unique())
        absent_names   = all_staff - present_staff - staff_on_leave

        absentees = employees_df[
            employees_df["Name"].str.strip().str.lower().isin(absent_names)
        ][["Name"]].drop_duplicates().reset_index(drop=True)

        st.subheader("Summary")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Late", len(late))
        c2.metric("Absent", len(absentees))
        c3.metric("Overtime", len(overtime))
        c4.metric("Afternoon/Night Shift", len(df[df["Shift"] == "Afternoon/Night Shift"]))

        for label, data in [
            ("Latecomers", late),
            ("Afternoon/Night Shift", df[df["Shift"] == "Afternoon/Night Shift"]),
            ("Absentees", absentees),
            ("Overtime", overtime),
        ]:
            st.subheader(label)
            st.dataframe(data, use_container_width=True)

# ─── LEAVE MANAGEMENT ─────────────────────────
elif menu == "Leave Management":
    st.markdown('<div class="title">LEAVE MANAGEMENT</div>', unsafe_allow_html=True)

    files = get_files("leave-management")
    if files:
        file = st.selectbox("Select File", files)
        df = pd.read_csv(os.path.join("leave-management", file))
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("No leave data found")

# ─── HR ANALYTICS ─────────────────────────────
elif menu == "HR Analytics":
    st.markdown('<div class="title">HR ANALYTICS</div>', unsafe_allow_html=True)

    employees = load_employees()
    st.metric("Total Employees", len(employees))

    att_files = get_files("daily-attendance")
    if not att_files:
        st.warning("No attendance data available")
    else:
        all_data = []
        for file in att_files:
            try:
                df = load_attendance(os.path.join("daily-attendance", file))
                if "Name" not in df.columns or "Time in" not in df.columns:
                    continue
                df["Name"] = df["Name"].astype(str).str.strip()
                df = df[df["Name"].notna()]
                df["Time in"] = pd.to_datetime(df["Time in"], errors="coerce")
                if "Date" in df.columns:
                    df["Date"] = pd.to_datetime(df["Date"], errors="coerce", dayfirst=True)
                else:
                    df["Date"] = pd.to_datetime(df["Time in"], errors="coerce").dt.date
                all_data.append(df)
            except Exception as e:
                st.warning(f"Could not read {file}: {e}")

        if not all_data:
            st.error("No valid attendance data found")
        else:
            df_all = pd.concat(all_data, ignore_index=True)
            df_all = df_all.dropna(subset=["Name", "Time in", "Date"])
            df_all["Date"] = pd.to_datetime(df_all["Date"], errors="coerce")
            df_all = df_all.dropna(subset=["Date"])
            df_all["Month"] = df_all["Date"].dt.to_period("M").astype(str)

            available_months = sorted(df_all["Month"].dropna().unique(), reverse=True)
            selected_month = st.selectbox("Select Month", ["All"] + available_months)
            if selected_month != "All":
                df_all = df_all[df_all["Month"] == selected_month]

            LATE_TIME = time(8, 30)
            df_all["Late"] = df_all["Time in"].dt.time > LATE_TIME

            monthly_summary = (
                df_all.groupby("Name")
                .agg(
                    Total_Days=("Name", "count"),
                    Late_Count=("Late", "sum"),
                    On_Time_Days=("Late", lambda x: (~x).sum())
                )
                .reset_index()
            )
            monthly_summary["Punctuality (%)"] = (
                monthly_summary["On_Time_Days"] / monthly_summary["Total_Days"] * 100
            ).round(2)
            monthly_summary = monthly_summary.sort_values("Punctuality (%)", ascending=False)

            c1, c2, c3 = st.columns(3)
            c1.metric("Employees Tracked", len(monthly_summary))
            c2.metric("Total Late Records", int(monthly_summary["Late_Count"].sum()))
            c3.metric("Late > 5 Times", len(monthly_summary[monthly_summary["Late_Count"] > 5]))

            st.subheader("📅 Monthly Performance Ranking")
            st.dataframe(monthly_summary, use_container_width=True)

            fig = px.bar(
                monthly_summary.head(10), x="Name", y="Punctuality (%)",
                title="Top Monthly Performers", color="Punctuality (%)",
                color_continuous_scale="Blues"
            )
            st.plotly_chart(fig, use_container_width=True)

            late_staff = monthly_summary[monthly_summary["Late_Count"] > 5]
            st.subheader("⚠ Employees Late More Than 5 Times")
            if late_staff.empty:
                st.success("No employee has been late more than 5 times.")
            else:
                st.dataframe(late_staff[["Name", "Late_Count", "Punctuality (%)"]], use_container_width=True)
                fig = px.bar(
                    late_staff, x="Name", y="Late_Count",
                    title="Late More Than 5 Times", color="Late_Count",
                    color_continuous_scale="Reds"
                )
                st.plotly_chart(fig, use_container_width=True)
