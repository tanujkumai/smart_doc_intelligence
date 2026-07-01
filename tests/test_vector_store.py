"""
Unit tests for vector_store.py
"""

from pathlib import Path

from src.pdf_processor import (
    extract_text_from_pdf,
    chunk_pages,
)
from src.vector_store import (
    add_documents,
    similarity_search,
    clear_database,
)

SAMPLE_PDF = Path("tests/sample_docs/ai_sample.pdf")


def test_add_documents():
    """
    Verify that document chunks are added
    to the vector database.
    """

    clear_database()

    pages = extract_text_from_pdf(SAMPLE_PDF)

    chunks = chunk_pages(
    pages,
    source_file="ai_sample.pdf",
    )

    add_documents(chunks)

    results = similarity_search(
        "document",
        k=1,
    )

    assert isinstance(results, list)
    assert len(results) > 0


def test_similarity_search():
    """
    Verify that similarity search
    returns Document objects.
    """

    results = similarity_search(
        "summary",
        k=2,
    )

    assert isinstance(results, list)

    if results:

        assert hasattr(
            results[0],
            "page_content",
        )

        assert hasattr(
            results[0],
            "metadata",
        )