"""
Smart Document Intelligence System
----------------------------------
Main Streamlit Application

Author  : Tanuj Kumai
Project : MCA Major Project
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st

from src.pdf_processor import extract_text_from_pdf, chunk_pages
from src.vector_store import add_documents, clear_database
from src.rag_chain import ask_question
from src.summarizer import summarize_document
from src.report_generator import export_chat

# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("doc_intel_app")

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Smart Document Intelligence System",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / "data" / "uploads"
REPORT_DIR = BASE_DIR / "reports" / "generated_reports"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)

MAX_SUMMARY_CHARS = 15000
MAX_DISPLAY_CHARS = 700

# ============================================================
# SESSION STATE INITIALIZATION
# ============================================================

DEFAULT_SESSION: Dict[str, Any] = {
    "messages": [],
    "uploaded_files": [],
    "chunks_count": 0,
    "summary": None,
    "processing": False,
}

for key, value in DEFAULT_SESSION.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def save_uploaded_file(uploaded_file) -> Path:
    """Save an uploaded PDF to the uploads directory and return its path."""
    save_path = UPLOAD_DIR / uploaded_file.name
    with open(save_path, "wb") as file:
        file.write(uploaded_file.getbuffer())
    logger.info("Saved uploaded file: %s", save_path)
    return save_path


def process_uploaded_documents(uploaded_files: List[Any]) -> None:
    """
    Process a batch of uploaded PDFs end-to-end:
    clear old index -> save -> extract -> chunk -> embed -> store.
    """
    clear_database()
    logger.info("Cleared existing vector database.")

    all_chunks: List[Dict[str, Any]] = []
    uploaded_names: List[str] = []

    for uploaded_file in uploaded_files:
        save_path = save_uploaded_file(uploaded_file)
        uploaded_names.append(uploaded_file.name)

        pages = extract_text_from_pdf(save_path)
        if not pages:
            logger.warning("No extractable text found in %s", uploaded_file.name)
            continue

        chunks = chunk_pages(pages)
        for chunk in chunks:
            chunk["source_file"] = uploaded_file.name

        all_chunks.extend(chunks)
        logger.info("Processed %s -> %d chunks", uploaded_file.name, len(chunks))

    if not all_chunks:
        logger.warning(
            "No text could be extracted from uploaded documents."
        )

        st.error(
            "No text could be extracted from the uploaded document(s). "
            "Please upload a text-based PDF."
        )
        return

    add_documents(all_chunks)

    st.session_state.uploaded_files = uploaded_names
    st.session_state.chunks_count = len(all_chunks)
    st.session_state.summary = None  # invalidate stale summary on new upload


def generate_document_summary() -> None:
    """Generate a combined summary across all currently uploaded PDFs."""
    full_text = ""

    for filename in st.session_state.uploaded_files:
        pdf_path = UPLOAD_DIR / filename
        if not pdf_path.exists():
            logger.warning("Expected uploaded file missing on disk: %s", pdf_path)
            continue

        pages = extract_text_from_pdf(pdf_path)
        for page in pages:
            full_text += page.get("text", "")

    if not full_text.strip():
        st.warning("No document text found to summarize.")
        return

    with st.spinner("Generating summary..."):
        st.session_state.summary = summarize_document(full_text[:MAX_SUMMARY_CHARS])


def render_sources(sources: List[Any]) -> None:
    """Render the source-pages and retrieved-context expanders for an answer."""
    with st.expander("📄 Source Pages", expanded=False):
        pages = sorted(
            {doc.metadata.get("page", "Unknown") for doc in sources},
            key=lambda p: (isinstance(p, str), p),
        )
        st.success(f"Answer generated using page(s): {', '.join(map(str, pages))}")

    with st.expander("🔍 Retrieved Context", expanded=False):
        for index, doc in enumerate(sources, start=1):
            st.markdown(f"### Source {index}")

            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**File:** {doc.metadata.get('source_file', 'Unknown')}")
            with col2:
                st.write(f"**Page:** {doc.metadata.get('page', 'Unknown')}")

            content = doc.page_content
            if len(content) > MAX_DISPLAY_CHARS:
                content = content[:MAX_DISPLAY_CHARS] + "\n\n...(truncated)"
            st.code(content, language=None)
            st.divider()


def handle_user_question(question: str) -> None:
    """Append the user question and the generated assistant answer to history."""
    st.session_state.messages.append({"role": "user", "content": question})

    if not st.session_state.uploaded_files:
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": "Please upload one or more PDF documents first.",
                "sources": [],
            }
        )
        return

    with st.spinner("Thinking..."):
        try:
            answer, docs = ask_question(question)
        except Exception:
            logger.exception("Failed to answer question: %s", question)
            answer = "An unexpected error occurred while processing your request."
            docs = []

    st.session_state.messages.append(
        {"role": "assistant", "content": answer, "sources": docs}
    )


# ============================================================
# HEADER
# ============================================================

st.title("📄 Smart Document Intelligence System")
st.caption(
    "AI-powered Document Question Answering using "
    "Retrieval-Augmented Generation (RAG)"
)

if not st.session_state.uploaded_files:
    st.info(
        "👈 Upload one or more PDF documents from the sidebar "
        "to start asking questions."
    )

# ============================================================
# SIDEBAR — UPLOAD
# ============================================================

st.sidebar.title("Navigation")
st.sidebar.markdown("---")
st.sidebar.header("📂 Upload Documents")

uploaded_files = st.sidebar.file_uploader(
    label="Choose one or more PDF files",
    type=["pdf"],
    accept_multiple_files=True,
)

# Only re-process if the set of uploaded filenames actually changed.
if uploaded_files:
    new_names = sorted(f.name for f in uploaded_files)
    if new_names != sorted(st.session_state.uploaded_files):
        try:
            with st.spinner("Indexing documents..."):
                process_uploaded_documents(uploaded_files)
            st.sidebar.success(f"Successfully indexed {len(uploaded_files)} document(s).")
        except Exception as error:
            logger.exception("Document processing failed.")
            st.sidebar.error(
                "Failed to process the uploaded document(s). "
                "Please verify that the files are valid PDF documents."
            )

# ============================================================
# SIDEBAR — ACTIONS
# ============================================================

st.sidebar.markdown("---")
st.sidebar.header("⚙️ Actions")

if st.sidebar.button("📝 Generate Summary", use_container_width=True):
    if not st.session_state.uploaded_files:
        st.sidebar.warning("Please upload at least one PDF first.")
    else:
        try:
            generate_document_summary()
            if st.session_state.summary:
                st.sidebar.success("Summary generated successfully!")
        except Exception as error:
            logger.exception("Summary generation failed.")
            st.sidebar.error(
                "Unable to generate a summary at this time. "
                "Please try again."
            )

if st.sidebar.button("📥 Export Chat", use_container_width=True):
    if not st.session_state.messages:
        st.sidebar.warning("No chat available to export.")
    else:
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_path = REPORT_DIR / f"chat_report_{timestamp}.docx"
            export_chat(st.session_state.messages, export_path)
            st.sidebar.success(f"Chat exported successfully.\n\n{export_path.name}")
        except Exception as error:
            logger.exception("Chat export failed.")
            st.sidebar.error(
                "Failed to export the chat. Please try again."
            )

if st.sidebar.button("🗑️ Clear Chat", use_container_width=True):
    st.session_state.messages = []
    st.rerun()

# ============================================================
# SIDEBAR — SYSTEM INFO
# ============================================================

st.sidebar.markdown("---")
st.sidebar.header("ℹ️ System Information")

st.sidebar.info(
    """
