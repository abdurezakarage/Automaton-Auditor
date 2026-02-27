from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv  # type: ignore[import]

from src.graph import build_complete_graph
from src.state import AgentState, AuditReport, CriterionResult, JudicialOpinion
from src.utils.report_renderer import render_audit_report_to_markdown


def load_rubric(path: Path) -> List[Dict[str, Any]]:
    """Load rubric.json and return the list of dimensions."""
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("dimensions", [])


def build_fallback_report(state: AgentState) -> AuditReport:
    """Build a simple fallback AuditReport when ChiefJustice did not produce one."""
    repo_url = state.get("repo_url", "")
    opinions: List[JudicialOpinion] = state.get("opinions", [])  # type: ignore[assignment]

    # If there are opinions, average their scores; otherwise default to neutral.
    if opinions:
        avg_score = sum(op.score for op in opinions) / len(opinions)
    else:
        avg_score = 3.0

    criterion = CriterionResult(
        dimension_id="overall",
        dimension_name="Overall Quality",
        final_score=int(round(avg_score)),
        judge_opinions=opinions,
        dissent_summary=None,
        remediation="Review judge arguments and address highlighted issues.",
    )

    report = AuditReport(
        repo_url=repo_url,
        executive_summary="Fallback audit report generated without ChiefJustice aggregation.",
        overall_score=avg_score,
        criteria=[criterion],
        remediation_plan="Prioritize fixing issues mentioned by judges, then rerun the auditor.",
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run full Automaton Auditor (detectives + judges + chief justice)."
    )
    parser.add_argument("--repo-url", required=True, help="Target GitHub repository URL")
    parser.add_argument("--pdf-path", required=True, help="Path to the architecture PDF")
    parser.add_argument(
        "--mode",
        choices=["self", "peer"],
        default="self",
        help="Report mode: 'self' (audit own repo) or 'peer' (audit peer repo)",
    )
    parser.add_argument(
        "--output-name",
        default="audit_report.md",
        help="Filename for the generated Markdown report",
    )
    args = parser.parse_args()

    load_dotenv()

    rubric_path = Path("rubric.json")
    rubric_dimensions = load_rubric(rubric_path)

    graph = build_complete_graph()

    initial_state: Dict[str, Any] = {
        "repo_url": args.repo_url,
        "pdf_path": args.pdf_path,
        "rubric_dimensions": rubric_dimensions,
        "evidences": {},
        "opinions": [],
    }

    final_state: AgentState = graph.invoke(initial_state)  # type: ignore[assignment]

    report = final_state.get("final_report")  # type: ignore[assignment]
    if report is None:
        # Build a simple fallback report so the pipeline still produces output.
        report = build_fallback_report(final_state)

    if args.mode == "self":
        out_dir = Path("audit") / "report_onself_generated"
    else:
        out_dir = Path("audit") / "report_onpeer_generated"

    out_path = out_dir / args.output_name
    render_audit_report_to_markdown(report, out_path)  # type: ignore[arg-type]

    print("Full audit run completed.")
    print(f"- Markdown report written to: {out_path.resolve()}")


if __name__ == "__main__":
    main()

