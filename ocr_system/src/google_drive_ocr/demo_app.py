from __future__ import annotations

from pathlib import Path
import sys

import streamlit as st  # type: ignore

try:
    from src.google_drive_ocr.service import GoogleDriveOCRModule
except ModuleNotFoundError:
    project_root = Path(__file__).resolve().parents[2]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from src.google_drive_ocr.service import GoogleDriveOCRModule

try:
    from streamlit.runtime.scriptrunner import get_script_run_ctx
except Exception:
    get_script_run_ctx = None

if __name__ == "__main__" and get_script_run_ctx and get_script_run_ctx() is None:
    print("This UI must be launched with Streamlit.")
    print("Run: python run_google_ocr_demo.py")
    raise SystemExit(0)


@st.cache_resource
def get_service() -> GoogleDriveOCRModule:
    return GoogleDriveOCRModule()


st.set_page_config(
    page_title="Google OCR Demo",
    page_icon="🧠",
    layout="wide",
)

st.markdown(
    """
    <style>
            [data-testid="stAppViewContainer"] {
        background: linear-gradient(180deg, #0b1020 0%, #111827 30%, #0f172a 100%);
      }
      .block-container {padding-top: 1.3rem;}
      .hero {
        border: 1px solid rgba(255,255,255,0.12);
        background: rgba(255,255,255,0.04);
        border-radius: 16px;
        padding: 1rem 1.2rem;
        margin-bottom: 1rem;
      }
            [data-testid="stTextArea"] textarea {
                background-color: #f8fafc !important;
                color: #111827 !important;
            }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
      <h2 style="margin:0;">Google Drive OCR Demo</h2>
      <p style="margin:0.3rem 0 0 0;opacity:0.85;">
      Upload one image/PDF, or batch-upload multiple PDFs. Text is shown instantly on screen.
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Demo Guide")
    st.write("- Single mode: image or PDF")
    st.write("- Batch mode: PDFs only")
    st.write("- Results are not permanently stored")
    st.divider()
    if st.button("Reset to Main", use_container_width=True):
        st.session_state.single_result = None
        st.session_state.batch_results = None
        st.rerun()

service = get_service()

if "single_result" not in st.session_state:
    st.session_state.single_result = None
if "batch_results" not in st.session_state:
    st.session_state.batch_results = None

tab1, tab2 = st.tabs(["Single OCR", "Batch PDF OCR"])

with tab1:
    uploaded = st.file_uploader(
        "Upload image or PDF",
        type=["png", "jpg", "jpeg", "bmp", "tif", "tiff", "pdf"],
        accept_multiple_files=False,
        key="single_uploader",
    )

    if uploaded and st.button("Extract Text", type="primary", key="single_extract_btn"):
        with st.spinner("Running OCR..."):
            result = service.extract_from_bytes(uploaded.name, uploaded.getvalue())
        st.session_state.single_result = result

    single_result = st.session_state.single_result
    if single_result is not None:
        if not single_result.success:
            st.error(single_result.error or "OCR failed")
            with st.expander("Technical details"):
                st.write(single_result)
        else:
            c1, c2, c3 = st.columns(3)
            c1.metric("File type", single_result.file_type.upper())
            c2.metric("Characters", single_result.characters)
            c3.metric("Words", single_result.words)

            st.subheader("Extracted Text")
            st.text_area("", single_result.text, height=360, label_visibility="collapsed")
            if not single_result.text.strip():
                st.warning("OCR completed but text is empty. Try a clearer image/PDF page.")
            else:
                st.caption("Text rendered successfully.")

with tab2:
    uploaded_pdfs = st.file_uploader(
        "Upload one or more PDFs",
        type=["pdf"],
        accept_multiple_files=True,
        key="batch_uploader",
    )

    if uploaded_pdfs and st.button("Run Batch OCR", type="primary", key="batch_extract_btn"):
        file_payloads = [(f.name, f.getvalue()) for f in uploaded_pdfs]

        with st.spinner("Processing PDFs..."):
            results = service.extract_batch_pdfs(file_payloads)
        st.session_state.batch_results = results

    batch_results = st.session_state.batch_results
    if batch_results:
        success_count = sum(1 for r in batch_results if r.success)
        st.success(f"Completed: {success_count}/{len(batch_results)} successful")

        for idx, result in enumerate(batch_results, start=1):
            label = f"{idx}. {result.file_name}"
            with st.expander(label, expanded=(idx == 1)):
                if not result.success:
                    st.error(result.error or "OCR failed")
                    with st.expander(f"Technical details - {result.file_name}"):
                        st.write(result)
                    continue
                c1, c2 = st.columns(2)
                c1.metric("Characters", result.characters)
                c2.metric("Words", result.words)
                st.text_area(
                    f"Text from {result.file_name}",
                    result.text,
                    height=250,
                    key=f"text_{idx}",
                )
