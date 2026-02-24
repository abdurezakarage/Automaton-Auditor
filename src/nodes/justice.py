"""
Supreme Court / ChiefJustice node stub.

Will later:
- Aggregate JudicialOpinion objects
- Apply deterministic conflict resolution rules
- Produce final AuditReport + render Markdown.
"""

from __future__ import annotations

from ..state import AgentState, AuditReport


def run_chief_justice(state: AgentState) -> AgentState:
    """Stub ChiefJustice node that currently just passes state through."""
    # TODO: implement conflict resolution + AuditReport construction.
    return state

