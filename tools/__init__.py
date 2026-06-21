"""
tools/__init__.py
------------------
Exports all FunctionTool wrappers from a single import point.

ADK's FunctionTool wraps a plain Python callable so the LLM can invoke it.
The function's name and docstring are used by the LLM to determine when/how to call it.

Usage:
    from tools import resume_tools_list, job_tools_list, ...
"""

from google.adk.tools import FunctionTool

# --- Resume Tools ---
from tools.resume_tools import extract_skills, score_resume_section, detect_resume_format

# --- Job Tools ---
from tools.job_tools import extract_job_requirements, classify_seniority, detect_tech_stack

# --- Gap Tools ---
from tools.gap_tools import compute_skill_overlap, prioritize_gaps, estimate_learning_time

# --- Strategy Tools ---
from tools.strategy_tools import generate_action_items, recommend_resources, build_timeline

# --- Interview Tools ---
from tools.interview_tools import generate_interview_questions, draft_star_answer, create_cheat_sheet

# --- PDF Parser ---
from tools.pdf_parser import pdf_parser_tool, extract_text_from_pdf


# Wrap each callable in a FunctionTool for ADK
resume_tools_list = [
    FunctionTool(func=extract_skills),
    FunctionTool(func=score_resume_section),
    FunctionTool(func=detect_resume_format),
]

job_tools_list = [
    FunctionTool(func=extract_job_requirements),
    FunctionTool(func=classify_seniority),
    FunctionTool(func=detect_tech_stack),
]

gap_tools_list = [
    FunctionTool(func=compute_skill_overlap),
    FunctionTool(func=prioritize_gaps),
    FunctionTool(func=estimate_learning_time),
]

strategy_tools_list = [
    FunctionTool(func=generate_action_items),
    FunctionTool(func=recommend_resources),
    FunctionTool(func=build_timeline),
]

interview_tools_list = [
    FunctionTool(func=generate_interview_questions),
    FunctionTool(func=draft_star_answer),
    FunctionTool(func=create_cheat_sheet),
]


__all__ = [
    "resume_tools_list",
    "job_tools_list",
    "gap_tools_list",
    "strategy_tools_list",
    "interview_tools_list",
    "pdf_parser_tool",
    "extract_text_from_pdf",
]
