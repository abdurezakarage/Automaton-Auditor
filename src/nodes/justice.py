"""
Supreme Court / ChiefJustice node.

Synthesizes JudicialOpinion objects from all three judges, applies explicit
named conflict-resolution rules (security override, fact-over-claims, Tech Lead
weighting), and produces the final AuditReport. Score-variance detection
triggers dissent summaries and re-evaluation language when judges strongly disagree.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List, Optional, Tuple

from ..state import AgentState, AuditReport, CriterionResult, Evidence, JudicialOpinion


# Variance threshold: when max(score) - min(score) >= this, dissent summary is required
SCORE_VARIANCE_THRESHOLD = 2

# Dimension IDs where Tech Lead weighting applies (technical/architecture criteria)
TECH_LEAD_WEIGHTING_DIMENSIONS = frozenset({
    "langgraph_architecture",
    "state_management",
    "safe_tooling",
    "forensic_accuracy",
})

# Named rule identifiers for report sections
RULE_SECURITY_OVERRIDE = "security_override"
RULE_FACT_OVER_CLAIMS = "fact_over_claims"
RULE_TECH_LEAD_WEIGHTING = "tech_lead_weighting"
RULE_MAJORITY = "majority"
RULE_AVERAGE = "average"


def _get_judges(opinions: List[JudicialOpinion]) -> Tuple[Optional[JudicialOpinion], Optional[JudicialOpinion], Optional[JudicialOpinion]]:
    prosecutor = next((op for op in opinions if op.judge == "Prosecutor"), None)
    defense = next((op for op in opinions if op.judge == "Defense"), None)
    tech_lead = next((op for op in opinions if op.judge == "TechLead"), None)
    return prosecutor, defense, tech_lead


def _security_override(opinions: List[JudicialOpinion]) -> Optional[Tuple[int, str]]:
    """
    Named rule: If Prosecutor identifies a confirmed security vulnerability,
    cap score at 3 (overrides Defense 'effort' points).
    """
    prosecutor, _, _ = _get_judges(opinions)
    if not prosecutor:
        return None
    arg_lower = prosecutor.argument.lower()
    if "security" in arg_lower and "vulnerability" in arg_lower:
        capped = min(3, prosecutor.score)
        return (capped, "Security override: Prosecutor identified security vulnerability; score capped at 3.")
    return None


def _fact_over_claims(
    opinions: List[JudicialOpinion],
    evidences: Dict[str, List[Evidence]],
) -> Optional[Tuple[int, str]]:
    """
    Named rule: Fact-over-claims — if Defense cites evidence that is not present
    in collected evidences, overrule Defense (prioritize Prosecutor or Tech Lead).
    """
    prosecutor, defense, tech_lead = _get_judges(opinions)
    if not defense or not defense.cited_evidence:
        return None
    # Flatten evidence goals and bucket keys present in state
    evidence_goals = set(evidences.keys()) if evidences else set()
    for bucket in (evidences or {}).values():
        for e in bucket:
            if getattr(e, "goal", None):
                evidence_goals.add(e.goal)
    # Check if Defense cited something not in evidence
    cited = set(defense.cited_evidence)
    uncited = cited - evidence_goals
    if not uncited:
        return None
    # Overrule: use Prosecutor score if available, else Tech Lead, else 3
    if prosecutor is not None:
        score = prosecutor.score
        reason = "Fact-over-claims: Defense cited evidence not in collected evidence; Prosecutor score applied."
    elif tech_lead is not None:
        score = tech_lead.score
        reason = "Fact-over-claims: Defense cited evidence not in collected evidence; Tech Lead score applied."
    else:
        score = 3
        reason = "Fact-over-claims: Defense cited evidence not in collected evidence; neutral score applied."
    return (score, reason)


def _tech_lead_weighting(
    opinions: List[JudicialOpinion],
    dimension_id: str,
) -> Optional[Tuple[int, str]]:
    """
    Named rule: Tech Lead carries highest weight for technical/architecture
    criteria (langgraph_architecture, state_management, safe_tooling, forensic_accuracy).
    """
    if dimension_id not in TECH_LEAD_WEIGHTING_DIMENSIONS:
        return None
    _, _, tech_lead = _get_judges(opinions)
    if not tech_lead:
        return None
    return (
        tech_lead.score,
        f"Tech Lead weighting: technical dimension '{dimension_id}'; Tech Lead score ({tech_lead.score}) applied.",
    )


def _majority_or_average(opinions: List[JudicialOpinion]) -> Tuple[int, str, str]:
    """Fallback: majority score if clear, else average. Returns (score, dissent, rule_name)."""
    scores = [op.score for op in opinions]
    if not scores:
        return 3, "No opinions provided; neutral score applied.", RULE_AVERAGE
    counts = Counter(scores)
    most_common = counts.most_common(1)[0]
    if most_common[1] >= 2:
        score = most_common[0]
        return score, f"Majority score: {score} (votes: {dict(counts)}).", RULE_MAJORITY
    avg = round(sum(scores) / len(scores))
    avg = max(1, min(5, avg))
    return avg, f"Averaged scores: {scores} -> {avg}.", RULE_AVERAGE


def _resolve_conflict(
    opinions: List[JudicialOpinion],
    dimension_id: str,
    evidences: Dict[str, List[Evidence]],
) -> Tuple[int, Optional[str], str, int]:
    """
    Apply named rules in order; compute variance and dissent.
    Returns (final_score, dissent_summary, resolution_rule, score_variance).
    """
    if not opinions:
        return 3, "No judge opinions provided; defaulting to neutral score.", RULE_AVERAGE, 0

    scores = [op.score for op in opinions]
    variance = max(scores) - min(scores) if len(scores) > 1 else 0

    # Rule order: 1) Security override, 2) Fact-over-claims, 3) Tech Lead weighting, 4) Majority/Average
    result = _security_override(opinions)
    if result is not None:
        score, dissent = result
        rule = RULE_SECURITY_OVERRIDE
        dissent_final = _format_dissent(dissent, variance, rule, scores)
        return score, dissent_final, rule, variance

    result = _fact_over_claims(opinions, evidences or {})
    if result is not None:
        score, dissent = result
        rule = RULE_FACT_OVER_CLAIMS
        dissent_final = _format_dissent(dissent, variance, rule, scores)
        return score, dissent_final, rule, variance

    result = _tech_lead_weighting(opinions, dimension_id)
    if result is not None:
        score, dissent = result
        rule = RULE_TECH_LEAD_WEIGHTING
        dissent_final = _format_dissent(dissent, variance, rule, scores)
        return score, dissent_final, rule, variance

    score, dissent, rule = _majority_or_average(opinions)
    dissent_final = _format_dissent(dissent, variance, rule, scores)
    return score, dissent_final, rule, variance


def _format_dissent(
    base_dissent: str,
    variance: int,
    rule: str,
    scores: List[int],
) -> Optional[str]:
    """
    When variance >= SCORE_VARIANCE_THRESHOLD, require dissent summary and add
    re-evaluation language. Otherwise return dissent only if we have content.
    """
    if variance >= SCORE_VARIANCE_THRESHOLD:
        scores_str = ", ".join(str(s) for s in scores)
        re_eval = (
            f" Re-evaluation triggered due to strong disagreement (score variance={variance}, scores: [{scores_str}]). "
            f"Resolved via rule: {rule}."
        )
        return base_dissent + re_eval
    return base_dissent if base_dissent else None


def run_chief_justice(state: AgentState) -> Dict[str, Any]:
    """
    ChiefJustice node: Synthesizes all judge opinions into final AuditReport.

    For each rubric criterion:
    1. Collects all three judge opinions
    2. Applies explicit named rules (security override, fact-over-claims, Tech Lead weighting)
    3. Detects score variance; triggers dissent summary and re-evaluation language when >= 2
    4. Produces CriterionResult with resolution_rule and score_variance for report sections
    """
    opinions: List[JudicialOpinion] = state.get("opinions", [])  # type: ignore[assignment]
    repo_url = state.get("repo_url", "")
    rubric_dimensions = state.get("rubric_dimensions", [])  # type: ignore[assignment]
    evidences: Dict[str, List[Evidence]] = state.get("evidences", {})  # type: ignore[assignment]

    criteria: List[CriterionResult] = []

    if rubric_dimensions:
        for dim in rubric_dimensions:
            dimension_id = dim.get("dimension_id", "unknown")
            dimension_name = dim.get("dimension_name", dimension_id)
            crit_ops = [op for op in opinions if op.criterion_id == dimension_id]

            if crit_ops:
                final_score, dissent_summary, resolution_rule, score_variance = _resolve_conflict(
                    crit_ops, dimension_id, evidences
                )
                remediation = (
                    f"Review implementation for dimension '{dimension_name}' "
                    f"and address issues highlighted by judge arguments."
                )
                criteria.append(
                    CriterionResult(
                        dimension_id=dimension_id,
                        dimension_name=dimension_name,
                        final_score=final_score,
                        judge_opinions=crit_ops,
                        dissent_summary=dissent_summary,
                        remediation=remediation,
                        score_variance=score_variance,
                        resolution_rule=resolution_rule,
                    )
                )
            else:
                criteria.append(
                    CriterionResult(
                        dimension_id=dimension_id,
                        dimension_name=dimension_name,
                        final_score=3,
                        judge_opinions=[],
                        dissent_summary="No judge opinions provided; defaulting to neutral score.",
                        remediation=f"Review implementation for dimension '{dimension_name}'.",
                        score_variance=None,
                        resolution_rule=RULE_AVERAGE,
                    )
                )
    else:
        seen_ids = {op.criterion_id for op in opinions}
        for cid in seen_ids:
            crit_ops = [op for op in opinions if op.criterion_id == cid]
            final_score, dissent_summary, resolution_rule, score_variance = _resolve_conflict(
                crit_ops, cid, evidences
            )
            criteria.append(
                CriterionResult(
                    dimension_id=cid,
                    dimension_name=cid,
                    final_score=final_score,
                    judge_opinions=crit_ops,
                    dissent_summary=dissent_summary,
                    remediation=f"Review implementation for criterion '{cid}'.",
                    score_variance=score_variance,
                    resolution_rule=resolution_rule,
                )
            )

    if criteria:
        overall_score = sum(c.final_score for c in criteria) / len(criteria)
    else:
        overall_score = 3.0

    executive_summary = (
        "Automated audit completed. Scores are determined by explicit conflict-resolution rules "
        "(security override, fact-over-claims, Tech Lead weighting, majority/average). "
        "When judges strongly disagree (score variance ≥ 2), re-evaluation is triggered and "
        "dissent summaries are included in the report."
    )
    remediation_plan = (
        "Prioritize addressing low-scoring dimensions first. "
        "For each criterion, follow the remediation guidance listed above. "
        "Review dissent summaries where score variance was high."
    )

    report = AuditReport(
        repo_url=repo_url,
        executive_summary=executive_summary,
        overall_score=overall_score,
        criteria=criteria,
        remediation_plan=remediation_plan,
    )

    return {"final_report": report}
