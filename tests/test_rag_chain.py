"""
Integration tests for rag_chain.py
"""

from src.rag_chain import ask_question


def test_ask_question_returns_answer():
    """
    Verify that the RAG pipeline returns
    an answer and a list of retrieved documents.

    NOTE:
    Before running this test, ensure that:
    - At least one PDF has been indexed.
    - GOOGLE_API_KEY is configured.
    """

    question = "Summarize the uploaded document."

    answer, documents = ask_question(question)

    assert isinstance(answer, str)
    assert len(answer) > 0

    assert isinstance(documents, list)

    if documents:
        assert hasattr(documents[0], "page_content")
        assert hasattr(documents[0], "metadata")