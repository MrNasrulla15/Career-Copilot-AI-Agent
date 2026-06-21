"""
agents/gap_agent.py
--------------------
Gap Analysis Agent — the third specialist in the Career Copilot pipeline.

Receives resume_analysis and job_analysis from session state (set by the two
upstream agents) and returns a structured JSON object with exactly four fields:
match_score, missing_skills, missing_keywords, priority_gaps.

Data flow:
    session.state["resume_analysis"]  ──┐
                                         ├──► GapAnalysisAgent ──► session.state["gap_analysis"]
    session.state["job_analysis"]     ──┘

ADK session state injection:
    The instruction uses {{resume_analysis}} and {{job_analysis}} placeholders.
    ADK automatically substitutes these with the live session state values at
    runtime — no manual data passing required.
"""

import os
from typing import Literal

from google.adk.agents import LlmAgent
from pydantic import BaseModel, Field

from prompts import GAP_AGENT_INSTRUCTION


# ---------------------------------------------------------------------------
# Output Schema
# ---------------------------------------------------------------------------

class PriorityGap(BaseModel):
    """A single prioritized skill gap with context."""

    skill: str = Field(
        description="The name of the missing skill or capability area."
    )

    priority: Literal["HIGH", "MEDIUM", "LOW"] = Field(
        description=(
            "Impact level of this gap: "
            "HIGH = likely disqualifier if unaddressed, "
            "MEDIUM = notable gap worth fixing before applying, "
            "LOW = nice-to-have, not a blocker."
        )
    )

    reason: str = Field(
        description=(
            "One sentence explaining why this is a gap and what its impact is "
            "on the candidate's fit for the role."
        )
    )


class GapAnalysisOutput(BaseModel):
    """Structured output from the Gap Analysis Agent."""

    match_score: int = Field(
        ge=0,
        le=100,
        description=(
            "Overall match score from 0–100 representing how well the candidate's "
            "resume aligns with the job requirements. "
            "Computed as: (required skill coverage * 70) + (preferred coverage * 20) "
            "+ (keyword coverage * 10). Be honest — do not inflate."
        )
    )

    missing_skills: list[str] = Field(
        description=(
            "Skills listed in the job's required_skills or preferred_skills that "
            "are NOT present anywhere in the resume analysis. "
            "Case-insensitive, normalized matching applied. "
            "Each entry is a concise skill name (e.g., 'Kafka', 'Terraform', 'Go')."
        )
    )

    missing_keywords: list[str] = Field(
        description=(
            "ATS/recruiter keywords from the job analysis that do NOT appear "
            "anywhere in the resume. These are terms the candidate should add "
            "to their resume to pass ATS screening. "
            "Return 8–20 of the most important missing keywords."
        )
    )

    priority_gaps: list[PriorityGap] = Field(
        description=(
            "Prioritized list of the most critical gaps the candidate must address. "
            "Each item has: skill (str), priority ('HIGH'|'MEDIUM'|'LOW'), reason (str). "
            "Ordered HIGH → MEDIUM → LOW. Includes all HIGH gaps, up to 5 MEDIUM, up to 3 LOW."
        )
    )


# ---------------------------------------------------------------------------
# Gap Analysis Agent
# ---------------------------------------------------------------------------
# Key design decisions:
#   - output_schema=GapAnalysisOutput: enforces the exact 4-field JSON structure.
#   - output_key="gap_analysis": persists the result to session state for
#     CareerStrategyAgent and InterviewPrepAgent to consume.
#   - No tools: output_schema and function calling are mutually exclusive in ADK.
#     The LLM performs the comparison directly from the injected session state.
#   - {{resume_analysis}} / {{job_analysis}}: ADK substitutes these placeholders
#     with the live session state values before sending the prompt to the LLM.
# ---------------------------------------------------------------------------

gap_agent = LlmAgent(
    name="GapAnalysisAgent",

    model=os.getenv("MODEL_NAME", "gemini-2.0-flash"),

    description=(
        "Compares a candidate's resume profile against a job's requirements and "
        "returns a structured gap report with: match_score (0-100), missing_skills, "
        "missing_keywords (ATS terms), and priority_gaps (HIGH/MEDIUM/LOW with reasons). "
        "Reads resume_analysis and job_analysis from session state automatically. "
        "Must be called after both ResumeAnalysisAgent and JobAnalysisAgent have completed."
    ),

    instruction=GAP_AGENT_INSTRUCTION,

    # Enforces the exact 4-field JSON schema with nested PriorityGap objects.
    output_schema=GapAnalysisOutput,

    # Persists the validated gap report to session.state["gap_analysis"]
    # for downstream agents (CareerStrategyAgent, InterviewPrepAgent).
    output_key="gap_analysis",
)
