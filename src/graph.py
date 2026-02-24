"""
LangGraph StateGraph wiring stub.

For now this just documents intended topology; nodes are not yet wired.
"""

from __future__ import annotations

# from langgraph.graph import StateGraph  # to be enabled when wiring the graph

# from .state import AgentState
# from .nodes.detectives import run_repo_investigator, run_doc_analyst, run_vision_inspector
# from .nodes.judges import run_prosecutor, run_defense, run_tech_lead
# from .nodes.justice import run_chief_justice


def build_graph():
    """
    Placeholder factory for the main StateGraph.

    Target topology:
    - Detectives fan-out in parallel, then fan-in (EvidenceAggregator).
    - Judges fan-out in parallel, then fan-in into ChiefJustice.
    """

    # builder = StateGraph(AgentState)
    # TODO: add nodes + edges as per architecture document.
    # return builder.compile()
    raise NotImplementedError("Graph wiring not implemented yet.")

