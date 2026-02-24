"""
RepoInvestigator tooling stubs.

TODO:
- clone_repo_to_temp(repo_url) -> local_path
- extract_git_history(local_path)
- analyze_graph_structure(local_path)
"""

from __future__ import annotations

from pathlib import Path
from typing import List

from git import Repo  # type: ignore[import]


def clone_repo_to_temp(repo_url: str) -> Path:
    """Clone the target repo into a temporary directory (to be implemented)."""
    # NOTE: Implement tempfile-based sandboxing here.
    raise NotImplementedError


def extract_git_history(repo_path: Path) -> List[str]:
    """Return a simple git history summary for now."""
    repo = Repo(str(repo_path))
    return [f"{c.committed_datetime.isoformat()} - {c.summary}" for c in repo.iter_commits()]


def analyze_graph_structure(repo_path: Path) -> dict:
    """
    Placeholder for AST-based LangGraph wiring analysis.

    Should inspect StateGraph construction and detect fan-out / fan-in.
    """
    # NOTE: Implement real AST parsing using `ast` or tree-sitter.
    return {"parallelism_detected": False, "details": "not implemented yet"}

