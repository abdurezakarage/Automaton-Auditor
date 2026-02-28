"""
Detective layer nodes: RepoInvestigator, DocAnalyst, VisionInspector.

Wired into the LangGraph StateGraph with parallel fan-out and evidence correlation.
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
from ..tools.vision_tools import extract_images_from_pdf, analyze_images_with_vision


def run_repo_investigator(state: AgentState) -> Dict[str, Any]:
    """Analyze the target repo and populate Evidence objects. Sets errors on clone/failure."""
    evidences: Dict[str, List[Evidence]] = dict(state.get("evidences", {}))  # type: ignore[assignment]
    errors: Dict[str, str] = dict(state.get("errors", {}))  # type: ignore[assignment]

    repo_url = state.get("repo_url", "")
    if not repo_url:
        return {"evidences": evidences, "errors": {"repo_investigator": "missing repo_url"}}

    try:
        local_path = clone_repo_to_temp(repo_url)
    except Exception as e:
        return {
            "evidences": evidences,
            "errors": {"repo_investigator": f"clone failed: {e!s}"},
        }

    try:
        # Git history evidence (correlates with doc/vision for full forensic picture)
        history = extract_git_history(local_path)
        evid_git = Evidence(
            goal="git_history",
            found=len(history) > 0,
            content="\n".join(history[:20]),
            location=str(local_path),
            rationale="Collected git log to assess commit granularity and progression.",
            confidence=0.8,
            correlates_with=["doc", "vision"],
        )

        # Graph wiring evidence (correlates with doc concepts and vision diagrams)
        graph_info = analyze_graph_structure(local_path)
        evid_graph = Evidence(
            goal="graph_orchestration",
            found=bool(graph_info.get("edges")),
            content=str(graph_info),
            location=str(local_path / "src"),
            rationale="Analyzed AST for StateGraph.add_edge fan-out/fan-in patterns.",
            confidence=0.7,
            correlates_with=["doc", "vision"],
        )

        evidences.setdefault("repo", []).extend([evid_git, evid_graph])
        return {"evidences": evidences}
    except Exception as e:
        return {
            "evidences": evidences,
            "errors": {"repo_investigator": f"repo analysis failed: {e!s}"},
        }


def run_doc_analyst(state: AgentState) -> Dict[str, Any]:
    """Analyze the PDF report and populate Evidence objects. Sets errors on missing path/failure."""
    evidences: Dict[str, List[Evidence]] = dict(state.get("evidences", {}))  # type: ignore[assignment]
    errors: Dict[str, str] = dict(state.get("errors", {}))  # type: ignore[assignment]

    pdf_path = state.get("pdf_path", "")
    if not pdf_path:
        return {"evidences": evidences, "errors": {"doc_analyst": "missing pdf_path"}}

    try:
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
                "Metacognition, and related orchestration concepts. To be correlated with repo "
                "graph_orchestration and vision diagram analysis."
            ),
            confidence=0.7,
            correlates_with=["repo", "vision"],
        )

        evidences.setdefault("doc", []).append(evid_doc)
        return {"evidences": evidences}
    except Exception as e:
        return {
            "evidences": evidences,
            "errors": {"doc_analyst": f"PDF ingest/query failed: {e!s}"},
        }


def run_vision_inspector(state: AgentState) -> Dict[str, Any]:
    """
    Extract images from the report PDF and run multimodal (vision) analysis.
    Sets errors on missing path or vision failure.
    """
    evidences: Dict[str, List[Evidence]] = dict(state.get("evidences", {}))  # type: ignore[assignment]

    pdf_path = state.get("pdf_path", "")
    if not pdf_path:
        return {"evidences": evidences, "errors": {"vision_inspector": "missing pdf_path"}}

    try:
        images = extract_images_from_pdf(pdf_path)
        if not images:
            evid_vision = Evidence(
                goal="pdf_diagrams",
                found=False,
                content="No embedded images found in PDF.",
                location=pdf_path,
                rationale="No images to analyze; report may be text-only.",
                confidence=0.5,
                correlates_with=["repo", "doc"],
            )
            evidences.setdefault("vision", []).append(evid_vision)
            return {"evidences": evidences}

        prompt = (
            "For each image, briefly describe what it shows. Focus on: "
            "architecture diagrams, flowcharts, fan-out/fan-in or parallel execution diagrams, "
            "state graphs, or any visual that relates to software orchestration, LangGraph, or "
            "dialectical synthesis. Note page numbers if visible. One short paragraph per image is enough."
        )
        analysis = analyze_images_with_vision(images, prompt, max_images=8)

        evid_vision = Evidence(
            goal="pdf_diagrams",
            found=True,
            content=analysis,
            location=pdf_path,
            rationale=(
                "Extracted images from PDF and ran vision model to describe diagrams. "
                "Correlate with repo graph_orchestration and doc pdf_concepts for alignment."
            ),
            confidence=0.75,
            correlates_with=["repo", "doc"],
        )
        evidences.setdefault("vision", []).append(evid_vision)
        return {"evidences": evidences}
    except Exception as e:
        return {
            "evidences": evidences,
            "errors": {"vision_inspector": f"vision analysis failed: {e!s}"},
        }

