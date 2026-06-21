"""
prompts/__init__.py
--------------------
Exports all agent system prompts from a single import point.

Usage:
    from prompts import RESUME_AGENT_INSTRUCTION, JOB_AGENT_INSTRUCTION, ...
"""

from prompts.resume_prompts import RESUME_AGENT_INSTRUCTION
from prompts.job_prompts import JOB_AGENT_INSTRUCTION
from prompts.gap_prompts import GAP_AGENT_INSTRUCTION
from prompts.strategy_prompts import STRATEGY_AGENT_INSTRUCTION
from prompts.interview_prompts import INTERVIEW_AGENT_INSTRUCTION
from prompts.coordinator_prompts import COORDINATOR_INSTRUCTION
from prompts.document_processor_prompts import DOCUMENT_PROCESSOR_INSTRUCTION

__all__ = [
    "RESUME_AGENT_INSTRUCTION",
    "JOB_AGENT_INSTRUCTION",
    "GAP_AGENT_INSTRUCTION",
    "STRATEGY_AGENT_INSTRUCTION",
    "INTERVIEW_AGENT_INSTRUCTION",
    "COORDINATOR_INSTRUCTION",
    "DOCUMENT_PROCESSOR_INSTRUCTION",
]
