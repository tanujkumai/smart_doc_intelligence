"""
Tests for summarizer.py
"""

from src.summarizer import summarize_document


def test_summarize_document():
    """
    Verify that the summarizer returns a non-empty string.
    """

    sample_text = """
    Artificial Intelligence is transforming industries by
    enabling machines to learn from data and automate tasks.
    """

    summary = summarize_document(sample_text)

    assert isinstance(summary, str)
    assert len(summary) > 0


def test_empty_document():
    """
    Verify behavior with empty input.
    """

    summary = summarize_document("")

    assert summary == "No document content available for summarization."