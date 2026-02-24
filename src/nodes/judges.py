"""
Judicial layer node stubs: Prosecutor, Defense, Tech Lead.

These will later call LLMs with structured output bound to JudicialOpinion.
"""

from __future__ import annotations

from typing import List

from ..state import AgentState, JudicialOpinion


def run_prosecutor(state: AgentState) -> AgentState:
    """Stub Prosecutor node."""
    state["opinions"] = state.get("opinions", [])  # type: ignore[assignment]
    return state


def run_defense(state: AgentState) -> AgentState:
    """Stub Defense node."""
    state["opinions"] = state.get("opinions", [])  # type: ignore[assignment]
    return state


def run_tech_lead(state: AgentState) -> AgentState:
    """Stub Tech Lead node."""
    state["opinions"] = state.get("opinions", [])  # type: ignore[assignment]
    return state

