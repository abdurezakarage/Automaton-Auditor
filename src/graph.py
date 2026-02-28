
from __future__ import annotations

from typing import Any

from langgraph.graph import END, START, StateGraph  # type: ignore[import]

from .state import AgentState, Evidence
from .state import JudicialOpinion
from .nodes.detectives import run_repo_investigator, run_doc_analyst, run_vision_inspector
from .nodes.judges import run_prosecutor, run_defense, run_tech_lead
from .nodes.justice import run_chief_justice


def _evidence_aggregator(state: AgentState) -> dict[str, Any]:
    """
    Fan-in node for detective outputs.

    Merges evidences from repo, doc, and vision (already merged via reducer).
    Produces correlation evidence that cross-references RepoInvestigator, DocAnalyst,
    and VisionInspector so evidences are correlated rather than isolated per node.
    """
    evidences: dict[str, list[Evidence]] = dict(state.get("evidences", {}))  # type: ignore[assignment]

    repo_evs = evidences.get("repo", [])
    doc_evs = evidences.get("doc", [])
    vision_evs = evidences.get("vision", [])

    # Build cross-reference summary tying repo + doc + vision together
    parts: list[str] = []
    if repo_evs:
        goals = [e.goal for e in repo_evs]
        parts.append(f"Repo: {', '.join(goals)}")
    if doc_evs:
        goals = [e.goal for e in doc_evs]
        parts.append(f"Doc: {', '.join(goals)}")
    if vision_evs:
        goals = [e.goal for e in vision_evs]
        parts.append(f"Vision: {', '.join(goals)}")

    if parts:
        alignment = (
            "Repo graph_orchestration (AST edges) can be cross-checked with Doc pdf_concepts "
            "(Fan-In/Fan-Out, Metacognition) and Vision pdf_diagrams (flow/architecture). "
            "Correlated evidence supports forensic accuracy."
        )
        correlation_content = " | ".join(parts) + "\n\n" + alignment
        correlation_evidence = Evidence(
            goal="cross_reference",
            found=True,
            content=correlation_content,
            location="evidence_aggregator",
            rationale=(
                "Synthesized repo, doc, and vision evidences so judges can evaluate "
                "consistency across code structure, report text, and diagram content."
            ),
            confidence=0.8,
            correlates_with=["repo", "doc", "vision"],
        )
        evidences.setdefault("correlation", []).append(correlation_evidence)

    # When any detective failed, add failure-summary evidence so judges see degraded mode
    errs = state.get("errors") or {}
    if errs:
        failure_content = "\n".join(f"{k}: {v}" for k, v in sorted(errs.items()))
        failure_evidence = Evidence(
            goal="degraded_evidence",
            found=True,
            content=failure_content,
            location="evidence_aggregator",
            rationale=(
                "One or more detective branches failed (clone, PDF, or vision). "
                "Judges should treat evidence as partial and may cap confidence."
            ),
            confidence=0.4,
            correlates_with=["repo", "doc", "vision"],
        )
        evidences.setdefault("correlation", []).append(failure_evidence)

    return {"evidences": evidences}


def _judge_aggregator(state: AgentState) -> dict[str, Any]:
    """Sync point after all three judges; no state change (conditional edge routes next)."""
    return {}


def _route_after_judges(state: AgentState) -> str:
    """Conditional: if any judge failed or produced no opinions, take error path to judge_fallback."""
    errs = state.get("errors") or {}
    judge_nodes = ("prosecutor", "defense", "tech_lead")
    if any(errs.get(n) for n in judge_nodes):
        return "judge_fallback"
    return "chief_justice"


def _judge_fallback(state: AgentState) -> dict[str, Any]:
    """Error path: add placeholder JudicialOpinions for failed judges so ChiefJustice can still run."""
    opinions: list = list(state.get("opinions", []))  # type: ignore[assignment]
    errs = state.get("errors") or {}
    rubric_dimensions = state.get("rubric_dimensions", []) or [{"dimension_id": "overall", "dimension_name": "Overall"}]
    criterion_ids = [d.get("dimension_id", "overall") for d in rubric_dimensions] or ["overall"]

    for judge_name, err_msg in errs.items():
        if judge_name not in ("prosecutor", "defense", "tech_lead"):
            continue
        judge_label = "Prosecutor" if judge_name == "prosecutor" else "Defense" if judge_name == "defense" else "TechLead"
        for cid in criterion_ids:
            opinions.append(
                JudicialOpinion(
                    judge=judge_label,  # type: ignore[arg-type]
                    criterion_id=cid,
                    score=3,
                    argument=f"[Fallback] {judge_name} failed: {err_msg}. Neutral score applied.",
                    cited_evidence=["degraded_evidence", "error_path"],
                )
            )
    return {"opinions": opinions}


