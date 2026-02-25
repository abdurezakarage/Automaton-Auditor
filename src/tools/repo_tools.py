"""
RepoInvestigator tooling stubs.

TODO:
- clone_repo_to_temp(repo_url) -> local_path
- extract_git_history(local_path)
- analyze_graph_structure(local_path)
"""

from __future__ import annotations

import ast
import tempfile
from pathlib import Path
from typing import Dict, List, Tuple

from git import Repo  # type: ignore[import]


def clone_repo_to_temp(repo_url: str) -> Path:
    """
    Clone the target repo into a sandboxed temporary directory.

    The caller is responsible for cleaning up the directory when finished.
    """
    tmp_dir = Path(tempfile.mkdtemp(prefix="automaton-auditor-"))
    Repo.clone_from(repo_url, tmp_dir)
    return tmp_dir


def extract_git_history(repo_path: Path) -> List[str]:
    """Return a simple git history summary (sorted from oldest to newest)."""
    repo = Repo(str(repo_path))
    commits = list(repo.iter_commits())
    commits.reverse()
    return [f"{c.committed_datetime.isoformat()} - {c.summary}" for c in commits]


def _collect_stategraph_edges(repo_path: Path) -> List[Tuple[str, str]]:
    """
    Walk Python files in src/ and extract (from_node, to_node) pairs from
    calls to *.add_edge(...).
    """
    edges: List[Tuple[str, str]] = []

    src_root = repo_path / "src"
    if not src_root.exists():
        return edges

    for py_file in src_root.rglob("*.py"):
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"))
        except Exception:
            continue

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if not isinstance(func, ast.Attribute):
                continue
            if func.attr != "add_edge":
                continue
            args = node.args
            if len(args) < 2:
                continue
            from_node = getattr(args[0], "s", None) or getattr(args[0], "value", None)
            to_node = getattr(args[1], "s", None) or getattr(args[1], "value", None)
            if isinstance(from_node, ast.Constant) and isinstance(from_node.value, str):
                src_name = from_node.value
            else:
                continue
            if isinstance(to_node, ast.Constant) and isinstance(to_node.value, str):
                dst_name = to_node.value
            else:
                continue
            edges.append((src_name, dst_name))
    return edges


def analyze_graph_structure(repo_path: Path) -> Dict[str, object]:
    """
    AST-based LangGraph wiring analysis.

    Inspects calls to add_edge to detect basic fan-out / fan-in structure.
    """
    edges = _collect_stategraph_edges(repo_path)
    adjacency: Dict[str, List[str]] = {}
    for src, dst in edges:
        adjacency.setdefault(src, []).append(dst)

    parallel_fan_out = {src: dsts for src, dsts in adjacency.items() if len(dsts) > 1}

    return {
        "edges": edges,
        "adjacency": adjacency,
        "parallelism_detected": bool(parallel_fan_out),
        "parallel_fan_out": parallel_fan_out,
    }


