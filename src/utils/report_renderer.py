from __future__ import annotations

from pathlib import Path

from ..state import AuditReport, CriterionResult


# Human-readable labels for named resolution rules
RESOLUTION_RULE_LABELS = {
    "security_override": "Security override (score capped at 3 when Prosecutor identifies vulnerability)",
    "fact_over_claims": "Fact-over-claims (Defense overruled when cited evidence not in collected evidence)",
    "tech_lead_weighting": "Tech Lead weighting (technical dimensions use Tech Lead score)",
    "majority": "Majority (most common judge score)",
    "average": "Average (mean of judge scores)",
}


def _criterion_section(criterion: CriterionResult) -> str:
    """Render one criterion with score variance, resolution rule, and dissent."""
    block = f"""### {criterion.dimension_name} (Score: {criterion.final_score}/5)

**Dimension ID:** `{criterion.dimension_id}`
"""
    if criterion.score_variance is not None:
        block += f"""
**Score variance:** {criterion.score_variance} (max − min of judge scores)
"""
        if criterion.score_variance >= 2:
            block += "\n> **Re-evaluation:** Strong disagreement detected; dissent summary and resolution rule applied.\n"
    if criterion.resolution_rule:
        label = RESOLUTION_RULE_LABELS.get(
            criterion.resolution_rule,
            criterion.resolution_rule,
        )
        block += f"""
**Resolution rule:** {label}
"""

    block += """
**Judge opinions:**
"""
    for opinion in criterion.judge_opinions:
        cited = ", ".join(opinion.cited_evidence) if opinion.cited_evidence else "None"
        block += f"""
- **{opinion.judge}** (Score: {opinion.score}/5)
  - Argument: {opinion.argument}
  - Cited evidence: {cited}
"""

    if criterion.dissent_summary:
        block += f"""
**Dissent summary:** {criterion.dissent_summary}
"""

    block += f"""
**Remediation:** {criterion.remediation}

---

"""
    return block


def render_audit_report_to_markdown(report: AuditReport, output_path: Path) -> None:
    """
    Serialize AuditReport to Markdown with explicit sections for
    conflict-resolution rules, score variance, and dissent.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    markdown = f"""# Audit Report: {report.repo_url}

## Executive Summary

{report.executive_summary}

## Overall Score: {report.overall_score:.2f}/5.0

## Conflict Resolution Rules

The Chief Justice applies the following named rules in order when synthesizing judge opinions:

1. **Security override:** If the Prosecutor identifies a confirmed security vulnerability, the score is capped at 3 (overrides Defense "effort" points).
2. **Fact-over-claims:** If the Defense cites evidence that is not present in the collected evidence, the Defense is overruled; the Prosecutor or Tech Lead score is used instead.
3. **Tech Lead weighting:** For technical/architecture dimensions (`langgraph_architecture`, `state_management`, `safe_tooling`, `forensic_accuracy`), the Tech Lead score carries highest weight.
4. **Majority / average:** Otherwise, the majority score is used if clear; else the average of judge scores.

When **score variance** (max judge score − min) is **≥ 2**, a re-evaluation is triggered and a **dissent summary** is required, documenting the disagreement and which rule resolved it.

## Criterion Breakdown

"""

    for criterion in report.criteria:
        markdown += _criterion_section(criterion)

    markdown += f"""## Remediation Plan

{report.remediation_plan}
"""

    output_path.write_text(markdown, encoding="utf-8")
