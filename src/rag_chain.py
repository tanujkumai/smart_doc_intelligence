"""
RAG Chain Module
----------------
Retrieves relevant document chunks from ChromaDB and
uses Gemini to generate grounded answers.
"""

import logging
import os
from typing import List, Tuple

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_google_genai import ChatGoogleGenerativeAI

from src.vector_store import similarity_search

# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv()

LOGGER = logging.getLogger(__name__)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError(
        "GOOGLE_API_KEY not found. Please configure your .env file."
    )

# ============================================================
# LLM INITIALIZATION
# ============================================================

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=GOOGLE_API_KEY,
    temperature=0.2,
)

# ============================================================
# PROMPT TEMPLATE
# ============================================================

PROMPT_TEMPLATE = """
You are an AI-powered document assistant.

Your job is to answer ONLY using the provided document context.

Rules:

1. Answer ONLY from the provided context.
2. Do NOT use your own knowledge.
3. If the answer is not available, reply exactly:

"I could not find the answer in the uploaded documents."

4. Keep answers clear and concise.
5. If possible, summarize instead of copying large portions.
6. Never invent facts.

------------------------
Document Context
------------------------

{context}

------------------------
User Question
------------------------

{question}
"""

# ============================================================
# HELPER FUNCTIONS
# ============================================================


def build_context(documents: List[Document]) -> str:
    """
    Build formatted context for the LLM prompt.
    """

    context_parts = []

    for document in documents:

        page = document.metadata.get("page", "Unknown")
        source = document.metadata.get("source_file", "Unknown")

        context_parts.append(
            f"""
Source File : {source}
Page        : {page}

Content:
{document.page_content}
"""
        )

    return "\n\n".join(context_parts)


# ============================================================
# MAIN RAG FUNCTION
# ============================================================


def ask_question(
    question: str,
) -> Tuple[str, List[Document]]:
    """
    Retrieve relevant document chunks and generate
    an answer using Gemini.

    Parameters
    ----------
    question : str
        User's question.

    Returns
    -------
    Tuple[str, List[Document]]
        Generated answer and retrieved documents.
    """

    try:

        documents = similarity_search(
            question,
            k=4,
        )

        if not documents:

            return (
                "I could not find the answer in the uploaded documents.",
                [],
            )

        context = build_context(documents)

        prompt = PROMPT_TEMPLATE.format(
            context=context,
            question=question,
        )

        response = llm.invoke(prompt)

        return response.content.strip(), documents

    except Exception:

        LOGGER.exception(
            "Error while generating answer."
        )

        return (
            "An unexpected error occurred while processing your request.",
            [],
        )