from __future__ import annotations

import argparse
from typing import Any, Dict

from dotenv import load_dotenv  # type: ignore[import]

from src.graph import build_graph
from src.state import AgentState


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run interim detective layer (RepoInvestigator + DocAnalyst)."
    )
    parser.add_argument("--repo-url", required=True, help="Target GitHub repository URL")
    parser.add_argument("--pdf-path", required=True, help="Path to the architecture PDF")
    args = parser.parse_args()

    load_dotenv()

    graph = build_graph()

    initial_state: Dict[str, Any] = {
        "repo_url": args.repo_url,
        "pdf_path": args.pdf_path,
        "rubric_dimensions": [],
        "evidences": {},
        "opinions": [],
    }

    final_state: AgentState = graph.invoke(initial_state)  # type: ignore[assignment]

    evidences = final_state.get("evidences", {})  # type: ignore[assignment]
    print("Detective run completed.")
    print(f"- Repo evidences: {len(evidences.get('repo', []))}")
    print(f"- Doc evidences: {len(evidences.get('doc', []))}")


if __name__ == "__main__":
    main()

