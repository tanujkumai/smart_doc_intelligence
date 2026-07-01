"""
PDF Processing Module
---------------------
Handles PDF text extraction and document chunking for the
Smart Document Intelligence System.
"""

import logging
from pathlib import Path
from typing import Any

import fitz
from langchain_text_splitters import RecursiveCharacterTextSplitter

# ============================================================
# CONFIGURATION
# ============================================================

LOGGER = logging.getLogger(__name__)

DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 200

# ============================================================
# PDF TEXT EXTRACTION
# ============================================================


def extract_text_from_pdf(
    pdf_path: str | Path,
) -> list[dict[str, Any]]:
    """
    Extract text from each page of a PDF document.

    Parameters
    ----------
    pdf_path : str | Path
        Path to the PDF file.

    Returns
    -------
    list
        List containing page number and extracted text.

    Example
    -------
    [
        {
            "page": 1,
            "text": "Introduction..."
        }
    ]
    """

    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(
            f"PDF not found: {pdf_path}"
        )

    pages = []

    try:

        with fitz.open(pdf_path) as document:

            LOGGER.info(
                "Opened PDF: %s",
                pdf_path.name,
            )

            for page_number, page in enumerate(
                document,
                start=1,
            ):

                text = page.get_text()

                # Remove unnecessary whitespace
                text = " ".join(text.split())

                if text:

                    pages.append(
                        {
                            "page": page_number,
                            "text": text,
                        }
                    )

        LOGGER.info(
            "Extracted %d pages",
            len(pages),
        )

        return pages

    except Exception:

        LOGGER.exception(
            "Unable to process PDF: %s",
            pdf_path.name,
        )

        raise

# ============================================================
# TEXT CHUNKING
# ============================================================


def chunk_pages(
    pages: list[dict[str, Any]],
    source_file: str = "",
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[dict[str, Any]]:
    """
    Split extracted pages into smaller overlapping chunks.

    Parameters
    ----------
    pages : list
        Extracted pages.

    chunk_size : int
        Maximum chunk size.

    chunk_overlap : int
        Overlap between consecutive chunks.

    Returns
    -------
    list
        List of chunk dictionaries.
    """

    if not pages:

        LOGGER.warning(
            "No pages available for chunking."
        )

        return []

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    chunks = []

    chunk_counter = 1

    for page in pages:

        page_chunks = splitter.split_text(
            page["text"]
        )

        for chunk in page_chunks:

            chunks.append(
                {
                    "id": (f"{source_file}_page_{page['page']}_chunk_{chunk_counter}"),
                    "page": page["page"],
                    "text": chunk,
                }
            )

            chunk_counter += 1

    LOGGER.info(
        "Generated %d text chunks.",
        len(chunks),
    )

    return chunks