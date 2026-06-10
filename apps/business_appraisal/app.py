"""
Business Department Appraisal System
Cardstel Solutions Limited
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import streamlit as st
import pandas as pd

from auth import require_auth
from utils.ui import inject_global_css, render_user_bar

st.set_page_config(
    page_title="Business Department Appraisal",
    page_icon="💼",
    layout="wide"
)

require_auth("business_appraisal")
inject_global_css()
render_user_bar()

st.title("📊 Monthly Business Development Appraisal")
st.markdown("Fill in the employee monthly KPI performance below.")

# ─── CSV Loader ───────────────────────────────
try:
    data_folder = "data"
    csv_files = [f for f in os.listdir(data_folder) if f.endswith(".csv")]

    if not csv_files:
        st.error("No CSV files found in /data folder")
        st.stop()

    selected_csv = st.selectbox("Select CSV File", csv_files)
    csv_path = os.path.join(data_folder, selected_csv)
    employee_data = pd.read_csv(csv_path)
    employee_data.columns = employee_data.columns.str.strip()
    st.success(f"Loaded: {selected_csv}")

    selected_employee = st.selectbox("Select Employee Name", employee_data["Name"].dropna().unique())
    selected_row = employee_data[employee_data["Name"] == selected_employee].iloc[0]

except Exception as e:
    st.error(f"Could not load employee CSV: {e}")
    st.stop()

# ─── Employee Name ────────────────────────────
employee_name = st.text_input("Employee Name", value=selected_employee)

# ─── KPI Data ─────────────────────────────────
kpi_data = {
    "KPI Area": [
        "Lead Generation", "Client Acquisition", "Revenue Growth",
        "Client Conversion", "Pipeline Management", "Proposal Success",
        "Client Retention", "Customer Relationship", "Business Expansion",
        "Reporting & Compliance", "Team Collaboration", "Professional Conduct"
    ],
    "KPI Measure": [
        "Number of qualified leads generated", "New customers acquired",
        "Sales revenue achieved (₦)", "Client conversion rate",
        "Value of active pipeline (₦)", "Proposal to deal conversion rate",
        "Existing customer retention rate", "Number of repeat customers",
        "New markets/accounts opened", "Timely submission of reports",
        "Feedback from departments", "Attendance, discipline & professionalism"
    ],
    "Target": [3, 2, 200000000, 40, 200000000, 50, 80, 2, 2, 100, 85, 100],
    "Weight (%)": [10, 10, 15, 10, 10, 10, 10, 5, 5, 5, 5, 5]
}

df = pd.DataFrame(kpi_data)

# ─── KPI Input ────────────────────────────────
st.subheader("KPI Appraisal Scorecard")

for i in range(len(df)):
    kpi_name = df.loc[i, "KPI Area"]
    st.markdown(f"### {kpi_name}")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        target = st.number_input(f"Target - {i}", value=float(df.loc[i, "Target"]), key=f"target_{i}")

    default_actual = 0.0
    if kpi_name in employee_data.columns:
        try:
            default_actual = float(selected_row[kpi_name])
        except:
            default_actual = 0.0

    with col2:
        actual = st.number_input(f"Actual Performance - {i}", min_value=0.0, value=default_actual, key=f"actual_{i}")

    with col3:
        weight = df.loc[i, "Weight (%)"]
        st.info(f"Weight: {weight}%")

    with col4:
        achievement = (actual / target * 100) if target > 0 else 0
        achievement = min(achievement, 100)
        weighted_score = (achievement * weight) / 100
        st.success(f"Score: {weighted_score:.2f}")

    df.loc[i, "Actual Performance"] = actual
    df.loc[i, "Score"] = weighted_score

# ─── Final Score ──────────────────────────────
total_score = df["Score"].sum()

st.markdown("---")
st.subheader("Final Appraisal Score")

col1, col2 = st.columns(2)
with col1:
    st.metric("Total Score", f"{total_score:.2f}%")
with col2:
    if   total_score >= 90: rating = "Excellent"
    elif total_score >= 75: rating = "Very Good"
    elif total_score >= 60: rating = "Good"
    elif total_score >= 50: rating = "Average"
    else:                   rating = "Poor"
    st.metric("Performance Rating", rating)

# ─── Summary Table ────────────────────────────
st.subheader("Appraisal Summary")
summary_df = df[["KPI Area", "KPI Measure", "Target", "Weight (%)", "Actual Performance", "Score"]]
st.dataframe(summary_df, use_container_width=True)

# ─── Download ─────────────────────────────────
csv = summary_df.to_csv(index=False).encode("utf-8")
st.download_button(
    label="📥 Download Appraisal Report",
    data=csv,
    file_name=f"{employee_name}_appraisal.csv",
    mime="text/csv"
)
