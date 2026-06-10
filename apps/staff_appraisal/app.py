"""
Staff Performance Appraisal System
Cardstel Solutions Limited
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import streamlit as st
import pandas as pd
import plotly.express as px

from auth import require_auth
from utils.ui import inject_global_css, render_user_bar

st.set_page_config(
    page_title="Staff Appraisal System",
    page_icon="📝",
    layout="wide"
)

require_auth("staff_appraisal")
inject_global_css()
render_user_bar()

st.title("Staff Performance Appraisal Dashboard")

BASE_DIR = "reports"

month_folders = sorted([
    f for f in os.listdir(BASE_DIR)
    if os.path.isdir(os.path.join(BASE_DIR, f))
]) if os.path.exists(BASE_DIR) else []

if not month_folders:
    st.warning("No report folders found in /reports directory.")
    st.stop()

selected_month = st.selectbox("Select Month", month_folders)
month_path = os.path.join(BASE_DIR, selected_month)

files = [f for f in os.listdir(month_path) if f.endswith(".csv")]
if not files:
    st.warning("No CSV files found for selected month.")
    st.stop()

selected_file = st.selectbox("Select Daily Report File", files)

# ─── Load All Monthly Data ────────────────────
all_month_data = []
for file in files:
    try:
        temp_df = pd.read_csv(os.path.join(month_path, file))
        temp_df["Source_File"] = file
        all_month_data.append(temp_df)
    except Exception as e:
        st.warning(f"Could not load {file}: {e}")

monthly_df = pd.concat(all_month_data, ignore_index=True)
monthly_df.columns = monthly_df.columns.str.strip()

# ─── Load Daily File ──────────────────────────
df = pd.read_csv(os.path.join(month_path, selected_file))
df.columns = df.columns.str.strip()

# ─── Scoring ──────────────────────────────────
def task_score(x):
    x = str(x).strip().lower()
    if x == "yes":       return 1
    elif x == "partially": return 0.5
    else:                return 0

for dframe in [df, monthly_df]:
    dframe["Task1_Score"]  = dframe["Was Task 1 completed?"].apply(task_score)
    dframe["Task2_Score"]  = dframe["Was Task 2 completed?"].apply(task_score)
    dframe["Daily_Score"]  = ((dframe["Task1_Score"] + dframe["Task2_Score"]) / 2) * 100

# ─── Monthly Aggregation ──────────────────────
performance = monthly_df.groupby(["Name", "Department", "Designation"]).agg(
    Task1_Score=("Task1_Score", "mean"),
    Task2_Score=("Task2_Score", "mean"),
    Daily_Score=("Daily_Score", "mean")
).reset_index()

performance["Performance %"] = performance["Daily_Score"]
performance = performance.sort_values("Performance %", ascending=False).reset_index(drop=True)
performance["Rank"] = performance.index + 1

top_performers = performance.head(5)
low_performers = performance.tail(5)

# ─── Metrics ──────────────────────────────────
col1, col2, col3 = st.columns(3)
col1.metric("Total Staff",           len(performance))
col2.metric("Top Performer Score",   round(performance["Performance %"].max(), 2))
col3.metric("Lowest Score",          round(performance["Performance %"].min(), 2))

# ─── Pie Chart ────────────────────────────────
st.subheader("Performance Distribution")
performance["Performance Band"] = pd.cut(
    performance["Performance %"],
    bins=[0, 50, 75, 100],
    labels=["Low", "Average", "High"],
    include_lowest=True
)
pie_data = performance["Performance Band"].value_counts().reset_index()
pie_data.columns = ["Band", "Count"]
fig_pie = px.pie(pie_data, names="Band", values="Count",
                 color_discrete_sequence=["black", "orange", "#ffcc99"])
st.plotly_chart(fig_pie, use_container_width=True)

# ─── Bar Chart ────────────────────────────────
st.subheader(f"Monthly Staff Performance Ranking — {selected_month}")
fig_bar = px.bar(performance, x="Name", y="Performance %",
                 color="Performance %",
                 color_continuous_scale=["black", "orange", "white"],
                 text="Performance %")
st.plotly_chart(fig_bar, use_container_width=True)

# ─── Top & Low ────────────────────────────────
col1, col2 = st.columns(2)
with col1:
    st.subheader("🏆 Top Performers")
    st.dataframe(top_performers.reset_index(drop=True), use_container_width=True)
with col2:
    st.subheader("⚠️ Low Performers")
    st.dataframe(low_performers.reset_index(drop=True), use_container_width=True)

st.subheader("Monthly Appraisal Table")
st.dataframe(performance.reset_index(drop=True), use_container_width=True)

# ─── Quarterly ────────────────────────────────
st.subheader("Quarterly Dashboard")

quarter_mapping = {
    "January": "Q1", "February": "Q1", "March": "Q1",
    "April":   "Q2", "May":      "Q2", "June":  "Q2",
    "July":    "Q3", "August":   "Q3", "September": "Q3",
    "October": "Q4", "November": "Q4", "December":  "Q4",
}

selected_quarter = quarter_mapping.get(selected_month, "Q1")
quarter_months = [m for m, q in quarter_mapping.items() if q == selected_quarter]

quarterly_data = []
for month in quarter_months:
    q_path = os.path.join(BASE_DIR, month)
    if os.path.exists(q_path):
        for file in [f for f in os.listdir(q_path) if f.endswith(".csv")]:
            try:
                quarterly_data.append(pd.read_csv(os.path.join(q_path, file)))
            except:
                pass

if quarterly_data:
    quarterly_df = pd.concat(quarterly_data, ignore_index=True)
    quarterly_df.columns = quarterly_df.columns.str.strip()
    quarterly_df["Task1_Score"] = quarterly_df["Was Task 1 completed?"].apply(task_score)
    quarterly_df["Task2_Score"] = quarterly_df["Was Task 2 completed?"].apply(task_score)
    quarterly_df["Daily_Score"] = ((quarterly_df["Task1_Score"] + quarterly_df["Task2_Score"]) / 2) * 100

    quarterly_performance = quarterly_df.groupby("Name")["Daily_Score"].mean().reset_index()
    quarterly_performance.rename(columns={"Daily_Score": "Quarterly Performance %"}, inplace=True)

    fig_quarter = px.bar(quarterly_performance, x="Name", y="Quarterly Performance %",
                         text="Quarterly Performance %", color="Quarterly Performance %",
                         color_continuous_scale=["black", "orange", "white"])
    st.plotly_chart(fig_quarter, use_container_width=True)
    st.dataframe(quarterly_performance, use_container_width=True)

# ─── Challenges ───────────────────────────────
st.subheader("Daily Challenges Report")
if "Challenges faced during the day" in df.columns:
    challenge_df = df[["Name", "Challenges faced during the day"]].reset_index(drop=True)
    challenge_df.index += 1
    st.dataframe(challenge_df, use_container_width=True)

# ─── Non-Submitters ───────────────────────────
st.subheader("Staff Who Did Not Submit Report")
try:
    employee_df = pd.read_csv("employee.csv")
    employee_df.columns = employee_df.columns.str.strip()
    all_staff = set(employee_df["Name"].astype(str).str.strip())
    submitted = set(df["Name"].astype(str).str.strip())
    non_submitters = sorted(list(all_staff - submitted))

    st.metric("Total Non-Submitters", len(non_submitters))
    if non_submitters:
        non_df = pd.DataFrame(non_submitters, columns=["Name"])
        non_df.index += 1
        st.dataframe(non_df, use_container_width=True)
    else:
        st.success("All staff submitted their reports.")
except Exception as e:
    st.error(f"Unable to read employee.csv: {e}")
