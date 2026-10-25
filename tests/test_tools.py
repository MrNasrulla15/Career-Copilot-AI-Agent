# -*- coding: utf-8 -*-
"""
tests/test_tools.py
-------------------
Unit tests for deterministic specialist tools in tools/.
"""

import unittest
from tools.resume_tools import extract_skills, score_resume_section, detect_resume_format
from tools.job_tools import extract_job_requirements, classify_seniority, detect_tech_stack
from tools.gap_tools import compute_skill_overlap, prioritize_gaps, estimate_learning_time
from tools.strategy_tools import generate_action_items, recommend_resources, build_timeline
from tools.interview_tools import generate_interview_questions, draft_star_answer, create_cheat_sheet
from tools.pdf_parser import _clean_text


class TestResumeTools(unittest.TestCase):
    """Test tools/resume_tools.py functions."""

    def test_extract_skills_technical_and_soft(self):
        sample_text = (
            "Senior Backend Engineer with 7 years of experience in Python, FastAPI, Docker, and AWS. "
            "Proven track record in cross-functional collaboration, agile leadership, and system design."
        )
        res = extract_skills(sample_text)
        self.assertEqual(res["status"], "success")
        self.assertIn("python", res["technical_skills"])
        self.assertIn("fastapi", res["technical_skills"])
        self.assertIn("docker", res["technical_skills"])
        self.assertIn("aws", res["technical_skills"])
        self.assertIn("collaboration", res["soft_skills"])
        self.assertIn("agile", res["soft_skills"])
        self.assertGreaterEqual(res["total_found"], 5)

    def test_extract_skills_empty(self):
        res = extract_skills("")
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["total_found"], 0)

    def test_score_resume_section(self):
        experience_text = (
            "Architected and deployed microservices on Kubernetes, reducing latency by 45%. "
            "Led a team of 6 engineers and managed a $500k infrastructure budget."
        )
        res = score_resume_section(experience_text, "experience")
        self.assertEqual(res["status"], "success")
        self.assertIn("score", res)
        self.assertGreaterEqual(res["score"], 60)
        self.assertTrue(res["has_metrics"])

    def test_detect_resume_format(self):
        text = "Work Experience:\n2022 - Present: Tech Lead\n2019 - 2022: Senior Developer"
        res = detect_resume_format(text)
        self.assertEqual(res["status"], "success")
        self.assertIn("detected_sections", res)
        self.assertIn("word_count", res)


class TestJobTools(unittest.TestCase):
    """Test tools/job_tools.py functions."""

    def test_extract_job_requirements(self):
        jd = (
            "Required Qualifications:\n"
            "- Must have 5+ years of Python experience\n"
            "- Minimum 3 years with Docker and CI/CD pipelines\n\n"
            "Nice to have:\n"
            "- Familiarity with Kubernetes"
        )
        res = extract_job_requirements(jd)
        self.assertEqual(res["status"], "success")
        self.assertIn("hard_requirements", res)
        self.assertIn("preferred_requirements", res)
        self.assertEqual(res["min_experience_years"], 5)

    def test_classify_seniority(self):
        senior_jd = "Senior Software Architect with 8+ years experience in distributed systems."
        res = classify_seniority(senior_jd)
        self.assertEqual(res["status"], "success")
        self.assertIn("seniority_level", res)
        self.assertIn(res["seniority_level"], ["senior", "staff", "principal", "lead"])

    def test_detect_tech_stack(self):
        jd = "Looking for an engineer proficient in React, TypeScript, FastAPI, and MongoDB on AWS."
        res = detect_tech_stack(jd)
        self.assertEqual(res["status"], "success")
        self.assertIn("stack", res)
        self.assertIn("frontend", res["stack"])
        self.assertIn("react", res["stack"]["frontend"])
        self.assertEqual(res["cloud_provider"], "aws")


class TestGapTools(unittest.TestCase):
    """Test tools/gap_tools.py functions."""

    def test_compute_skill_overlap(self):
        candidate = ["Python", "FastAPI", "Docker", "Git"]
        required = ["Python", "FastAPI", "Kubernetes", "AWS"]
        preferred = ["Terraform"]

        res = compute_skill_overlap(candidate, required, preferred)
        self.assertEqual(res["status"], "success")
        self.assertIn("python", res["matched_skills"])
        self.assertIn("fastapi", res["matched_skills"])
        self.assertIn("kubernetes", res["critical_gaps"])
        self.assertIn("aws", res["critical_gaps"])
        self.assertIn("docker", res["bonus_skills"])
        self.assertGreater(res["match_score"], 0)
        self.assertLessEqual(res["match_score"], 100)

    def test_compute_skill_overlap_empty_inputs(self):
        res = compute_skill_overlap([], [])
        self.assertEqual(res["status"], "error")

    def test_prioritize_gaps(self):
        critical = ["Kubernetes", "AWS"]
        preferred = ["Terraform"]
        res = prioritize_gaps(critical, preferred, "DevOps Engineer")
        self.assertEqual(res["status"], "success")
        self.assertIn("high_priority", res)
        self.assertIn("medium_priority", res)
        self.assertIn("Kubernetes", res["high_priority"])

    def test_estimate_learning_time(self):
        skills = ["Kubernetes", "Docker"]
        res = estimate_learning_time(skills)
        self.assertEqual(res["status"], "success")
        self.assertIn("estimates", res)
        self.assertGreater(res["total_min_weeks"], 0)


class TestStrategyAndInterviewTools(unittest.TestCase):
    """Test tools/strategy_tools.py and tools/interview_tools.py."""

    def test_generate_action_items(self):
        res = generate_action_items(["Kubernetes"], ["Terraform"], ["Go"], job_title="Cloud Engineer")
        self.assertEqual(res["status"], "success")
        self.assertIn("day_30_actions", res)
        self.assertIn("day_60_actions", res)
        self.assertIn("day_90_actions", res)
        self.assertGreaterEqual(len(res["day_30_actions"]), 1)

    def test_recommend_resources(self):
        res = recommend_resources(["Python", "Kubernetes"])
        self.assertEqual(res["status"], "success")
        self.assertIn("resources", res)
        self.assertGreater(res["total"], 0)

    def test_generate_interview_questions(self):
        res = generate_interview_questions("Staff Engineer", ["Python", "AWS"], "senior")
        self.assertEqual(res["status"], "success")
        self.assertIn("technical_questions", res)
        self.assertIn("behavioral_questions", res)
        self.assertGreaterEqual(res["total_questions"], 1)

    def test_draft_star_answer(self):
        res = draft_star_answer(
            question="Tell me about a time you handled a production outage.",
            candidate_experience_summary="Lead engineer managing payment microservices.",
        )
        self.assertEqual(res["status"], "success")
        self.assertIn("star_framework", res)
        self.assertIn("Situation", res["star_framework"])


class TestPdfCleaner(unittest.TestCase):
    """Test text cleaning in tools/pdf_parser.py."""

    def test_clean_text_normalizes_ligatures(self):
        dirty = "The \ufb01le had an e\ufb04ort and \u201csmart quotes\u201d with \u2022 bullet points."
        cleaned = _clean_text(dirty)
        self.assertIn("file", cleaned)
        self.assertIn('"smart quotes"', cleaned)
        self.assertIn("- bullet points", cleaned)


if __name__ == "__main__":
    unittest.main()
