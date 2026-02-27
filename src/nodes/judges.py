"""
Judicial layer nodes: Prosecutor, Defense, Tech Lead.

Each judge analyzes evidence through a distinct persona lens and returns
structured JudicialOpinion objects via .with_structured_output() or .bind_tools().
"""

from __future__ import annotations

from typing import Any, Dict, List

from langchain_core.prompts import ChatPromptTemplate  # type: ignore[import]

from ..state import AgentState, JudicialOpinion
from ..utils.llm_setup import get_llm


def run_prosecutor(state: AgentState) -> Dict[str, Any]:
    """
    Prosecutor node: Critical lens - "Trust No One. Assume Vibe Coding."

    Scrutinizes evidence for gaps, security flaws, and laziness.
    Returns one JudicialOpinion per rubric dimension via .with_structured_output().
    """
    evidences = state.get("evidences", {})  # type: ignore[assignment]
    rubric_dimensions = state.get("rubric_dimensions", [])  # type: ignore[assignment]

    try:
        llm = get_llm()
    except RuntimeError:
        # No LLM configured; return no opinions to keep pipeline running
        return {"opinions": []}

    structured_llm = llm.with_structured_output(JudicialOpinion)

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                (
                    "You are the Prosecutor in a digital courtroom. "
                    "Trust no one. Assume vibe coding. "
                    "You must look for missing structure, security issues, and laziness.\n"
                    "Return a JSON object matching the JudicialOpinion schema."
                ),
            ),
            (
                "user",
                (
                    "Rubric criterion ID: {criterion_id}\n"
                    "Rubric criterion name: {criterion_name}\n\n"
                    "Collected evidence:\n{evidences}\n"
                ),
            ),
        ]
    )

    opinions: List[JudicialOpinion] = []

    if rubric_dimensions:
        for dimension in rubric_dimensions:
            criterion_id = dimension.get("dimension_id", "overall")
            criterion_name = dimension.get("dimension_name", criterion_id)

            messages = prompt.format_messages(
                criterion_id=criterion_id,
                criterion_name=criterion_name,
                evidences=str(evidences),
            )

            try:
                opinion = structured_llm.invoke(messages)
            except Exception:
                # If LLM call fails for this criterion, skip it but continue others.
                continue

            opinion.judge = "Prosecutor"
            opinion.criterion_id = criterion_id
            opinions.append(opinion)
    else:
        # Fallback: single overall opinion if no rubric dimensions were provided.
        criterion_id = "overall"
        criterion_name = "Overall Quality"

        messages = prompt.format_messages(
            criterion_id=criterion_id,
            criterion_name=criterion_name,
            evidences=str(evidences),
        )

        try:
            opinion = structured_llm.invoke(messages)
        except Exception:
            return {"opinions": []}

        opinion.judge = "Prosecutor"
        opinion.criterion_id = criterion_id
        opinions.append(opinion)

    return {"opinions": opinions}


def run_defense(state: AgentState) -> Dict[str, Any]:
    """
    Defense Attorney node: Optimistic lens - "Reward Effort and Intent."

    Highlights creative workarounds, deep thought, and effort even if
    implementation is imperfect. Returns one JudicialOpinion per rubric dimension.
    """
    evidences = state.get("evidences", {})  # type: ignore[assignment]
    rubric_dimensions = state.get("rubric_dimensions", [])  # type: ignore[assignment]

    try:
        llm = get_llm()
    except RuntimeError:
        return {"opinions": []}

    structured_llm = llm.with_structured_output(JudicialOpinion)

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                (
                    "You are the Defense Attorney in a digital courtroom. "
                    "Reward effort and intent. Look for the 'spirit of the law'. "
                    "Highlight creativity, learning, and iteration even if code is imperfect.\n"
                    "Return a JSON object matching the JudicialOpinion schema."
                ),
            ),
            (
                "user",
                (
                    "Rubric criterion ID: {criterion_id}\n"
                    "Rubric criterion name: {criterion_name}\n\n"
                    "Collected evidence:\n{evidences}\n"
                ),
            ),
        ]
    )

    opinions: List[JudicialOpinion] = []

    if rubric_dimensions:
        for dimension in rubric_dimensions:
            criterion_id = dimension.get("dimension_id", "overall")
            criterion_name = dimension.get("dimension_name", criterion_id)

            messages = prompt.format_messages(
                criterion_id=criterion_id,
                criterion_name=criterion_name,
                evidences=str(evidences),
            )

            try:
                opinion = structured_llm.invoke(messages)
            except Exception:
                continue

            opinion.judge = "Defense"
            opinion.criterion_id = criterion_id
            opinions.append(opinion)
    else:
        criterion_id = "overall"
        criterion_name = "Overall Quality"

        messages = prompt.format_messages(
            criterion_id=criterion_id,
            criterion_name=criterion_name,
            evidences=str(evidences),
        )

        try:
            opinion = structured_llm.invoke(messages)
        except Exception:
            return {"opinions": []}

        opinion.judge = "Defense"
        opinion.criterion_id = criterion_id
        opinions.append(opinion)

    return {"opinions": opinions}


def run_tech_lead(state: AgentState) -> Dict[str, Any]:
    """
    Tech Lead node: Pragmatic lens - "Does it actually work? Is it maintainable?"

    Evaluates architectural soundness, code cleanliness, and practical viability.
    Acts as tie-breaker. Returns one JudicialOpinion per rubric dimension.
    """
    evidences = state.get("evidences", {})  # type: ignore[assignment]
    rubric_dimensions = state.get("rubric_dimensions", [])  # type: ignore[assignment]

    try:
        llm = get_llm()
    except RuntimeError:
        return {"opinions": []}

    structured_llm = llm.with_structured_output(JudicialOpinion)

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                (
                    "You are the Tech Lead in a digital courtroom. "
                    "Ignore vibes and effort; focus on whether the system works, "
                    "is secure, and is maintainable. Consider technical debt.\n"
                    "Return a JSON object matching the JudicialOpinion schema."
                ),
            ),
            (
                "user",
                (
                    "Rubric criterion ID: {criterion_id}\n"
                    "Rubric criterion name: {criterion_name}\n\n"
                    "Collected evidence:\n{evidences}\n"
                ),
            ),
        ]
    )

    opinions: List[JudicialOpinion] = []

    if rubric_dimensions:
        for dimension in rubric_dimensions:
            criterion_id = dimension.get("dimension_id", "overall")
            criterion_name = dimension.get("dimension_name", criterion_id)

            messages = prompt.format_messages(
                criterion_id=criterion_id,
                criterion_name=criterion_name,
                evidences=str(evidences),
            )

            try:
                opinion = structured_llm.invoke(messages)
            except Exception:
                continue

            opinion.judge = "TechLead"
            opinion.criterion_id = criterion_id
            opinions.append(opinion)
    else:
        criterion_id = "overall"
        criterion_name = "Overall Quality"

        messages = prompt.format_messages(
            criterion_id=criterion_id,
            criterion_name=criterion_name,
            evidences=str(evidences),
        )

        try:
            opinion = structured_llm.invoke(messages)
        except Exception:
            return {"opinions": []}

        opinion.judge = "TechLead"
        opinion.criterion_id = criterion_id
        opinions.append(opinion)

    return {"opinions": opinions}