**Embedding Model**
all-MiniLM-L6-v2

**Vector Database**
ChromaDB

**Large Language Model**
Gemini 2.5 Flash
"""
)

if st.session_state.uploaded_files:
    st.sidebar.markdown("---")
    st.sidebar.subheader("📁 Uploaded Files")

    for filename in st.session_state.uploaded_files:
        st.sidebar.caption(f"📄 {filename}")

    st.sidebar.metric(label="Indexed Chunks", value=st.session_state.chunks_count)

    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 Statistics")
    st.sidebar.metric("Documents", len(st.session_state.uploaded_files))
    st.sidebar.metric("Chunks", st.session_state.chunks_count)
    st.sidebar.metric(
        "Questions Asked",
        len([m for m in st.session_state.messages if m["role"] == "user"]),
    )

# ============================================================
# CHAT INPUT
# ============================================================

question = st.chat_input("Ask a question about your uploaded documents...")

if question:
    handle_user_question(question)

# ============================================================
# CHAT HISTORY
# ============================================================

for msg_index, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        if message["role"] == "assistant" and message.get("sources"):
            render_sources(message["sources"])

# ============================================================
# DOCUMENT SUMMARY
# ============================================================

if st.session_state.summary:
    st.markdown("---")
    st.subheader("📝 Document Summary")
    st.info("Summary generated using Google's Gemini model.")
    st.write(st.session_state.summary)

# ============================================================
# FOOTER
# ============================================================

st.markdown("---")
st.caption(
    "Smart Document Intelligence System | "
    "MCA Major Project | "
    "Built with Streamlit, LangChain, ChromaDB & Gemini"
)