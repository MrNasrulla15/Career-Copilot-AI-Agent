"""
agents/__init__.py
-------------------
Exports all agent instances from a single import point.

Usage:
    from agents import resume_agent, job_agent, gap_agent, strategy_agent, interview_agent
    from agents import coordinator_agent
"""

from agents.resume_agent import resume_agent
from agents.job_agent import job_agent
from agents.gap_agent import gap_agent
from agents.strategy_agent import strategy_agent
from agents.interview_agent import interview_agent

# Coordinator is imported separately to avoid circular imports
# (coordinator imports all other agents)
# Use: from agents.coordinator import coordinator_agent

__all__ = [
    "resume_agent",
    "job_agent",
    "gap_agent",
    "strategy_agent",
    "interview_agent",
]
