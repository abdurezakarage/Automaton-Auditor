from __future__ import annotations

from pathlib import Path

from ..state import AuditReport


def render_audit_report_to_markdown(report: AuditReport, output_path: Path) -> None:
    """Serialize AuditReport to Markdown format."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    markdown = f"""# Audit Report: {report.repo_url}

## Executive Summary

{report.executive_summary}

## Overall Score: {report.overall_score:.2f}/5.0

## Criterion Breakdown

"""

    for criterion in report.criteria:
        markdown += f"""### {criterion.dimension_name} (Score: {criterion.final_score}/5)

**Dimension ID:** `{criterion.dimension_id}`

**Judge Opinions:**
"""
        for opinion in criterion.judge_opinions:
            cited = ", ".join(opinion.cited_evidence) if opinion.cited_evidence else "None"
            markdown += f"""
- **{opinion.judge}** (Score: {opinion.score}/5)
  - Argument: {opinion.argument}
  - Cited Evidence: {cited}
"""

        if criterion.dissent_summary:
            markdown += f"""
**Dissent Summary:** {criterion.dissent_summary}
"""

        markdown += f"""
**Remediation:** {criterion.remediation}

---

"""

    markdown += f"""## Remediation Plan

{report.remediation_plan}
"""

    output_path.write_text(markdown, encoding="utf-8")

