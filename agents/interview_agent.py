"""
agents/interview_agent.py
--------------------------
Interview Preparation Agent — the fifth and final specialist in the pipeline.

Reads resume_analysis and job_analysis from session state (set by their
respective upstream agents) and returns a structured 3-field JSON interview
prep kit: interview_questions, suggested_answers, preparation_areas.

Data flow:
    session.state["resume_analysis"] ──┐
                                        ├──► InterviewPrepAgent ──► session.state["interview_prep"]
    session.state["job_analysis"]    ──┘

ADK session state injection:
    The instruction uses {{resume_analysis}} and {{job_analysis}} — ADK
    substitutes live session state values at runtime automatically.
"""

import os
from typing import Literal

from google.adk.agents import LlmAgent
from pydantic import BaseModel, Field

from prompts import INTERVIEW_AGENT_INSTRUCTION


# ---------------------------------------------------------------------------
# Output Schema
# ---------------------------------------------------------------------------

class InterviewQuestion(BaseModel):
    """A single interview question with category and difficulty metadata."""

    question: str = Field(
        description="The full interview question exactly as an interviewer would ask it."
    )

    category: Literal["technical", "behavioral", "system_design", "culture"] = Field(
        description=(
            "Question category: "
            "'technical' = coding/concepts, "
            "'behavioral' = STAR-method experience questions, "
            "'system_design' = architecture/scale questions, "
            "'culture' = values/fit questions."
        )
    )

    difficulty: Literal["easy", "medium", "hard"] = Field(
        description=(
            "Question difficulty relative to the role's seniority level. "
            "'easy' = foundational, 'medium' = expected competency, "
            "'hard' = differentiator/depth question."
        )
    )


class SuggestedAnswer(BaseModel):
    """Answer framework for a single high-priority interview question."""

    question: str = Field(
        description="The exact question text — must match one from interview_questions."
    )

    answer_framework: str = Field(
        description=(
            "3–5 sentence coaching narrative describing HOW to answer this question. "
            "For behavioral: STAR method (Situation, Task, Action, Result). "
            "For technical: key concepts to cover and presentation order. "
            "For system design: requirements → scale estimation → components → trade-offs."
        )
    )

    key_points: list[str] = Field(
        description=(
            "3–5 concrete bullet points the candidate MUST include in their answer. "
            "Ground these in the candidate's actual resume experience where possible."
        )
    )


class PreparationArea(BaseModel):
    """A broad preparation area with specific action items."""

    area: str = Field(
        description=(
            "Name of the preparation area "
            "(e.g., 'Go Language Fundamentals', 'System Design Patterns', "
            "'Behavioral Story Bank', 'Company & Domain Research')."
        )
    )

    why_important: str = Field(
        description=(
            "1–2 sentences explaining why this area matters specifically for "
            "this candidate targeting this role. Be concrete and specific."
        )
    )

    action_items: list[str] = Field(
        description=(
            "3–5 concrete preparation tasks, each achievable in 1–3 days. "
            "Name specific resources, exercises, or deliverables."
        )
    )


class InterviewPrepOutput(BaseModel):
    """Structured output from the Interview Preparation Agent."""

    interview_questions: list[InterviewQuestion] = Field(
        description=(
            "12–18 realistic interview questions tailored to the candidate and role. "
            "Mix: 5–7 technical, 4–5 behavioral, 2–4 system_design, 1–2 culture. "
            "Each has: question (str), category (enum), difficulty (enum)."
        )
    )

    suggested_answers: list[SuggestedAnswer] = Field(
        description=(
            "Answer frameworks for the 8–10 highest-impact questions. "
            "Prioritise system design, hard behavioral, and core technical questions. "
            "Each has: question (str), answer_framework (str), key_points (list[str])."
        )
    )

    preparation_areas: list[PreparationArea] = Field(
        description=(
            "4–6 broad preparation areas with specific action items. "
            "Always include: technical gap areas, behavioral story bank, "
            "company/domain research, and system design (if senior+). "
            "Each has: area (str), why_important (str), action_items (list[str])."
        )
    )


# ---------------------------------------------------------------------------
# Interview Preparation Agent
# ---------------------------------------------------------------------------
# Key design decisions:
#   - output_schema=InterviewPrepOutput: enforces the exact 3-field JSON structure
#     with three distinct nested models (Question, Answer, PrepArea).
#   - output_key="interview_prep": saves to session state for the Coordinator
#     to include in the final Career Intelligence Report.
#   - {{resume_analysis}} / {{job_analysis}}: ADK injects these from session
#     state at runtime — the agent gets full candidate context automatically.
#   - No tools: output_schema and function calling are mutually exclusive in ADK.
#     Gemini generates all content directly from the injected session context.
# ---------------------------------------------------------------------------

interview_agent = LlmAgent(
    name="InterviewPrepAgent",

    model=os.getenv("MODEL_NAME", "gemini-2.0-flash"),

    description=(
        "Generates a personalized interview preparation kit for a candidate "
        "targeting a specific role. Returns: interview_questions (12–18 questions "
        "with category and difficulty), suggested_answers (STAR/technical frameworks "
        "for the top 8–10 questions), and preparation_areas (4–6 focused study "
        "areas with concrete action items). "
        "Reads resume_analysis and job_analysis from session state automatically. "
        "Must be called after ResumeAnalysisAgent and JobAnalysisAgent have completed."
    ),

    instruction=INTERVIEW_AGENT_INSTRUCTION,

    # Enforces the 3-field schema with nested InterviewQuestion,
    # SuggestedAnswer, and PreparationArea models.
    output_schema=InterviewPrepOutput,

    # Saves to session.state["interview_prep"] for the Coordinator.
    output_key="interview_prep",
)
