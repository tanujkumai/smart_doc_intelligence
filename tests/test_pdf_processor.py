"""
Unit tests for pdf_processor.py
"""

from pathlib import Path

from src.pdf_processor import (
    extract_text_from_pdf,
    chunk_pages,
)

SAMPLE_PDF = Path("tests/sample_docs/ai_sample.pdf")


def test_extract_text_from_pdf():
    """
    Verify that text is extracted from a valid PDF.
    """

    pages = extract_text_from_pdf(SAMPLE_PDF)

    assert isinstance(pages, list)
    assert len(pages) > 0

    assert "page" in pages[0]
    assert "text" in pages[0]

    assert isinstance(pages[0]["text"], str)


def test_chunk_pages():
    """
    Verify that extracted pages are split into chunks.
    """

    pages = extract_text_from_pdf(SAMPLE_PDF)

    chunks = chunk_pages(
    pages,
    source_file="ai_sample.pdf",
    )

    assert isinstance(chunks, list)
    assert len(chunks) > 0

    first_chunk = chunks[0]

    assert "id" in first_chunk
    assert "page" in first_chunk
    assert "text" in first_chunk

    assert isinstance(first_chunk["text"], str)