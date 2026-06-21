"""
agents/resume_agent.py
-----------------------
Resume Analysis Agent — the first specialist in the Career Copilot pipeline.

Accepts raw resume text and returns a structured JSON profile with 8 fields:
candidate_name, current_title, total_experience_years, technical_skills,
soft_skills, education, certifications, summary.

Design note:
    Uses output_schema (constrained JSON generation) for guaranteed, type-safe
    output — consistent with all other agents in the pipeline.
    output_key="resume_analysis" saves the result to session state so
    GapAnalysisAgent and InterviewPrepAgent can read it automatically.
"""

import os

from google.adk.agents import LlmAgent
from pydantic import BaseModel, Field

from prompts import RESUME_AGENT_INSTRUCTION


# ---------------------------------------------------------------------------
# Output Schema
# ---------------------------------------------------------------------------

class ResumeAnalysisOutput(BaseModel):
    """Structured output from the Resume Analysis Agent."""

    candidate_name: str = Field(
        description="Full name of the candidate. 'Not provided' if absent."
    )

    current_title: str = Field(
        description="Most recent job title. 'Not provided' if absent."
    )

    total_experience_years: float = Field(
        ge=0,
        description=(
            "Total years of professional experience, calculated from the earliest "
            "role to present. Rounded to one decimal place."
        )
    )

    technical_skills: list[str] = Field(
        description=(
            "All technical skills from the resume: languages, frameworks, platforms, "
            "cloud services, databases, DevOps tools. Concise names, deduplicated."
        )
    )

    soft_skills: list[str] = Field(
        description=(
            "Soft skills and professional competencies found or inferred from "
            "role descriptions. Examples: 'cross-functional collaboration', "
            "'technical mentorship', 'incident management'."
        )
    )

    education: str = Field(
        description=(
            "Highest education level in format: "
            "'<Degree> in <Field>, <Institution> (<Year>)'. "
            "'Not provided' if absent."
        )
    )

    certifications: list[str] = Field(
        description=(
            "All professional certifications listed in the resume. "
            "Empty list [] if none."
        )
    )

    summary: str = Field(
        description=(
            "2–3 sentence objective summary of the candidate: "
            "experience level, primary tech stack, and most notable strength."
        )
    )


# ---------------------------------------------------------------------------
# Resume Analysis Agent
# ---------------------------------------------------------------------------

resume_agent = LlmAgent(
    name="ResumeAnalysisAgent",

    model=os.getenv("MODEL_NAME", "gemini-2.0-flash"),

    description=(
        "Analyzes raw resume text and returns a structured JSON profile with: "
        "candidate_name, current_title, total_experience_years, technical_skills, "
        "soft_skills, education, certifications, and a summary. "
        "Call this agent when you have resume text that needs to be parsed."
    ),

    instruction=RESUME_AGENT_INSTRUCTION,

    # Enforces the exact 8-field JSON schema via constrained decoding.
    output_schema=ResumeAnalysisOutput,

    # Saves validated output to session.state["resume_analysis"] so
    # GapAnalysisAgent and InterviewPrepAgent can read it automatically.
    output_key="resume_analysis",
)
