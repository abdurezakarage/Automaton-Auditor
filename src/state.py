from __future__ import annotations

import operator
from typing import Annotated, Dict, List, Literal, Optional

from pydantic import BaseModel, Field
from typing_extensions import TypedDict


class Evidence(BaseModel):
    goal: str = Field()
    found: bool = Field(description="Whether the artifact exists")
    content: Optional[str] = Field(default=None)
    location: str = Field(description="File path or commit hash")
    rationale: str = Field(
        description=(
            "Your rationale for your confidence on the evidence you find "
            "for this particular goal"
        )
    )
    confidence: float
    correlates_with: Optional[List[str]] = Field(
        default=None,
        description="Keys of other evidence buckets (e.g. repo, doc, vision) this evidence correlates with",
    )


class JudicialOpinion(BaseModel):
    judge: Literal["Prosecutor", "Defense", "TechLead"]
    criterion_id: str
    score: int = Field(ge=1, le=5)
    argument: str
    cited_evidence: List[str]


class CriterionResult(BaseModel):
    dimension_id: str
    dimension_name: str
    final_score: int = Field(ge=1, le=5)
    judge_opinions: List[JudicialOpinion]
    dissent_summary: Optional[str] = Field(
        default=None, description="Required when score variance > 2"
    )
    remediation: str = Field(
        description="Specific file-level instructions for improvement",
    )
    # Explicit conflict resolution: variance and which named rule was applied
    score_variance: Optional[int] = Field(
        default=None,
        description="Max minus min judge score; triggers dissent when >= 2",
    )
    resolution_rule: Optional[str] = Field(
        default=None,
        description="Named rule applied: security_override, fact_over_claims, tech_lead_weighting, majority, average",
    )


class AuditReport(BaseModel):
    repo_url: str
    executive_summary: str
    overall_score: float
    criteria: List[CriterionResult]
    remediation_plan: str


class AgentState(TypedDict, total=False):
    repo_url: str
    pdf_path: str
    rubric_dimensions: List[Dict]
    evidences: Annotated[Dict[str, List[Evidence]], operator.ior]
    opinions: Annotated[List[JudicialOpinion], operator.add]
    final_report: Optional[AuditReport]
    # Failure tracking: node_id -> error message; merged so parallel branches can each set errors
    errors: Annotated[Dict[str, str], operator.ior]