def _route_after_repo(state: AgentState) -> str:
    """Conditional: on repo_investigator failure take error path, else go to aggregator."""
    if (state.get("errors") or {}).get("repo_investigator"):
        return "repo_failure_handler"
    return "evidence_aggregator"


def _route_after_doc(state: AgentState) -> str:
    """Conditional: on doc_analyst failure take error path, else go to aggregator."""
    if (state.get("errors") or {}).get("doc_analyst"):
        return "doc_failure_handler"
    return "evidence_aggregator"


def _route_after_vision(state: AgentState) -> str:
    """Conditional: on vision_inspector failure take error path, else go to aggregator."""
    if (state.get("errors") or {}).get("vision_inspector"):
        return "vision_failure_handler"
    return "evidence_aggregator"


def _repo_failure_handler(state: AgentState) -> dict[str, Any]:
    """Error path: record repo_investigator failure as evidence and continue to aggregator."""
    evidences: dict[str, list[Evidence]] = dict(state.get("evidences", {}))  # type: ignore[assignment]
    err = (state.get("errors") or {}).get("repo_investigator", "unknown error")
    evidences.setdefault("repo", []).append(
        Evidence(
            goal="repo_error",
            found=False,
            content=err,
            location="repo_investigator",
            rationale="Clone or repo analysis failed; evidence is missing for this branch.",
            confidence=0.0,
            correlates_with=["doc", "vision"],
        )
    )
    return {"evidences": evidences}


def _doc_failure_handler(state: AgentState) -> dict[str, Any]:
    """Error path: record doc_analyst failure as evidence and continue to aggregator."""
    evidences: dict[str, list[Evidence]] = dict(state.get("evidences", {}))  # type: ignore[assignment]
    err = (state.get("errors") or {}).get("doc_analyst", "unknown error")
    evidences.setdefault("doc", []).append(
        Evidence(
            goal="doc_error",
            found=False,
            content=err,
            location="doc_analyst",
            rationale="PDF ingest or query failed; evidence is missing for this branch.",
            confidence=0.0,
            correlates_with=["repo", "vision"],
        )
    )
    return {"evidences": evidences}


def _vision_failure_handler(state: AgentState) -> dict[str, Any]:
    """Error path: record vision_inspector failure as evidence and continue to aggregator."""
    evidences: dict[str, list[Evidence]] = dict(state.get("evidences", {}))  # type: ignore[assignment]
    err = (state.get("errors") or {}).get("vision_inspector", "unknown error")
    evidences.setdefault("vision", []).append(
        Evidence(
            goal="vision_error",
            found=False,
            content=err,
            location="vision_inspector",
            rationale="Vision extraction or analysis failed; evidence is missing for this branch.",
            confidence=0.0,
            correlates_with=["repo", "doc"],
        )
    )
    return {"evidences": evidences}


def build_graph() -> StateGraph:
   
    builder = StateGraph(AgentState)

    # Detective nodes
    builder.add_node("repo_investigator", run_repo_investigator)
    builder.add_node("doc_analyst", run_doc_analyst)
    builder.add_node("vision_inspector", run_vision_inspector)

    # Fan-in node
    builder.add_node("evidence_aggregator", _evidence_aggregator)

    # Detective failure handlers (error paths)
    builder.add_node("repo_failure_handler", _repo_failure_handler)
    builder.add_node("doc_failure_handler", _doc_failure_handler)
    builder.add_node("vision_failure_handler", _vision_failure_handler)

    # Parallel fan-out from START to all three detectives
    builder.add_edge(START, "repo_investigator")
    builder.add_edge(START, "doc_analyst")
    builder.add_edge(START, "vision_inspector")

    # Conditional edges: success -> evidence_aggregator, failure -> failure_handler -> evidence_aggregator
    builder.add_conditional_edges(
        "repo_investigator",
        _route_after_repo,
        {"evidence_aggregator": "evidence_aggregator", "repo_failure_handler": "repo_failure_handler"},
    )
    builder.add_conditional_edges(
        "doc_analyst",
        _route_after_doc,
        {"evidence_aggregator": "evidence_aggregator", "doc_failure_handler": "doc_failure_handler"},
    )
    builder.add_conditional_edges(
        "vision_inspector",
        _route_after_vision,
        {"evidence_aggregator": "evidence_aggregator", "vision_failure_handler": "vision_failure_handler"},
    )
    builder.add_edge("repo_failure_handler", "evidence_aggregator")
    builder.add_edge("doc_failure_handler", "evidence_aggregator")
    builder.add_edge("vision_failure_handler", "evidence_aggregator")

    # End of interim graph
    builder.add_edge("evidence_aggregator", END)

    return builder.compile()


