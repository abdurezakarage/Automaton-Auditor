"""
Detective layer node stubs (RepoInvestigator, DocAnalyst, VisionInspector).

These will later be wired into a LangGraph StateGraph.
"""

from __future__ import annotations

from typing import Any, Dict, List

from ..state import AgentState, Evidence
from ..tools.repo_tools import (
    analyze_graph_structure,
    clone_repo_to_temp,
    extract_git_history,
)
from ..tools.doc_tools import ingest_pdf, query_pdf


def run_repo_investigator(state: AgentState) -> Dict[str, Any]:
    """Analyze the target repo and populate Evidence objects."""
    evidences: Dict[str, List[Evidence]] = state.get("evidences", {})  # type: ignore[assignment]

    repo_url = state.get("repo_url", "")
    if not repo_url:
        return {"evidences": evidences}

    local_path = clone_repo_to_temp(repo_url)

    # Git history evidence
    history = extract_git_history(local_path)
    evid_git = Evidence(
        goal="git_history",
        found=len(history) > 0,
        content="\n".join(history[:20]),
        location=str(local_path),
        rationale="Collected git log to assess commit granularity and progression.",
        confidence=0.8,
    )

    # Graph wiring evidence
    graph_info = analyze_graph_structure(local_path)
    evid_graph = Evidence(
        goal="graph_orchestration",
        found=bool(graph_info.get("edges")),
        content=str(graph_info),
        location=str(local_path / "src"),
        rationale="Analyzed AST for StateGraph.add_edge fan-out/fan-in patterns.",
        confidence=0.7,
    )

    evidences.setdefault("repo", []).extend([evid_git, evid_graph])
    # Return only the keys we're modifying (LangGraph will merge via reducer)
    return {"evidences": evidences}


def run_doc_analyst(state: AgentState) -> Dict[str, Any]:
    """Analyze the PDF report and populate Evidence objects."""
    evidences: Dict[str, List[Evidence]] = state.get("evidences", {})  # type: ignore[assignment]

    pdf_path = state.get("pdf_path", "")
    if not pdf_path:
        return {"evidences": evidences}

    chunks = ingest_pdf(pdf_path)
    # Focus on core conceptual keywords from the rubric.
    key_terms_question = "Dialectical Synthesis Fan-In Fan-Out Metacognition State Synchronization"
    top_chunks = query_pdf(chunks, key_terms_question, top_k=5)

    content = "\n\n---\n\n".join(chunk.text for chunk in top_chunks)
    evid_doc = Evidence(
        goal="pdf_concepts",
        found=len(top_chunks) > 0,
        content=content,
        location=pdf_path,
        rationale=(
            "Scanned PDF for deep explanations of Dialectical Synthesis, Fan-In/Fan-Out, "
            "Metacognition, and related orchestration concepts."
        ),
        confidence=0.7,
    )

    evidences.setdefault("doc", []).append(evid_doc)
    # Return only the keys we're modifying (LangGraph will merge via reducer)
    return {"evidences": evidences}


def run_vision_inspector(state: AgentState) -> Dict[str, Any]:
    """Stub node: will later analyze diagrams from the PDF."""
    return {}

