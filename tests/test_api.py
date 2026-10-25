# -*- coding: utf-8 -*-
"""
tests/test_api.py
-----------------
Unit and integration tests for FastAPI backend in api/server.py.
"""

import io
import unittest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from api.server import (
    app,
    sanitize_text,
    extract_text_from_upload,
    build_response,
    _score_label,
    _score_color,
    _parse,
)


class TestApiServer(unittest.TestCase):
    """Test api/server.py endpoints and middleware."""

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_health_endpoint(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["model"], "gemini-2.5-flash")
        self.assertIn("api_key_configured", data)

    def test_security_headers_present(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.headers.get("X-Frame-Options"), "DENY")
        self.assertEqual(response.headers.get("X-Content-Type-Options"), "nosniff")
        self.assertEqual(response.headers.get("X-XSS-Protection"), "1; mode=block")
        self.assertIn("default-src 'self'", response.headers.get("Content-Security-Policy", ""))

    def test_sanitize_text(self):
        dirty = "<script>alert('xss')</script>Hello\x00 World!\x1f"
        clean = sanitize_text(dirty)
        self.assertEqual(clean, "alert('xss')Hello World!")
        self.assertEqual(sanitize_text(""), "")

    def test_extract_text_from_upload_invalid_pdf_header(self):
        fake_bytes = b"NOT_A_PDF_FILE"
        with self.assertRaises(HTTPException) as ctx:
            extract_text_from_upload(fake_bytes, "resume.pdf")
        self.assertEqual(ctx.exception.status_code, 422)

    def test_extract_text_from_upload_text_file(self):
        raw_text = "John Doe\nSoftware Engineer\nPython, Docker"
        extracted = extract_text_from_upload(raw_text.encode("utf-8"), "resume.txt")
        self.assertIn("John Doe", extracted)
        self.assertIn("Software Engineer", extracted)

    def test_score_label_and_color_mappings(self):
        self.assertEqual(_score_label(90), "Excellent Match")
        self.assertEqual(_score_label(70), "Good Match")
        self.assertEqual(_score_label(55), "Moderate Match")
        self.assertEqual(_score_label(40), "Weak Match")
        self.assertEqual(_score_label(20), "Poor Match")

        self.assertEqual(_score_color(85), "success")
        self.assertEqual(_score_color(55), "warning")
        self.assertEqual(_score_color(30), "danger")

    def test_parse_helper(self):
        self.assertEqual(_parse(None), {})
        self.assertEqual(_parse('{"key": "value"}'), {"key": "value"})
        self.assertEqual(_parse({"already": "dict"}), {"already": "dict"})
        self.assertEqual(_parse("invalid json"), {})

    def test_build_response_structure(self):
        dummy_state = {
            "resume_analysis": {
                "candidate_name": "Alex Smith",
                "current_title": "Full Stack Engineer",
                "total_experience_years": 5.0,
                "technical_skills": ["Python", "FastAPI", "React", "PostgreSQL"],
                "soft_skills": ["Leadership"],
                "education": "BS CS",
                "certifications": ["AWS Associate"],
            },
            "job_analysis": {
                "required_skills": ["Python", "FastAPI", "Kubernetes"],
                "preferred_skills": ["Docker"],
                "seniority_level": "senior",
                "keywords": ["cloud native"],
            },
            "gap_analysis": {
                "match_score": 75,
                "missing_skills": ["Kubernetes"],
                "missing_keywords": ["cloud native"],
                "priority_gaps": [
                    {
                        "skill": "Kubernetes",
                        "priority": "HIGH",
                        "reason": "Required for microservice orchestration.",
                    }
                ],
            },
            "career_strategy": {
                "plan_30_day": ["Setup minikube"],
                "plan_60_day": ["Deploy service"],
                "plan_90_day": ["Get CKA"],
                "recommended_projects": [
                    {
                        "title": "K8s Microservice",
                        "description": "Deploy demo app",
                        "skills_covered": ["Kubernetes"],
                        "duration": "1 week",
                    }
                ],
                "learning_priorities": [
                    {
                        "skill": "Kubernetes",
                        "resource": "CKA course",
                        "timeframe": "4 weeks",
                        "priority": "HIGH",
                    }
                ],
            },
            "interview_prep": {
                "interview_questions": [
                    {"question": "What is a Pod in K8s?", "category": "technical", "difficulty": "medium"}
                ],
                "suggested_answers": [
                    {"question": "What is a Pod?", "answer_framework": "STAR", "key_points": ["Container wrapper"]}
                ],
                "preparation_areas": [
                    {"area": "K8s Architecture", "why_important": "Required", "action_items": ["Study Pods"]}
                ],
            },
        }

        resp = build_response(dummy_state)
        self.assertEqual(resp["candidate_name"], "Alex Smith")
        self.assertEqual(resp["current_title"], "Full Stack Engineer")
        self.assertEqual(resp["match_score"]["score"], 75)
        self.assertEqual(resp["match_score"]["label"], "Good Match")
        self.assertEqual(resp["match_score"]["color"], "success")
        self.assertIn("Kubernetes", resp["skill_gaps"]["missing_skills"])
        self.assertEqual(len(resp["interview_prep"]["technical_questions"]), 1)

    def test_analyze_endpoint_missing_job_description(self):
        files = {"resume_file": ("resume.txt", io.BytesIO(b"Candidate text"), "text/plain")}
        data = {"job_description": "   "}
        response = self.client.post("/api/analyze", files=files, data=data)
        self.assertEqual(response.status_code, 400)

    def test_client_ip_forwarded_for_header(self):
        response = self.client.get("/api/health", headers={"X-Forwarded-For": "203.0.113.195, 10.0.0.1"})
        self.assertEqual(response.status_code, 200)

    def test_health_check_exempt_from_rate_limit(self):
        # Even after multiple requests exceeding default limit, health check must remain available for Render
        for _ in range(15):
            res = self.client.get("/api/health", headers={"X-Forwarded-For": "198.51.100.22"})
            self.assertEqual(res.status_code, 200)


if __name__ == "__main__":
    unittest.main()
