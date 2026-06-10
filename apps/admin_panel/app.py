"""
Admin Document Portal
Cardstel Solutions Limited
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import streamlit as st
import base64
import pandas as pd
import mammoth
from io import BytesIO

from auth import require_auth
from utils.ui import inject_global_css, render_user_bar

st.set_page_config(
    page_title="Admin Panel",
    page_icon="🛠️",
    layout="wide"
)

require_auth("admin_panel")
inject_global_css()

st.markdown("""
<style>
h1, h2, h3, h4, h5, h6 { color: #ff6600 !important; }
section[data-testid="stSidebar"] { background-color: #111827 !important; }
section[data-testid="stSidebar"] * { color: #ffffff !important; }
button[kind="primaryFormSubmit"] {
    background-color: #ff6600 !important;
    color: #ffffff !important;
    border: none !important;
}
</style>
""", unsafe_allow_html=True)

render_user_bar()

# ─── Folders ──────────────────────────────────
FOLDERS = {
    "Meetings":    "Meetings",
    "Reports":     "Reports",
    "Stock":       "Stock_Records",
    "Consumables": "Consumables_Records"
}

for folder_path in FOLDERS.values():
    os.makedirs(folder_path, exist_ok=True)

# ─── Helpers ──────────────────────────────────
def get_files(folder):
    if not os.path.exists(folder):
        st.warning(f"{folder} folder not found")
        return []
    return sorted([f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))])


def read_file_once(file_path):
    try:
        with open(file_path, "rb") as f:
            return f.read()
    except Exception as e:
        st.error(f"Error reading file: {e}")
        return None


def display_file(folder, file_name):
    file_path = os.path.join(folder, file_name)
    if not os.path.exists(file_path):
        st.error("File not found")
        return

    st.subheader(f"📄 {file_name}")
    file_bytes = read_file_once(file_path)
    if file_bytes is None:
        return

    st.download_button("⬇ Download File", data=file_bytes,
                       file_name=file_name, mime="application/octet-stream")

    if file_name.lower().endswith(".pdf"):
        b64 = base64.b64encode(file_bytes).decode("utf-8")
        st.markdown(f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="900px" style="border:none;"></iframe>',
                    unsafe_allow_html=True)

    elif file_name.lower().endswith(".docx"):
        try:
            result = mammoth.convert_to_html(BytesIO(file_bytes))
            st.components.v1.html(
                f'<div style="background:white;padding:20px;border-radius:10px;height:850px;overflow:auto;color:black;border:1px solid #ddd;">{result.value}</div>',
                height=900, scrolling=True
            )
        except Exception as e:
            st.error(f"Error displaying Word document: {e}")

    elif file_name.lower().endswith((".xlsx", ".xls", ".csv")):
        try:
            df = pd.read_csv(file_path) if file_name.lower().endswith(".csv") else pd.read_excel(file_path)
            st.dataframe(df, use_container_width=True)
        except Exception as e:
            st.error(f"Error reading spreadsheet: {e}")

    elif file_name.lower().endswith(".txt"):
        try:
            st.text_area("Preview", file_bytes.decode("utf-8"), height=500)
        except Exception as e:
            st.error(f"Error reading text file: {e}")
    else:
        st.warning("Unsupported file type")


def searchable_selectbox(label, options):
    search = st.text_input(f"🔍 Search {label}")
    filtered = [o for o in options if search.lower() in o.lower()] if search else options
    return st.selectbox(label, ["None"] + filtered)


# ─── Main UI ──────────────────────────────────
st.title("📂 Admin Document Portal")

with st.sidebar:
    st.header("Navigation")
    app_mode = st.radio("Go to:", ["Meetings", "Reports", "Stock", "Consumables"])
    st.markdown("---")

# ─── MEETINGS ─────────────────────────────────
if app_mode == "Meetings":
    with st.sidebar:
        meeting_files = get_files(FOLDERS["Meetings"])
        selected_meeting = st.selectbox("Meetings", ["None"] + meeting_files)
    if selected_meeting != "None":
        display_file(FOLDERS["Meetings"], selected_meeting)
    else:
        st.info("Select a meeting document from the sidebar to view.")

# ─── REPORTS ──────────────────────────────────
elif app_mode == "Reports":
    with st.sidebar:
        report_files = get_files(FOLDERS["Reports"])
        selected_report = st.selectbox("Reports", ["None"] + report_files)
    if selected_report != "None":
        display_file(FOLDERS["Reports"], selected_report)
    else:
        st.info("Select a report document from the sidebar to view.")

# ─── STOCK ────────────────────────────────────
elif app_mode == "Stock":
    with st.sidebar:
        stock_files = get_files(FOLDERS["Stock"])
        selected_stock = searchable_selectbox("Stock Records", stock_files)

    if selected_stock != "None":
        display_file(FOLDERS["Stock"], selected_stock)
        st.markdown("---")

    st.subheader("📦 Stock/Furniture Movement Register")
    register_file = os.path.join(FOLDERS["Stock"], "stock_movement_register.csv")

    if not os.path.exists(register_file):
        pd.DataFrame(columns=["Date", "Item Name", "Quantity", "From Office",
                               "To Office", "Moved By", "Reason"]).to_csv(register_file, index=False)

    with st.expander("➕ Add Stock Movement"):
        with st.form("movement_form"):
            date        = st.date_input("Date")
            item        = st.text_input("Item Name")
            qty         = st.number_input("Quantity", min_value=1, step=1)
            from_office = st.text_input("From Office")
            to_office   = st.text_input("To Office")
            moved_by    = st.text_input("Moved By")
            reason      = st.text_area("Reason")
            submit      = st.form_submit_button("Save Movement")

            if submit:
                if item and from_office and to_office:
                    new_data = pd.DataFrame([{
                        "Date": date, "Item Name": item, "Quantity": qty,
                        "From Office": from_office, "To Office": to_office,
                        "Moved By": moved_by, "Reason": reason
                    }])
                    df = pd.read_csv(register_file)
                    df = pd.concat([df, new_data], ignore_index=True)
                    df.to_csv(register_file, index=False)

                    clean_name = "".join([c if c.isalnum() else "_" for c in item])
                    generated_filepath = os.path.join(FOLDERS["Stock"], f"Movement_{date}_{clean_name}.csv")
                    try:
                        new_data.to_csv(generated_filepath, index=False)
                        st.success(f"Saved! Generated: Movement_{date}_{clean_name}.csv")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Saved to register but file generation failed: {e}")
                else:
                    st.error("Please fill required fields")

    st.subheader("📋 Movement History")
    try:
        df = pd.read_csv(register_file)
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇ Download Register", csv, "stock_movement_register.csv", "text/csv")
    except Exception as e:
        st.error(f"Error loading register: {e}")

# ─── CONSUMABLES ──────────────────────────────
elif app_mode == "Consumables":
    with st.sidebar:
        consumable_files = get_files(FOLDERS["Consumables"])
        selected_consumable = searchable_selectbox("Consumables", consumable_files)
    if selected_consumable != "None":
        display_file(FOLDERS["Consumables"], selected_consumable)
    else:
        st.info("Select a consumable record document from the sidebar to view.")
