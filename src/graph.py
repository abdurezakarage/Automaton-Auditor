"""
LangGraph StateGraph wiring stub.

For now this just documents intended topology; nodes are not yet wired.
"""

from __future__ import annotations

from typing import Any

from langgraph.graph import END, START, StateGraph  # type: ignore[import]

from .state import AgentState
from .nodes.detectives import run_repo_investigator, run_doc_analyst


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
    Placeholder factory for the main StateGraph.

    Target interim topology:
    - Detectives (RepoInvestigator, DocAnalyst) fan-out in parallel.
    - EvidenceAggregator fan-in node synchronizes before any judges exist.
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


