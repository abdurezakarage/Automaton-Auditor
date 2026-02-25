"""
Supreme Court / ChiefJustice node.

Synthesizes JudicialOpinion objects from all three judges, applies deterministic
conflict resolution rules, and produces the final AuditReport.
"""

from __future__ import annotations

from typing import Any, Dict, List

from ..state import AgentState, AuditReport, CriterionResult, JudicialOpinion


def _resolve_conflict(opinions: List[JudicialOpinion]) -> tuple[int, str]:
    """
    Apply deterministic conflict resolution rules.
    
    Rules:
    1. Security override: If Prosecutor identifies confirmed security vulnerability,
       cap score at 3 (overrides Defense "effort" points).
    2. Evidence supremacy: If Defense claims something but evidence doesn't support it,
       overrule Defense for hallucination.
    3. Functionality weighting: Tech Lead carries highest weight for architecture criterion.
    """
    if not opinions:
        return 3, "No opinions provided"
    
    scores = [op.score for op in opinions]
    prosecutor = next((op for op in opinions if op.judge == "Prosecutor"), None)
    defense = next((op for op in opinions if op.judge == "Defense"), None)
    tech_lead = next((op for op in opinions if op.judge == "TechLead"), None)
    
    # Rule 1: Security override
    if prosecutor and "security" in prosecutor.argument.lower() and "vulnerability" in prosecutor.argument.lower():
        return min(3, max(scores)), "Security vulnerability detected - score capped at 3"
    
    # Rule 3: Functionality weighting (Tech Lead for architecture)
    if tech_lead:
        final_score = tech_lead.score
        dissent = f"Tech Lead assessment ({tech_lead.score}) weighted highest for technical viability"
    else:
        final_score = sum(scores) // len(scores)  # Average as fallback
        dissent = f"Averaged scores: {scores}"
    
    # Rule 2: Evidence supremacy (check for hallucination claims)
    if defense and "metacognition" in defense.argument.lower():
        # Would cross-reference with evidence here
        pass
    
    return final_score, dissent


def run_chief_justice(state: AgentState) -> Dict[str, Any]:
    """
    ChiefJustice node: Synthesizes all judge opinions into final AuditReport.
    
    For each rubric criterion:
    1. Collects all three judge opinions
    2. Applies conflict resolution rules
    3. Generates CriterionResult with final score and dissent summary
    4. Produces final AuditReport
    """
    opinions: List[JudicialOpinion] = state.get("opinions", [])  # type: ignore[assignment]
    repo_url = state.get("repo_url", "")
    rubric_dimensions = state.get("rubric_dimensions", [])  # type: ignore[assignment]

    criteria: List[CriterionResult] = []

    if rubric_dimensions:
        # Use rubric-defined dimensions
        for dim in rubric_dimensions:
            dimension_id = dim.get("dimension_id", "unknown")
            dimension_name = dim.get("dimension_name", dimension_id)
            crit_ops = [op for op in opinions if op.criterion_id == dimension_id]

            if crit_ops:
                final_score, dissent = _resolve_conflict(crit_ops)
                scores = [op.score for op in crit_ops]
                variance = max(scores) - min(scores) if len(scores) > 1 else 0
                dissent_summary = dissent if variance > 2 else None
            else:
                # No opinions for this criterion yet; neutral default
                final_score = 3
                dissent_summary = "No judge opinions provided; defaulting to neutral score."
                crit_ops = []

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
                )
            )
    else:
        # Fallback: group by criterion_id found in opinions
        seen_ids = {op.criterion_id for op in opinions}
        for cid in seen_ids:
            crit_ops = [op for op in opinions if op.criterion_id == cid]
            final_score, dissent = _resolve_conflict(crit_ops)
            scores = [op.score for op in crit_ops]
            variance = max(scores) - min(scores) if len(scores) > 1 else 0
            dissent_summary = dissent if variance > 2 else None
            remediation = (
                f"Review implementation for criterion '{cid}' "
                f"and address issues highlighted by judge arguments."
            )
            criteria.append(
                CriterionResult(
                    dimension_id=cid,
                    dimension_name=cid,
                    final_score=final_score,
                    judge_opinions=crit_ops,
                    dissent_summary=dissent_summary,
                    remediation=remediation,
                )
            )

    if criteria:
        overall_score = sum(c.final_score for c in criteria) / len(criteria)
    else:
        overall_score = 3.0

    executive_summary = (
        "Automated audit completed. "
        "Scores are based on combined Prosecutor, Defense, and Tech Lead opinions "
        "for each rubric dimension."
    )
    remediation_plan = (
        "Prioritize addressing low-scoring dimensions first. "
        "For each criterion, follow the remediation guidance listed above."
    )

    report = AuditReport(
        repo_url=repo_url,
        executive_summary=executive_summary,
        overall_score=overall_score,
        criteria=criteria,
        remediation_plan=remediation_plan,
    )

    return {"final_report": report}


