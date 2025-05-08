# tctoolbox/pages/field_overview.py
import streamlit as st
import os
import requests
import pandas as pd
from datetime import datetime

from openpyxl.styles import Alignment
from io import BytesIO
import base64


def generate_excel(df_fields, df_lists, df_orgs, domain):
    excel_buffer = BytesIO()
    try:
        with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
            # Write only non-empty DataFrames and track sheet names
            sheet_names = []
            if not df_fields.empty:
                df_fields.to_excel(writer, sheet_name="Employee Fields", index=False)
                sheet_names.append("Employee Fields")
            if not df_lists.empty:
                df_lists.to_excel(writer, sheet_name="Lists", index=False)
                sheet_names.append("Lists")
            if not df_orgs.empty:
                df_orgs.to_excel(writer, sheet_name="Organizations", index=False)
                sheet_names.append("Organizations")

            # Adjust columns and alignment only for included sheets
            for sheet_name in sheet_names:
                worksheet = writer.sheets[sheet_name]
                for idx, col in enumerate(worksheet.columns, 1):
                    max_length = 0
                    column = col[0].column_letter
                    for cell in col:
                        try:
                            val = str(cell.value)
                            if len(val) > max_length:
                                max_length = len(val)
                        except Exception:
                            pass
                    adjusted_width = max_length + 2
                    worksheet.column_dimensions[column].width = adjusted_width
                for row in worksheet.iter_rows():
                    for cell in row:
                        cell.alignment = Alignment(horizontal="left")
        excel_buffer.seek(0)
        safe_domain = domain.replace(".", "_")
        st.download_button(
            label="Download file with available data",
            data=excel_buffer,
            file_name=f"{safe_domain}_field_overview.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    except Exception as e:
        st.error(f"Error creating downloadable Excel file: {e}")


def render_fields_export(go_to):
    # Sidebar navigation
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
        args=("fields_export",),
        key="btn_sidebar_fields_export",
    )

    st.title("Field Overview")
    st.markdown("*Export available fields from Employees, Lists, and Organizations*")

    st.subheader("API Input", divider="violet")

    # Inputs
    domain = st.text_input(
        "Domain", key="fields_domain", placeholder="e.g. reriksson.sb"
    )
    client_id = st.text_input("Client ID", type="password", key="fields_client_id")
    client_secret = st.text_input(
        "Client Secret", type="password", key="fields_client_secret"
    )

    if st.button("Generate Excel", key="btn_generate_excel"):
        # validate inputs
        if not (domain and client_id and client_secret):
            st.error("Please fill in all fields.")
            return

        base_url = f"https://{domain}.catalystone.com/mono/api"
        # get token
        try:
            token = get_token(base_url, client_id, client_secret)
        except Exception as e:
            st.error(f"Access token error: {e}")
            return

        headers = {
            "Access-Token": token,
            "Api-Version": "v3",
            "Accept": "application/json",
        }

        warnings = []

        # 1) Employees fields: fetch all employees to discover all unique field keys
        try:
            resp_emp = requests.get(
                f"{base_url}/employees",
                headers=headers,
                params={"includeInactive": "true"},
            )
            resp_emp.raise_for_status()
            data_emp = resp_emp.json()
            # Extract employees list or treat as empty
            employees = data_emp.get("employees") if isinstance(data_emp, dict) else []
            if not employees:
                # Use API message if available, otherwise default
                msg = (
                    data_emp.get("message", "Empty result from Employees endpoint.")
                    if isinstance(data_emp, dict)
                    else "Invalid response format."
                )
                warnings.append(
                    "⚠️ Failed to fetch Employees resource: Please check API configuration or download file anyway."
                )
                employees = []
        except Exception as e:
            warnings.append(
                "⚠️ Failed to fetch Employees resource: Please check API configuration or download file anyway."
            )
            employees = []

        # Collect unique fields
        all_fields = {}
        for emp in employees:
            for fid, fld in emp.get("field", {}).items():
                if fid not in all_fields:
                    all_fields[fid] = {
                        "name": fld.get("name", ""),
                        "type": fld.get("type", ""),
                    }
        # Build DataFrame
        field_rows = [
            {"ID": fid, "Name": info["name"], "Type": info["type"]}
            for fid, info in all_fields.items()
        ]
        df_fields = pd.DataFrame(field_rows, columns=["ID", "Name", "Type"])
        # Ensure IDs are sorted numerically
        try:
            df_fields["ID"] = pd.to_numeric(df_fields["ID"], errors="coerce")
        except Exception:
            pass
        df_fields = df_fields.sort_values("ID")

        # 2) Lists definitions: fetch scales
        try:
            resp_lst = requests.get(f"{base_url}/lists", headers=headers)
            resp_lst.raise_for_status()
            data_lst = resp_lst.json()
            list_items = data_lst.get("list") if isinstance(data_lst, dict) else []
            if not list_items:
                warnings.append(
                    "⚠️ Failed to fetch Lists resource: Please check API configuration or download file anyway."
                )
                list_items = []
        except Exception:
            warnings.append(
                "⚠️ Failed to fetch Lists resource: Please check API configuration or download file anyway."
            )
            list_items = []
        list_scales = {}
        for item in list_items:
            scale = item.get("scale", {})
            sid = scale.get("id", "")
            sname = scale.get("name", "")
            if sid and sid not in list_scales:
                list_scales[sid] = sname
        list_rows = [{"ID": sid, "Name": sname} for sid, sname in list_scales.items()]
        df_lists = pd.DataFrame(list_rows, columns=["ID", "Name"])
        # Numeric sort on ID
        try:
            df_lists["ID"] = pd.to_numeric(df_lists["ID"], errors="coerce")
        except Exception:
            pass
        df_lists = df_lists.sort_values("ID")

        # 3) Organizations definitions: fetch fields
        try:
            resp_org = requests.get(f"{base_url}/organizations", headers=headers)
            resp_org.raise_for_status()
            data_org = resp_org.json()
            org_items = (
                data_org.get("organizations") if isinstance(data_org, dict) else []
            )
            if not org_items:
                warnings.append(
                    "⚠️ Failed to fetch Organizations resource: Please check API configuration or download file anyway."
                )
                org_items = []
        except Exception:
            warnings.append(
                "⚠️ Failed to fetch Organizations resource: Please check API configuration or download file anyway."
            )
            org_items = []
        org_fields = {}
        for item in org_items:
            for fid, fld in item.get("field", {}).items():
                if fid not in org_fields:
                    org_fields[fid] = fld.get("name", "")
        org_rows = [{"ID": fid, "Name": name} for fid, name in org_fields.items()]
        df_orgs = pd.DataFrame(org_rows, columns=["ID", "Name"])
        # Numeric sort on ID
        try:
            df_orgs["ID"] = pd.to_numeric(df_orgs["ID"], errors="coerce")
        except Exception:
            pass
        df_orgs = df_orgs.sort_values("ID")
        # Show warnings for any missing resources
        for warn in warnings:
            st.warning(warn)

        if df_fields.empty and df_lists.empty and df_orgs.empty:
            st.error(
                "❌ Unable to generate workbook: no data available from Employees, Lists or Organizations."
            )
            return

        # Provide download button regardless of warnings
        generate_excel(df_fields, df_lists, df_orgs, domain)


def get_token(base_url: str, client_id: str, client_secret: str) -> str:
    headers = {
        "Client-Id": client_id.strip(),
        "Client-Secret": client_secret.strip(),
        "Grant-Type": "client_credentials",
        "Api-Version": "v3",
    }
    resp = requests.get(f"{base_url}/accesstoken", headers=headers)
    resp.raise_for_status()
    return resp.json().get("access_token", "")
