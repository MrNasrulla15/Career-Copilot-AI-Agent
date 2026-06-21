"""
agents/job_agent.py
--------------------
Job Analysis Agent — the second specialist in the Career Copilot pipeline.

Accepts raw job description text and returns a structured JSON object with
exactly four fields: required_skills, preferred_skills, seniority_level, keywords.

Design note on output_schema vs tools:
    ADK's `output_schema` forces the model into JSON-constrained generation mode,
    which is incompatible with function calling (tools). Since Gemini extracts
    structured job info natively and more accurately than keyword-matching heuristics,
    we use output_schema here for guaranteed, type-safe JSON output.
    The job_tools.py module still exists for standalone / testing use.
"""

import os
from typing import Literal

from google.adk.agents import LlmAgent
from pydantic import BaseModel, Field

from prompts import JOB_AGENT_INSTRUCTION


# ---------------------------------------------------------------------------
# Output Schema
# ---------------------------------------------------------------------------
# Pydantic model that defines the exact JSON structure this agent must return.
# ADK enforces this schema via constrained decoding — the LLM cannot deviate.
# ---------------------------------------------------------------------------

class JobAnalysisOutput(BaseModel):
    """Structured output from the Job Analysis Agent."""

    required_skills: list[str] = Field(
        description=(
            "Must-have skills explicitly stated as required in the job description. "
            "Include technical skills, tools, frameworks, and languages. "
            "Each item should be a concise skill name (e.g., 'Python', 'PostgreSQL', 'Kubernetes')."
        )
    )

    preferred_skills: list[str] = Field(
        description=(
            "Nice-to-have or preferred skills mentioned as a bonus or 'preferred' in the job description. "
            "These are desirable but not mandatory. "
            "Each item should be a concise skill name."
        )
    )

    seniority_level: Literal[
        "intern",
        "junior",
        "mid",
        "senior",
        "staff",
        "principal",
        "lead",
        "manager",
        "director",
        "vp",
        "c-level",
        "unknown",
    ] = Field(
        description=(
            "Normalized seniority level of the role. "
            "Infer from the job title, years of experience required, and responsibility scope. "
            "Use 'unknown' only if there is genuinely no signal."
        )
    )

    keywords: list[str] = Field(
        description=(
            "High-value ATS and recruiter keywords extracted from the job description. "
            "Include role-specific terminology, domain keywords, methodologies, certifications, "
            "and any repeated or emphasized terms. "
            "These are the words a candidate should mirror in their resume and cover letter."
        )
    )


# ---------------------------------------------------------------------------
# Job Analysis Agent
# ---------------------------------------------------------------------------
# Key design decisions:
#   - output_schema=JobAnalysisOutput: ADK uses constrained JSON generation to
#     guarantee the response matches the Pydantic model exactly.
#   - output_key="job_analysis": ADK also saves the validated JSON to
#     session.state["job_analysis"] for downstream agents (GapAnalysisAgent, etc.).
#   - No tools: output_schema and function calling are mutually exclusive in ADK.
#     Gemini natively extracts structured info from text with high accuracy.
# ---------------------------------------------------------------------------

job_agent = LlmAgent(
    name="JobAnalysisAgent",

    model=os.getenv("MODEL_NAME", "gemini-2.5-flash"),

    description=(
        "Analyzes a raw job description and returns a structured JSON object with: "
        "required_skills (must-have), preferred_skills (nice-to-have), "
        "seniority_level (normalized label), and keywords (ATS/recruiter terms). "
        "Call this agent when you have a job description that needs to be parsed."
    ),

    instruction=JOB_AGENT_INSTRUCTION,

    # Enforces the exact 4-field JSON schema — the LLM cannot return anything else.
    output_schema=JobAnalysisOutput,

    # Also persists the validated output to session.state["job_analysis"]
    # so GapAnalysisAgent can read it without being passed the data explicitly.
    output_key="job_analysis",
)
