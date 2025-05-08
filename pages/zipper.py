# tctoolbox/pages/zipper.py
import streamlit as st
import os
import zipfile


# Inlined from utils.py
def zip_person_files(person_folder: str, zip_output_path: str) -> int:
    """Compress all files in a person_folder into a single ZIP. Returns number of files compressed."""
    file_count = 0
    with zipfile.ZipFile(zip_output_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for filename in os.listdir(person_folder):
            file_path = os.path.join(person_folder, filename)
            if os.path.isfile(file_path):
                try:
                    zipf.write(file_path, filename)
                    file_count += 1
                except Exception:
                    pass
    return file_count


def render_zipper(go_to):
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

    st.title("Zipper")
    st.markdown(
        """
        _Compress folders or images into ZIP archives._
        """
    )

    st.subheader("Select zipping mode", divider="violet")

    # Zipping mode selection
    mode = st.radio(
        "Zipping mode",
        options=["Document-folders", "Photos"],
        key="zip_mode",
        label_visibility="collapsed",
    )
    st.markdown(
        """
        **Document-folders**: _Compress each (employee) subfolder in the root folder into its own ZIP file, named after the folder._

        **Photos**: _Compress individual image files in the root folder into its own ZIP file, named after the image._
        """
    )

    st.subheader("Folder paths", divider="violet")

    # Input fields for paths
    root_folder = st.text_input(
        "Root folder path",
        key="zip_root",
        placeholder="e.g. /Users/rickard/documents-original",
    )
    output_folder = st.text_input(
        "Output folder path",
        key="zip_output",
        placeholder="e.g. /Users/rickard/documents-zip",
    )

    # Dynamic run button label based on mode
    btn_label = "Run Zipper"
    if st.button(btn_label, key="btn_run_zipper"):
        if not root_folder or not output_folder:
            st.error("Please specify both root and output folder paths.")
            return
        os.makedirs(output_folder, exist_ok=True)

        # Initialize counters
        total_items = 0
        total_converted = 0
        total_failed = 0

        try:
            if mode == "Document-folders":
                # Existing per-folder zipping
                for dir_name in os.listdir(root_folder):
                    subfolder = os.path.join(root_folder, dir_name)
                    if os.path.isdir(subfolder) and dir_name.isdigit():
                        total_items += 1
                        zip_path = os.path.join(output_folder, f"{dir_name}.zip")
                        num = zip_person_files(subfolder, zip_path)
                        if num > 0:
                            total_converted += 1
                        else:
                            total_failed += 1
            else:
                # ZIP each photo file in root_folder individually
                for filename in os.listdir(root_folder):
                    if filename.lower().endswith(
                        (".jpg", ".jpeg", ".png", ".bmp", ".gif")
                    ):
                        total_items += 1
                        src = os.path.join(root_folder, filename)
                        zip_name = os.path.splitext(filename)[0] + ".zip"
                        zip_path = os.path.join(output_folder, zip_name)
                        with zipfile.ZipFile(
                            zip_path, "w", zipfile.ZIP_DEFLATED
                        ) as zipf:
                            zipf.write(src, filename)
                            total_converted += 1
        except Exception as e:
            st.error(f"Error during zipping: {e}")
            return

        # Final summary
        st.write("### Summary")
        st.write(f"• Total items processed: {total_items}")
        st.write(f"• Successfully converted: {total_converted}")
        st.write(f"• Failed conversions: {total_failed}")
