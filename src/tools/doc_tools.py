"""
DocAnalyst tooling stubs.

TODO:
- ingest_pdf(path) -> chunks/index
- query_pdf(question) -> citations/answers
"""

from __future__ import annotations

from pathlib import Path
from typing import List

import pdfplumber  # type: ignore[import]


def ingest_pdf(path: str) -> List[str]:
    """Very simple PDF ingestion that returns a list of page texts (to refine later)."""
    pdf_path = Path(path)
    pages: List[str] = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            pages.append(page.extract_text() or "")
    return pages


def query_pdf(pages: List[str], question: str) -> str:
    """Placeholder: naive implementation that just returns concatenated text."""
    # NOTE: Replace with real chunking + retrieval logic.
    return "\n\n".join(pages)

