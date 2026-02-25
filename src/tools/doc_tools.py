"""
DocAnalyst tooling stubs.

TODO:
- ingest_pdf(path) -> chunks/index
- query_pdf(question) -> citations/answers
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence

import pdfplumber  # type: ignore[import]


@dataclass
class PdfChunk:
    id: int
    page: int
    text: str


def _chunk_text(text: str, max_chars: int = 1200) -> List[str]:
    """Split a long string into roughly max_chars-sized chunks on paragraph boundaries."""
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    chunks: List[str] = []
    current: List[str] = []
    current_len = 0
    for para in paragraphs:
        if current_len + len(para) > max_chars and current:
            chunks.append("\n".join(current))
            current = []
            current_len = 0
        current.append(para)
        current_len += len(para) + 1
    if current:
        chunks.append("\n".join(current))
    return chunks


def ingest_pdf(path: str) -> List[PdfChunk]:
    """
    Ingest a PDF into lightweight chunks (RAG-lite).

    Returns a list of PdfChunk objects containing page and text.
    """
    pdf_path = Path(path)
    chunks: List[PdfChunk] = []
    chunk_id = 0
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page_index, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            for piece in _chunk_text(text):
                chunks.append(PdfChunk(id=chunk_id, page=page_index, text=piece))
                chunk_id += 1
    return chunks


def query_pdf(chunks: Sequence[PdfChunk], question: str, top_k: int = 5) -> List[PdfChunk]:
    """
    Very simple keyword-based "RAG-lite" retrieval over PdfChunk objects.

    Scores chunks by how many query terms they contain and returns the top_k.
    """
    terms = [t.lower() for t in question.split() if t.strip()]
    scored: List[tuple[int, PdfChunk]] = []
    for chunk in chunks:
        text_lower = chunk.text.lower()
        score = sum(text_lower.count(term) for term in terms)
        if score > 0:
            scored.append((score, chunk))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [c for _, c in scored[:top_k]]


