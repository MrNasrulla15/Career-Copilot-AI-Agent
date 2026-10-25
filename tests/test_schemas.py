# -*- coding: utf-8 -*-
"""
tests/test_schemas.py
---------------------
Unit tests validating Pydantic v2 schemas and constraints across all specialist agents.
"""

import unittest
from pydantic import ValidationError

from agents.resume_agent import ResumeAnalysisOutput
from agents.job_agent import JobAnalysisOutput
from agents.gap_agent import GapAnalysisOutput, PriorityGap
from agents.strategy_agent import (
    CareerStrategyOutput,
    ProjectRecommendation,
    LearningPriority,
)
from agents.interview_agent import (
    InterviewPrepOutput,
    InterviewQuestion,
    SuggestedAnswer,
    PreparationArea,
)


class TestResumeSchema(unittest.TestCase):
    """Test ResumeAnalysisOutput model."""

    def test_valid_resume_schema(self):
        data = {
            "candidate_name": "Jane Doe",
            "current_title": "Senior Backend Engineer",
            "total_experience_years": 6.5,
            "technical_skills": ["Python", "FastAPI", "PostgreSQL", "Docker"],
            "soft_skills": ["Cross-functional leadership", "Mentoring"],
            "education": "B.S. in Computer Science",
            "certifications": ["AWS Certified Solutions Architect"],
            "summary": "Experienced backend developer focused on scalable APIs.",
        }
        output = ResumeAnalysisOutput(**data)
        self.assertEqual(output.candidate_name, "Jane Doe")
        self.assertEqual(output.total_experience_years, 6.5)

    def test_negative_experience_rejected(self):
        data = {
            "candidate_name": "Jane Doe",
            "current_title": "Engineer",
            "total_experience_years": -2.0,
            "technical_skills": [],
            "soft_skills": [],
            "education": "None",
            "certifications": [],
            "summary": "Summary",
        }
        with self.assertRaises(ValidationError):
            ResumeAnalysisOutput(**data)


class TestJobSchema(unittest.TestCase):
    """Test JobAnalysisOutput model."""

    def test_valid_job_schema(self):
        data = {
            "required_skills": ["Python", "Docker", "PostgreSQL"],
            "preferred_skills": ["Kubernetes", "AWS"],
            "seniority_level": "senior",
            "keywords": ["distributed systems", "CI/CD", "microservices"],
        }
        output = JobAnalysisOutput(**data)
        self.assertEqual(output.seniority_level, "senior")

    def test_invalid_seniority_rejected(self):
        data = {
            "required_skills": ["Python"],
            "preferred_skills": [],
            "seniority_level": "grandmaster",  # Invalid enum
            "keywords": ["python"],
        }
        with self.assertRaises(ValidationError):
            JobAnalysisOutput(**data)


class TestGapSchema(unittest.TestCase):
    """Test GapAnalysisOutput and PriorityGap models."""

    def test_valid_gap_schema(self):
        data = {
            "match_score": 75,
            "missing_skills": ["Kubernetes", "Terraform"],
            "missing_keywords": ["cloud native", "observability"],
            "priority_gaps": [
                {
                    "skill": "Kubernetes",
                    "priority": "HIGH",
                    "reason": "Job requires production cluster deployment experience.",
                }
            ],
        }
        output = GapAnalysisOutput(**data)
        self.assertEqual(output.match_score, 75)
        self.assertEqual(output.priority_gaps[0].priority, "HIGH")

    def test_score_bounds_validation(self):
        with self.assertRaises(ValidationError):
            GapAnalysisOutput(
                match_score=150,  # exceeds 100
                missing_skills=[],
                missing_keywords=[],
                priority_gaps=[],
            )

        with self.assertRaises(ValidationError):
            GapAnalysisOutput(
                match_score=-5,  # below 0
                missing_skills=[],
                missing_keywords=[],
                priority_gaps=[],
            )

    def test_invalid_gap_priority(self):
        with self.assertRaises(ValidationError):
            PriorityGap(skill="AWS", priority="CRITICAL", reason="Need cloud")


class TestStrategySchema(unittest.TestCase):
    """Test CareerStrategyOutput and nested models."""

    def test_valid_strategy_schema(self):
        data = {
            "plan_30_day": ["Complete Kubernetes tutorial", "Update resume with Docker metrics"],
            "plan_60_day": ["Deploy demo app on EKS", "Practice mock interviews"],
            "plan_90_day": ["Apply to senior roles", "Write tech blog post"],
            "recommended_projects": [
                {
                    "title": "Cloud-Native Task Manager",
                    "description": "Full-stack service with FastAPI and PostgreSQL on K8s.",
                    "skills_covered": ["FastAPI", "Kubernetes", "PostgreSQL"],
                    "duration": "2 weeks",
                }
            ],
            "learning_priorities": [
                {
                    "skill": "Kubernetes",
                    "resource": "Kubernetes the Hard Way",
                    "timeframe": "3 weeks",
                    "priority": "HIGH",
                }
            ],
        }
        output = CareerStrategyOutput(**data)
        self.assertEqual(len(output.plan_30_day), 2)
        self.assertEqual(output.recommended_projects[0].duration, "2 weeks")


class TestInterviewSchema(unittest.TestCase):
    """Test InterviewPrepOutput and nested models."""

    def test_valid_interview_schema(self):
        data = {
            "interview_questions": [
                {
                    "question": "How do you handle database connection pooling in FastAPI?",
                    "category": "technical",
                    "difficulty": "medium",
                }
            ],
            "suggested_answers": [
                {
                    "question": "How do you handle database connection pooling in FastAPI?",
                    "answer_framework": "Explain async engine, pool sizing, and lifecycle handlers.",
                    "key_points": ["SQLAlchemy asyncpg", "pool_size and max_overflow"],
                }
            ],
            "preparation_areas": [
                {
                    "area": "System Architecture",
                    "why_important": "Senior role requires designing high throughput services.",
                    "action_items": ["Review Designing Data-Intensive Applications chapter 5"],
                }
            ],
        }
        output = InterviewPrepOutput(**data)
        self.assertEqual(output.interview_questions[0].category, "technical")
        self.assertEqual(output.interview_questions[0].difficulty, "medium")


if __name__ == "__main__":
    unittest.main()
