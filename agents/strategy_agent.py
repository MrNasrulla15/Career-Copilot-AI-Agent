"""
agents/strategy_agent.py
-------------------------
Career Strategy Agent — the fourth specialist in the Career Copilot pipeline.

Reads gap_analysis from session state (set by GapAnalysisAgent) and returns
a structured 5-field JSON career action plan with 30/60/90-day plans,
project recommendations, and ranked learning priorities.

Data flow:
    session.state["gap_analysis"] ──► CareerStrategyAgent ──► session.state["career_strategy"]

ADK session state injection:
    The instruction uses {{gap_analysis}} — ADK substitutes the live session
    state value at runtime, no manual data passing required.
"""

import os
from typing import Literal

from google.adk.agents import LlmAgent
from pydantic import BaseModel, Field

from prompts import STRATEGY_AGENT_INSTRUCTION


# ---------------------------------------------------------------------------
# Output Schema — nested models first, then root
# ---------------------------------------------------------------------------

class ProjectRecommendation(BaseModel):
    """A single hands-on project recommendation to close specific skill gaps."""

    title: str = Field(
        description="Short, descriptive name for the project (e.g., 'Distributed Rate Limiter Service')."
    )

    description: str = Field(
        description=(
            "2–3 sentences explaining what to build, why it matters for this candidate, "
            "and which specific gaps from the analysis it addresses."
        )
    )

    skills_covered: list[str] = Field(
        description="List of skills this project demonstrates (should overlap with missing_skills or priority_gaps)."
    )

    duration: str = Field(
        description="Realistic time estimate to complete the project (e.g., '1–2 weekends', '2 weeks')."
    )


class LearningPriority(BaseModel):
    """A single ranked learning item with a specific resource and timeframe."""

    skill: str = Field(
        description="The skill to learn — should match a gap from the gap analysis."
    )

    resource: str = Field(
        description=(
            "Specific learning resource: name the exact course, book, or platform. "
            "Example: 'Go by Example at gobyexample.com' or "
            "'Designing Data-Intensive Applications by Martin Kleppmann (O'Reilly)'."
        )
    )

    timeframe: str = Field(
        description="Realistic time to reach working proficiency (e.g., '2 weeks', '1 month', '6–8 weeks')."
    )

    priority: Literal["HIGH", "MEDIUM", "LOW"] = Field(
        description="Priority level — align with the priority_gaps field from the gap analysis."
    )


class CareerStrategyOutput(BaseModel):
    """Structured output from the Career Strategy Agent."""

    plan_30_day: list[str] = Field(
        description=(
            "6–10 specific, actionable items to complete in the first 30 days. "
            "Focus on HIGH-priority gap closure, resume/LinkedIn optimization, "
            "and foundational learning. Each item starts with an action verb "
            "and names a concrete resource or deliverable."
        )
    )

    plan_60_day: list[str] = Field(
        description=(
            "5–8 specific items for days 31–60. Focus on MEDIUM-priority gaps, "
            "building publicly visible proof of skills (GitHub, blog), "
            "starting job applications, and mock interviews."
        )
    )

    plan_90_day: list[str] = Field(
        description=(
            "4–7 specific items for days 61–90. Focus on LOW-priority gap closure, "
            "deepening skills already started, full application pipeline, "
            "salary negotiation prep, and community visibility."
        )
    )

    recommended_projects: list[ProjectRecommendation] = Field(
        description=(
            "3–5 hands-on projects the candidate should build to demonstrate skills "
            "and close gaps. Each has: title, description, skills_covered, duration."
        )
    )

    learning_priorities: list[LearningPriority] = Field(
        description=(
            "Ranked list of skills to learn, ordered HIGH → MEDIUM → LOW, then "
            "by time ascending (quick wins first). Each has: skill, resource, timeframe, priority."
        )
    )


# ---------------------------------------------------------------------------
# Career Strategy Agent
# ---------------------------------------------------------------------------
# Key design decisions:
#   - output_schema=CareerStrategyOutput: enforces the exact 5-field JSON structure
#     including nested ProjectRecommendation and LearningPriority models.
#   - output_key="career_strategy": persists the result to session state for
#     InterviewPrepAgent and the Coordinator's final report synthesis.
#   - {{gap_analysis}}: ADK injects the live session state value at runtime.
#     No tools needed — the LLM reasons directly from the injected gap data.
# ---------------------------------------------------------------------------

strategy_agent = LlmAgent(
    name="CareerStrategyAgent",

    model=os.getenv("MODEL_NAME", "gemini-2.0-flash"),

    description=(
        "Transforms a gap analysis report into a concrete, personalized 30/60/90-day "
        "career action plan. Returns: plan_30_day (immediate actions), plan_60_day "
        "(mid-term momentum), plan_90_day (long-term positioning), "
        "recommended_projects (hands-on builds to close gaps), and "
        "learning_priorities (ranked skills with specific resources and timeframes). "
        "Reads gap_analysis from session state automatically. "
        "Must be called after GapAnalysisAgent has completed."
    ),

    instruction=STRATEGY_AGENT_INSTRUCTION,

    # Enforces the 5-field schema with nested ProjectRecommendation + LearningPriority.
    output_schema=CareerStrategyOutput,

    # Saves to session.state["career_strategy"] for InterviewPrepAgent + Coordinator.
    output_key="career_strategy",
)
