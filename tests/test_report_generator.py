"""
Tests for report_generator.py
"""

from pathlib import Path

from src.report_generator import export_chat


def test_export_chat(tmp_path):
    """
    Verify that a DOCX report is created successfully.
    """

    chat_history = [
        {
            "role": "user",
            "content": "What is AI?"
        },
        {
            "role": "assistant",
            "content": "Artificial Intelligence..."
        },
    ]

    output_file = tmp_path / "report.docx"

    export_chat(chat_history, output_file)

    assert output_file.exists()