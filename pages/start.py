from pages.historical_export import render_export
from pages.zipper import render_zipper
from pages.document_export import render_document_export
import streamlit as st


def render_start(go_to):
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

    st.image("http://localhost:8501/app/static/co.png", width=300)
    st.header("Technical Consulting Toolbox")

    st.markdown(
        """
    ---
    **Features**
    """,
        unsafe_allow_html=True,
    )

    with st.expander(
        "**Historical Export** - *Export employee history data into CSV files*",
        expanded=False,
    ):
        st.markdown(
            """
        - Select history start date.
        - Choose identifier field (Profile ID, Employee ID, or E-mail) and select custom fields to export.
        - Generates CSVs (semicolon-delimited) with timeline history.
        """
        )
    with st.expander(
        "**Zipper** - *Compress folders or images into ZIP archives.*",
        expanded=False,
    ):
        st.markdown(
            """
        - Input a root folder containing subdirectories named by a unique identifier.
        - Creates ZIP archives for each numeric subfolder.
        - Outputs in a separate folder and shows a summary of processed, compressed, and failed operations.
        """
        )
    with st.expander(
        "**Document Export** - *Count and download employee documents (single, multiple, photo).*",
        expanded=False,
    ):
        st.markdown(
            """
        - Select fields to process (Photo, DocumentSingle, and DocumentMultiple).
        - Choose an identifier (Username, Profile ID, Employee ID, E-mail) to name employee subfolders.
        - Count the number of documents per type, and download them into `output_folder/<FieldName>/<Identifier>/` subdirectories.
        - Supports Base64 decoding and dynamic progress counters.
        """
        )
    with st.expander(
        "**Field Overview** - *Export available fields from Employees, Lists, and Organizations*",
        expanded=False,
    ):
        st.markdown(
            """
        - Fetch *all* available fields from the Employees, Lists, and Organizations resources.
        - Export results into an Excel workbook with three tabs: Employee Fields, Lists, Organizations.
            """
        )
    st.markdown("---")
    st.markdown(
        """
            **Configuration**
        All API-related pages require:
        - **Domain:** e.g., `reriksson.sb` to form `https://<domain>.catalystone.com/mono/api`.
        - **Client ID and Client Secret:** Credentials for the CatalystOne API.
        - **Include inactive employees:** Toggle to include/exclude.
        Supply these settings via the input fields on each page.
        """
    )

    st.write("Use the menu in the sidebar to select a tool.")
