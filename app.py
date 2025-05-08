# app.py
import streamlit as st
from pages.start import render_start
from pages.historical_export import render_export
from pages.zipper import render_zipper
from pages.document_export import render_document_export
from pages.field_overview import render_fields_export

st.set_page_config(page_title="Technical Consulting Toolbox")

# Dölj Streamlit-menyn och fotnoter
hide_streamlit_style = """
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        .stAppDeployButton {display: none !important;}
        [data-testid="stHeaderActionElements"] {display: none !important;}
        [data-testid="stElementToolbar"] {display: none !important;}
    </style>
    """

st.markdown(hide_streamlit_style, unsafe_allow_html=True)


# Simple session‐based navigation
if "page" not in st.session_state:
    st.session_state.page = "start"


def go_to(page):
    st.session_state.page = page


# Render the correct page
if st.session_state.page == "start":
    render_start(go_to)
elif st.session_state.page == "historical_export":
    render_export(go_to)
elif st.session_state.page == "zipper":
    render_zipper(go_to)
elif st.session_state.page == "document_export":
    render_document_export(go_to)
elif st.session_state.page == "field_overview":
    render_fields_export(go_to)
