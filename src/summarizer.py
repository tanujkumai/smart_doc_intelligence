"""
Document Summarizer Module
--------------------------
Generates structured summaries of uploaded documents
using the Gemini Large Language Model.
"""

import logging

from src.rag_chain import llm

# ============================================================
# CONFIGURATION
# ============================================================

LOGGER = logging.getLogger(__name__)

MAX_INPUT_LENGTH = 15000

SUMMARY_PROMPT = """
You are an AI-powered document summarization assistant.

Your task is to generate a well-structured summary of the provided document.

Instructions:

1. Read the entire document carefully.
2. Write the summary in clear and professional language.
3. Do not invent information that is not present in the document.
4. Keep the summary concise but informative.

Return the output in the following format:

# Executive Summary
(A short overview of the document.)

# Key Points
- Point 1
- Point 2
- Point 3

# Important Findings
- Finding 1
- Finding 2

# Conclusion
(A brief concluding paragraph.)

Document:

{document}
"""


def summarize_document(text: str) -> str:
    """
    Generate a structured summary for a document.

    Parameters
    ----------
    text : str
        Extracted document text.

    Returns
    -------
    str
        Generated document summary.
    """

    if not text.strip():
        return "No document content available for summarization."

    try:

        prompt = SUMMARY_PROMPT.format(
            document=text[:MAX_INPUT_LENGTH]
        )

        response = llm.invoke(prompt)

        LOGGER.info("Document summary generated successfully.")

        return response.content.strip()

    except Exception:

        LOGGER.exception(
            "Failed to generate document summary."
        )

        return (
            "An unexpected error occurred while generating "
            "the document summary."
        )