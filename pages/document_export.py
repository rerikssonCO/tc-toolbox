# tctoolbox/pages/document_export.py
import streamlit as st
import os
import requests
import json
from datetime import datetime


# --- Inline helper functions for API access ---
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


def fetch_employees(base_url: str, token: str, include_inactive: bool) -> list:
    url = f"{base_url}/employees?" f"includeInactive={str(include_inactive).lower()}"
    headers = {
        "Content-Type": "application/json",
        "Api-Version": "v3",
        "Access-Token": token,
    }
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.json().get("employees", [])


# Document export page for counting and downloading employee documents


def render_document_export(go_to):
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
        args=("field_overview",),
        key="btn_sidebar_fields",
    )
    st.title("Document Export")
    st.markdown(
        """
        _Count and download employee documents (single, multiple, photo)._
        """
    )

    st.subheader("API Input", divider="violet")

    # Session state for available document fields
    if "doc_field_opts" not in st.session_state:
        st.session_state.doc_field_opts = []

    # Credentials & config inputs
    domain = st.text_input("Domain", key="doc_domain", placeholder="e.g. reriksson.sb")
    client_id = st.text_input("Client ID", type="password", key="doc_client_id")
    client_secret = st.text_input(
        "Client Secret", type="password", key="doc_client_secret"
    )

    # Load available document fields
    def load_doc_fields():
        if not (domain and client_id and client_secret):
            st.error(
                "Please fill Domain, Client ID and Client Secret before loading fields."
            )
            return
        base_url = f"https://{domain}.catalystone.com/mono/api"
        # Manually fetch token to avoid outdated cache
        token_url = f"{base_url}/accesstoken"
        token_resp = requests.get(
            token_url,
            headers={
                "Client-Id": client_id.strip(),
                "Client-Secret": client_secret.strip(),
                "Grant-Type": "client_credentials",
                "Api-Version": "v3",
            },
        )
        if not token_resp.ok:
            st.error(f"Failed to retrieve access token: {token_resp.text}")
            return
        token_data = token_resp.json()
        token = token_data.get("access_token")
        if not token:
            st.error(f"No access_token in response: {token_data}")
            return
        st.session_state.doc_token = token
        # Fetch employees for field discovery
        resp = requests.get(
            f"{base_url}/employees",
            headers={
                "Access-Token": token,
                "Api-Version": "v3",
                "Accept": "application/json",
            },
        )
        if not resp.ok:
            st.error(
                f"Failed to load employees!\n"
                f"URL: {resp.request.url}\n"
                f"Status code: {resp.status_code}\n"
                f"Response: {resp.text}"
            )
            return
        employees = resp.json().get("employees", [])
        opts = []
        for emp in employees:
            for fid, fld in emp.get("field", {}).items():
                ftype = fld.get("type")
                if ftype in ("PHOTO", "DOCUMENTSINGLE", "DOCUMENTMULTIPLE"):
                    name = fld.get("name", f"Field {fid}")
                    label = f"{fid}: {name} ({ftype})"
                    if label not in opts:
                        opts.append(label)
        opts.sort()
        st.session_state.doc_field_opts = opts
        id_opts = [
            f"{fid}: {fld.get('name', f'Field {fid}')}"
            for emp in employees
            for fid, fld in emp.get("field", {}).items()
            if fid.startswith(("47", "0", "7", "101"))
        ]
        d_opts = sorted(set(id_opts), key=lambda x: int(x.split(":")[0]))
        st.session_state["id_opts_docs"] = d_opts
        st.success(f"Loaded {len(opts)} document fields.")

    st.button(
        "Load document fields", on_click=load_doc_fields, key="btn_load_doc_fields"
    )

    st.subheader("Settings", divider="violet")

    include_inactive = st.checkbox(
        "Include inactive employees", key="doc_include_inactive"
    )
    output_folder = st.text_input(
        "Download folder path",
        key="doc_output_folder",
        placeholder="e.g. /Users/rickard/Downloads",
    )

    identifier = None
    if st.session_state.get("id_opts_docs"):
        identifier = st.selectbox(
            "Identifier",
            st.session_state["id_opts_docs"],
            key="selected_doc_identifier",
        )

    # Field selection (after fields are loaded)
    selected_doc_fields = []
    if st.session_state.doc_field_opts:
        selected_doc_fields = st.multiselect(
            "Select document fields to process",
            st.session_state.doc_field_opts,
            key="selected_doc_fields",
        )

    # Load and count documents
    if st.button("Count Documents", key="btn_count_docs"):
        if not (domain and client_id and client_secret):
            st.error("Please fill Domain, Client ID and Client Secret.")
        else:
            base_url = f"https://{domain}.catalystone.com/mono/api"
            try:
                # Reuse previously loaded access token
                token = st.session_state.get("doc_token")
                if not token:
                    st.error(
                        "Access token missing. Please click 'Load document fields' first."
                    )
                    return
                # Fetch employees for counting documents
                resp = requests.get(
                    f"{base_url}/employees",
                    headers={
                        "Access-Token": token,
                        "Api-Version": "v3",
                        "Accept": "application/json",
                    },
                )
                if not resp.ok:
                    st.error(
                        f"Failed to load employees for count!\n"
                        f"URL: {resp.request.url}\n"
                        f"Status code: {resp.status_code}\n"
                        f"Response: {resp.text}"
                    )
                    return
                employees = resp.json().get("employees", [])
                # Aggregate document counts per type
                counts = {
                    ftype: 0
                    for ftype in ("DOCUMENTSINGLE", "DOCUMENTMULTIPLE", "PHOTO")
                }
                for emp in employees:
                    for sel in selected_doc_fields:
                        fid = sel.split(":")[0]
                        fld = emp.get("field", {}).get(fid)
                        if not fld:
                            continue
                        ftype = fld.get("type")
                        data = fld.get("data")
                        if ftype == "DOCUMENTSINGLE" and data:
                            counts[ftype] += 1
                        elif ftype == "PHOTO" and data:
                            counts[ftype] += 1
                        elif ftype == "DOCUMENTMULTIPLE" and isinstance(data, list):
                            counts[ftype] += len(data)
                # Display summary
                st.write("### Document Counts")
                st.write(f"• Single docs: {counts['DOCUMENTSINGLE']}")
                st.write(f"• Multiple docs: {counts['DOCUMENTMULTIPLE']}")
                st.write(f"• Photos: {counts['PHOTO']}")
            except Exception as e:
                st.error(f"Error counting documents: {e}")

    # Download documents
    if st.button("Download Documents", key="btn_download_docs"):
        if not (domain and client_id and client_secret and output_folder):
            st.error("Please fill Domain, credentials, and output folder.")
        else:
            if not identifier:
                st.error("Please select an identifier before downloading.")
                return
            os.makedirs(output_folder, exist_ok=True)
            base_url = f"https://{domain}.catalystone.com/mono/api"
            try:
                # Reuse previously loaded access token
                token = st.session_state.get("doc_token")
                if not token:
                    st.error(
                        "Access token missing. Please click 'Load document fields' first."
                    )
                    return
                # Prepare per-field folders
                for sel in selected_doc_fields:
                    fid, name_type = sel.split(": ", 1)
                    field_name = name_type.rsplit(" (", 1)[0]
                    os.makedirs(os.path.join(output_folder, field_name), exist_ok=True)
                # Fetch employees for downloading documents
                resp = requests.get(
                    f"{base_url}/employees",
                    headers={
                        "Access-Token": token,
                        "Api-Version": "v3",
                        "Accept": "application/json",
                    },
                )
                if not resp.ok:
                    st.error(
                        f"Failed to load employees for download!\n"
                        f"URL: {resp.request.url}\n"
                        f"Status code: {resp.status_code}\n"
                        f"Response: {resp.text}"
                    )
                    return
                employees = resp.json().get("employees", [])
                errors = []
                total_to_download = 0
                total_downloaded = 0
                for emp in employees:
                    username = emp.get("username")
                    for sel in selected_doc_fields:
                        fid, name_type = sel.split(": ", 1)
                        field_name = name_type.rsplit(" (", 1)[0]
                        fld = emp.get("field", {}).get(fid)
                        if not fld:
                            continue
                        ftype = fld.get("type")
                        data = fld.get("data")
                        if ftype in ("DOCUMENTSINGLE", "PHOTO") and isinstance(
                            data, dict
                        ):
                            total_to_download += 1
                            link = data.get("link", {}).get("href")
                            if link:
                                try:
                                    r = requests.get(
                                        link,
                                        headers={
                                            "Access-Token": token,
                                            "Api-Version": "v3",
                                            "Accept": "application/json",
                                        },
                                    )
                                    r.raise_for_status()
                                    ext = data.get("extension", "dat")
                                    title = data.get("title", "").strip() or fid
                                    # Sanitize title
                                    safe_title = "".join(
                                        c
                                        for c in title
                                        if c.isalnum() or c in (" ", "_", "-")
                                    ).rstrip()
                                    fid_id = identifier.split(":")[0]
                                    emp_name = (
                                        emp.get("field", {})
                                        .get(fid_id, {})
                                        .get("data", {})
                                        .get("value")
                                    ) or emp.get("username")
                                    emp_dir = os.path.join(
                                        output_folder,
                                        field_name,
                                        emp_name or emp.get("username"),
                                    )
                                    os.makedirs(emp_dir, exist_ok=True)
                                    filename = f"{safe_title}.{ext}"
                                    path = os.path.join(emp_dir, filename)
                                    with open(path, "wb") as f:
                                        f.write(r.content)
                                    total_downloaded += 1
                                except Exception as e:
                                    errors.append(f"{username} fid {fid}: {e}")
                        elif ftype == "DOCUMENTMULTIPLE" and isinstance(data, list):
                            for idx, item in enumerate(data):
                                total_to_download += 1
                                link = item.get("link", {}).get("href")
                                if link:
                                    try:
                                        r = requests.get(
                                            link,
                                            headers={
                                                "Access-Token": token,
                                                "Api-Version": "v3",
                                                "Accept": "application/json",
                                            },
                                        )
                                        r.raise_for_status()
                                        ext = item.get("extension", "dat")
                                        title = (
                                            item.get("title", "").strip()
                                            or f"{fid}_{idx}"
                                        )
                                        safe_title = "".join(
                                            c
                                            for c in title
                                            if c.isalnum() or c in (" ", "_", "-")
                                        ).rstrip()
                                        fid_id = identifier.split(":")[0]
                                        emp_name = (
                                            emp.get("field", {})
                                            .get(fid_id, {})
                                            .get("data", {})
                                            .get("value")
                                        ) or emp.get("username")
                                        emp_dir = os.path.join(
                                            output_folder,
                                            field_name,
                                            emp_name or emp.get("username"),
                                        )
                                        os.makedirs(emp_dir, exist_ok=True)
                                        filename = f"{safe_title}.{ext}"
                                        path = os.path.join(emp_dir, filename)
                                        with open(path, "wb") as f:
                                            f.write(r.content)
                                        total_downloaded += 1
                                    except Exception as e:
                                        errors.append(
                                            f"{username} fid {fid} idx {idx}: {e}"
                                        )
                st.write(
                    f"Downloaded {total_downloaded} of {total_to_download} documents."
                )
                if errors:
                    st.error(f"Errors downloading documents:\n" + "\n".join(errors))
                else:
                    st.success("All documents downloaded successfully.")
            except Exception as e:
                st.error(f"Error during document download: {e}")
