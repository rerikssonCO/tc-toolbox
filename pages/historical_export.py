# tctoolbox/pages/historical_export.py
import streamlit as st
import os, csv, json
import io, zipfile
from datetime import datetime

import requests

# --- API Authentication and Data Fetching Functions ---


def get_token(base_url, client_id, client_secret):
    headers = {
        "Client-Id": client_id.strip(),
        "Client-Secret": client_secret.strip(),
        "Grant-Type": "client_credentials",
        "Api-Version": "v3",
    }
    url = f"{base_url}/accesstoken"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json().get("access_token", "")


def fetch_employees(base_url, token, include_inactive=False, since_date=None):
    # Fetch employee data from the API with optional filters for inactive employees and history since a date
    headers = {
        "Access-Token": token,
        "Api-Version": "v3",
        "Content-Type": "application/json",
    }
    params = {}
    if include_inactive:
        params["includeInactive"] = "true"
    if since_date:
        params["timelineSince"] = since_date
    url = f"{base_url}/employees"
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json().get("employees", [])


def render_export(go_to):
    # --- Sidebar Navigation ---
    st.sidebar.title("🛠 TC Toolbox")
    st.sidebar.markdown("## Menu")
    st.sidebar.button("Start", on_click=go_to, args=("start",), key="btn_sidebar_start")
    st.sidebar.button(
        "Historical Export",
        on_click=go_to,
        args=("historical_export",),
        key="btn_sidebar_historical",
    )
    st.sidebar.button(
        "Zipper", on_click=go_to, args=("zipper",), key="btn_sidebar_zipper"
    )
    st.sidebar.button(
        "Document Export",
        on_click=go_to,
        args=("document_export",),
        key="btn_sidebar_docs",
    )
    st.sidebar.button(
        "Field Overview",
        on_click=go_to,
        args=("field_overview",),
        key="btn_sidebar_fields",
    )

    # --- Page Title and Description ---
    st.title("Historical Export")
    st.markdown(
        """
        *Export employee history data into CSV files.*
        """,
        unsafe_allow_html=True,
    )

    # --- API Input Section ---
    st.subheader("API Input", divider="violet")
    domain = st.text_input("Domain", key="domain", placeholder="e.g. reriksson.sb")
    client_id = st.text_input("Client ID", type="password", key="client_id")
    client_secret = st.text_input("Client Secret", type="password", key="client_secret")

    # Callback to load fields from API and aggregate them for selection
    def load_fields_cb():
        if not (domain and client_id and client_secret):
            st.session_state.load_error = (
                "Please fill Domain, Client ID and Client Secret."
            )
            return
        base_url = f"https://{domain}.catalystone.com/mono/api"
        try:
            token = get_token(base_url, client_id, client_secret)
            # Fetch employees without history for field aggregation
            employees = fetch_employees(base_url, token, include_inactive)
            # Aggregate fields across all employees
            field_map = {}
            for emp in employees:
                for fid, fld in emp.get("field", {}).items():
                    field_map[fid] = fld.get("name", "")
            options = [
                f"{fid}: {name}"
                for fid, name in sorted(field_map.items(), key=lambda x: int(x[0]))
            ]
            id_opts = [
                opt for opt in options if opt.startswith(("47:", "0:", "7:", "101:"))
            ]
            st.session_state.options = options
            st.session_state.id_opts = id_opts
            # st.session_state.employees = employees
            st.session_state.pop("load_error", None)
            st.session_state.load_status = f"Aggregated {len(options)} unique fields."
        except Exception as e:
            st.error(f"Error loading fields: {e}")

    st.button("Load fields", on_click=load_fields_cb, key="btn_load_fields")

    if "load_error" in st.session_state:
        st.error(st.session_state.load_error)

    if "load_status" in st.session_state:
        st.success(st.session_state.load_status)

    # --- Settings Section ---
    st.subheader("Settings", divider="violet")

    include_inactive = st.checkbox("Include inactive employees", key="include_inactive")

    exclude_current = st.checkbox("Exclude the current value", key="exclude_current")

    write_debug = st.checkbox("Write complete JSON-file (backup)", key="write_debug")

    # Initialize session state variables if not present
    if "options" not in st.session_state:
        st.session_state.options = []
        st.session_state.id_opts = []
        st.session_state.employees = []

    # Load options and employees from session state
    options = st.session_state.options
    id_opts = st.session_state.id_opts
    employees = st.session_state.employees

    # --- Date Input for History Filter ---
    since_date = st.text_input(
        "History since (yyyy-MM-dd)",
        value=datetime.today().strftime("%Y-%m-%d"),
        key="since_date",
    )

    identifier = None
    selected_fields = []
    if st.session_state.id_opts:
        identifier = st.selectbox(
            "Identifier", st.session_state.id_opts, key="identifier"
        )
        selected_fields = st.multiselect(
            "Field IDs to export", st.session_state.options, key="fields"
        )
    prefix = st.text_input("Output filename prefix", value="historical_", key="prefix")

    # Callback to run the export process and generate a ZIP archive with CSVs
    def run_export_cb():
        if not (options and identifier and selected_fields):
            st.session_state.export_error = (
                "Ensure you've loaded fields, chosen identifier & fields."
            )
            return

        if not (domain and client_id and client_secret):
            st.session_state.export_error = (
                "Please fill Domain, Client ID and Client Secret."
            )
            return

        base_url = f"https://{domain}.catalystone.com/mono/api"
        try:
            token = get_token(base_url, client_id, client_secret)
            # Fetch employees including history since the specified date
            employees = fetch_employees(base_url, token, include_inactive, since_date)
        except Exception as e:
            st.error(f"Error fetching employees: {e}")
            return

        logs = []
        id_fid, id_name = identifier.split(": ", 1)

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for item in selected_fields:
                fid, fname = item.split(": ", 1)
                safe = "".join(c if c.isalnum() else "_" for c in fname).strip("_")
                csv_buffer = io.StringIO()
                writer = csv.writer(csv_buffer, delimiter=";")
                # Write CSV header row
                writer.writerow(
                    [id_name, "Name", "Username", fname, "Valid From", "Valid To"]
                )
                # Write data rows for each employee and timeline entry
                for emp in employees:
                    id_val = (
                        emp.get("field", {})
                        .get(id_fid, {})
                        .get("data", {})
                        .get("value", "")
                    )
                    for rec in (
                        emp.get("field", {}).get(fid, {}).get("timelineChange", [])
                    ):
                        vf = rec.get("dataValidFrom") or rec.get("lastModified")
                        vt = rec.get("dataValidTo") or ""
                        if exclude_current and not vt:
                            continue
                        d = rec.get("data")
                        if isinstance(d, dict):
                            val = (
                                d.get("value") or d.get("alternativeExportValue") or ""
                            )
                        elif isinstance(d, list):
                            val = ";".join(x.get("value", "") for x in d)
                        else:
                            val = ""
                        writer.writerow(
                            [id_val, emp.get("name"), emp.get("username"), val, vf, vt]
                        )
                # Add CSV to ZIP archive
                zip_file.writestr(f"{prefix}{safe}.csv", csv_buffer.getvalue())

            # Optionally write full JSON backup to ZIP
            if write_debug:
                zip_file.writestr(
                    f"{prefix}debug.json",
                    json.dumps(employees, ensure_ascii=False, indent=2),
                )

        zip_buffer.seek(0)
        st.session_state.pop("export_error", None)
        st.session_state.export_ready = {
            "zip": zip_buffer.getvalue(),
            "filename": f"{prefix}export.zip",
            "message": "Export ready for download.",
        }

    st.button("Run Export", on_click=run_export_cb, key="btn_run_export")

    if "export_error" in st.session_state:
        st.error(st.session_state.export_error)

    if "export_ready" in st.session_state:
        st.success(st.session_state.export_ready["message"])
        st.download_button(
            label="Download ZIP",
            data=st.session_state.export_ready["zip"],
            file_name=st.session_state.export_ready["filename"],
            mime="application/zip",
            key="download_zip",
        )
