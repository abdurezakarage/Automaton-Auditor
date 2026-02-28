
from __future__ import annotations

from typing import Any

from langgraph.graph import END, START, StateGraph  # type: ignore[import]

from .state import AgentState
from .nodes.detectives import run_repo_investigator, run_doc_analyst
from .nodes.judges import run_prosecutor, run_defense, run_tech_lead
from .nodes.justice import run_chief_justice


def _evidence_aggregator(state: AgentState) -> dict[str, Any]:
    """
    Fan-in node for detective outputs.

    Because evidences uses a reducer (operator.ior), the evidences from both
    detective branches have already been merged. This node just synchronizes
    the parallel branches before proceeding.
    """
    # No state modifications needed - just a synchronization point
    return {}


def build_graph() -> StateGraph:
    """
    Interim graph: Detectives only (for interim submission).

    Topology:
    - Detectives (RepoInvestigator, DocAnalyst) fan-out in parallel.
    - EvidenceAggregator fan-in node synchronizes.
    """
    builder = StateGraph(AgentState)

    # Detective nodes
    builder.add_node("repo_investigator", run_repo_investigator)
    builder.add_node("doc_analyst", run_doc_analyst)

    # Fan-in node
    builder.add_node("evidence_aggregator", _evidence_aggregator)

    # Parallel fan-out from START to both detectives
    builder.add_edge(START, "repo_investigator")
    builder.add_edge(START, "doc_analyst")

    # Fan-in to aggregator
    builder.add_edge("repo_investigator", "evidence_aggregator")
    builder.add_edge("doc_analyst", "evidence_aggregator")

    # End of interim graph
    builder.add_edge("evidence_aggregator", END)

    return builder.compile()


def build_complete_graph() -> StateGraph:
    """
    Complete graph: Detectives → Judges → Chief Justice (for final submission).

    Topology:
    - Detectives fan-out in parallel → EvidenceAggregator (fan-in)
    - Judges fan-out in parallel → ChiefJustice (fan-in) → END
    """
    builder = StateGraph(AgentState)

    # Detective layer
    builder.add_node("repo_investigator", run_repo_investigator)
    builder.add_node("doc_analyst", run_doc_analyst)
    builder.add_node("evidence_aggregator", _evidence_aggregator)

    # Judicial layer
    builder.add_node("prosecutor", run_prosecutor)
    builder.add_node("defense", run_defense)
    builder.add_node("tech_lead", run_tech_lead)

    # Supreme Court
    builder.add_node("chief_justice", run_chief_justice)

    # Detective fan-out
    builder.add_edge(START, "repo_investigator")
    builder.add_edge(START, "doc_analyst")

    # Detective fan-in
    builder.add_edge("repo_investigator", "evidence_aggregator")
    builder.add_edge("doc_analyst", "evidence_aggregator")

    # Judge fan-out (from evidence aggregator)
    builder.add_edge("evidence_aggregator", "prosecutor")
    builder.add_edge("evidence_aggregator", "defense")
    builder.add_edge("evidence_aggregator", "tech_lead")

    # Judge fan-in (to chief justice)
    builder.add_edge("prosecutor", "chief_justice")
    builder.add_edge("defense", "chief_justice")
    builder.add_edge("tech_lead", "chief_justice")

    # Final output
    builder.add_edge("chief_justice", END)

    return builder.compile()

