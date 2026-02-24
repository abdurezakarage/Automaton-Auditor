"""
Detective layer node stubs (RepoInvestigator, DocAnalyst, VisionInspector).

These will later be wired into a LangGraph StateGraph.
"""

from __future__ import annotations

from typing import Dict, List

from ..state import AgentState, Evidence


def run_repo_investigator(state: AgentState) -> AgentState:
    """Stub node: populate evidences from repo analysis."""
    # TODO: call repo_tools.clone_repo_to_temp / extract_git_history / analyze_graph_structure
    state["evidences"] = state.get("evidences", {})  # type: ignore[assignment]
    return state


def run_doc_analyst(state: AgentState) -> AgentState:
    """Stub node: populate evidences from PDF report analysis."""
    state["evidences"] = state.get("evidences", {})  # type: ignore[assignment]
    return state


def run_vision_inspector(state: AgentState) -> AgentState:
    """Stub node: will later analyze diagrams from the PDF."""
    return state

