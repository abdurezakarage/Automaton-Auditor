"""Quick test script for the detective graph with default test inputs."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv  # type: ignore[import]

from src.graph import build_graph
from src.state import AgentState

# Default test inputs (you can modify these)
DEFAULT_REPO_URL = "https://github.com/langchain-ai/langgraph.git"
DEFAULT_PDF_PATH = Path(__file__).parent.parent / "TRP1 Challenge Week 2_ The Automaton Auditor.pdf"


def main() -> None:
    """Run the detective graph with default test inputs."""
    load_dotenv()

    repo_url = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_REPO_URL
    pdf_path = sys.argv[2] if len(sys.argv) > 2 else str(DEFAULT_PDF_PATH)

    if not Path(pdf_path).exists():
        print(f"ERROR: PDF not found at: {pdf_path}")
        print(f"Please provide a valid PDF path as the second argument.")
        sys.exit(1)

    print(f"Testing detective graph...")
    print(f"  Repo URL: {repo_url}")
    print(f"  PDF Path: {pdf_path}")
    print()

    graph = build_graph()

    initial_state: dict[str, Any] = {
        "repo_url": repo_url,
        "pdf_path": pdf_path,
        "rubric_dimensions": [],
        "evidences": {},
        "opinions": [],
    }

    try:
        final_state: AgentState = graph.invoke(initial_state)  # type: ignore[assignment]

        evidences = final_state.get("evidences", {})  # type: ignore[assignment]
        print("✅ Detective run completed!")
        print(f"  - Repo evidences: {len(evidences.get('repo', []))}")
        print(f"  - Doc evidences: {len(evidences.get('doc', []))}")
        
        # Show a sample of evidences
        if evidences.get("repo"):
            print("\n  Sample repo evidence:")
            for ev in list(evidences["repo"])[:2]:  # type: ignore[index]
                print(f"    - {ev.goal}: found={ev.found}")
        
        if evidences.get("doc"):
            print("\n  Sample doc evidence:")
            for ev in list(evidences["doc"])[:2]:  # type: ignore[index]
                print(f"    - {ev.goal}: found={ev.found}")
                
    except Exception as e:
        print(f"❌ Error running detective graph: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
