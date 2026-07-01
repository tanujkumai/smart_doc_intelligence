"""
Vector Store Module
-------------------
Handles embedding generation and vector database operations
using ChromaDB.
"""

import logging
from pathlib import Path
from typing import Any

from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_community.embeddings import HuggingFaceEmbeddings

# ============================================================
# CONFIGURATION
# ============================================================

LOGGER = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
CHROMA_DB_PATH = BASE_DIR / "data" / "chroma_db"

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

DEFAULT_SEARCH_K = 4

# ============================================================
# EMBEDDING MODEL
# ============================================================

embedding_function = HuggingFaceEmbeddings(
    model_name=EMBEDDING_MODEL,
)

# ============================================================
# CHROMA DATABASE
# ============================================================

vector_store = Chroma(
    persist_directory=str(CHROMA_DB_PATH),
    embedding_function=embedding_function,
)

# ============================================================
# VECTOR STORE OPERATIONS
# ============================================================


def add_documents(chunks: list[dict[str, Any]]) -> None:
    """
    Add document chunks to the vector database.

    Parameters
    ----------
    chunks : list
        List of processed document chunks.
    """

    if not chunks:

        LOGGER.warning(
            "No document chunks received."
        )

        return

    documents = []

    document_ids = []

    for chunk in chunks:

        documents.append(
            Document(
                page_content=chunk["text"],
                metadata={
                    "page": chunk["page"],
                    "chunk_id": chunk["id"],
                    "source_file": chunk.get(
                        "source_file",
                        "Unknown",
                    ),
                },
            )
        )

        document_ids.append(str(chunk["id"]))

    try:

        vector_store.add_documents(
            documents=documents,
            ids=document_ids,
        )

        LOGGER.info(
            "Indexed %d document chunks.",
            len(documents),
        )

    except Exception:

        LOGGER.exception(
            "Failed to add documents to ChromaDB."
        )

        raise


# ============================================================
# SEARCH OPERATIONS
# ============================================================


def similarity_search(
    query: str,
    k: int = DEFAULT_SEARCH_K,
):
    """
    Perform semantic similarity search.

    Returns
    -------
    list[Document]
    """

    return vector_store.similarity_search(
        query=query,
        k=k,
    )


def similarity_search_with_score(
    query: str,
    k: int = DEFAULT_SEARCH_K,
):
    """
    Perform similarity search and return scores.
    """

    return vector_store.similarity_search_with_score(
        query=query,
        k=k,
    )


# ============================================================
# DATABASE MANAGEMENT
# ============================================================


def clear_database() -> None:
    """
    Remove all indexed documents.
    """

    try:

        vector_store.delete_collection()

        LOGGER.info(
            "Vector database cleared."
        )

    except Exception:

        LOGGER.exception(
            "Unable to clear vector database."
        )

        raise


def get_retriever(
    k: int = DEFAULT_SEARCH_K,
):
    """
    Return LangChain retriever.
    """

    return vector_store.as_retriever(
        search_kwargs={"k": k},
    )