def build_complete_graph() -> StateGraph:
    """
    Complete graph: Detectives → Judges → Chief Justice (for final submission).

    Topology:
    - Detectives (Repo, Doc, Vision) fan-out in parallel; conditional edges route
      success -> evidence_aggregator, failure -> *_failure_handler -> evidence_aggregator.
    - Judges fan-out in parallel -> judge_aggregator; conditional routes
      success -> chief_justice, failure -> judge_fallback -> chief_justice.
    """
    builder = StateGraph(AgentState)

    # Detective layer
    builder.add_node("repo_investigator", run_repo_investigator)
    builder.add_node("doc_analyst", run_doc_analyst)
    builder.add_node("vision_inspector", run_vision_inspector)
    builder.add_node("evidence_aggregator", _evidence_aggregator)

    # Detective failure handlers (error paths)
    builder.add_node("repo_failure_handler", _repo_failure_handler)
    builder.add_node("doc_failure_handler", _doc_failure_handler)
    builder.add_node("vision_failure_handler", _vision_failure_handler)

    # Judicial layer
    builder.add_node("prosecutor", run_prosecutor)
    builder.add_node("defense", run_defense)
    builder.add_node("tech_lead", run_tech_lead)

    # Supreme Court
    builder.add_node("chief_justice", run_chief_justice)

    # Judge sync and error-path nodes
    builder.add_node("judge_aggregator", _judge_aggregator)
    builder.add_node("judge_fallback", _judge_fallback)

    # Detective fan-out
    builder.add_edge(START, "repo_investigator")
    builder.add_edge(START, "doc_analyst")
    builder.add_edge(START, "vision_inspector")

    # Conditional edges: success -> evidence_aggregator, failure -> failure_handler -> evidence_aggregator
    builder.add_conditional_edges(
        "repo_investigator",
        _route_after_repo,
        {"evidence_aggregator": "evidence_aggregator", "repo_failure_handler": "repo_failure_handler"},
    )
    builder.add_conditional_edges(
        "doc_analyst",
        _route_after_doc,
        {"evidence_aggregator": "evidence_aggregator", "doc_failure_handler": "doc_failure_handler"},
    )
    builder.add_conditional_edges(
        "vision_inspector",
        _route_after_vision,
        {"evidence_aggregator": "evidence_aggregator", "vision_failure_handler": "vision_failure_handler"},
    )
    builder.add_edge("repo_failure_handler", "evidence_aggregator")
    builder.add_edge("doc_failure_handler", "evidence_aggregator")
    builder.add_edge("vision_failure_handler", "evidence_aggregator")

    # Judge fan-out (from evidence aggregator)
    builder.add_edge("evidence_aggregator", "prosecutor")
    builder.add_edge("evidence_aggregator", "defense")
    builder.add_edge("evidence_aggregator", "tech_lead")

    # Judge fan-in to sync node, then conditional: success -> chief_justice, failure -> judge_fallback -> chief_justice
    builder.add_edge("prosecutor", "judge_aggregator")
    builder.add_edge("defense", "judge_aggregator")
    builder.add_edge("tech_lead", "judge_aggregator")
    builder.add_conditional_edges(
        "judge_aggregator",
        _route_after_judges,
        {"chief_justice": "chief_justice", "judge_fallback": "judge_fallback"},
    )
    builder.add_edge("judge_fallback", "chief_justice")

    # Final output
    builder.add_edge("chief_justice", END)

    return builder.compile()

