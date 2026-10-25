# -*- coding: utf-8 -*-
"""
tests/test_mcp_server.py
------------------------
Unit tests for the FastMCP document processor tools in mcp_server/server.py.
"""

import json
import unittest

from mcp_server.server import extract_resume_text, parse_resume_sections


class TestMcpServer(unittest.TestCase):
    """Test mcp_server/server.py tool functions."""

    def test_extract_resume_text_nonexistent_file(self):
        result = extract_resume_text("non_existent_path_12345.pdf")
        self.assertTrue(result.startswith("ERROR: File not found"))

    def test_parse_resume_sections_empty(self):
        raw_json = parse_resume_sections("")
        parsed = json.loads(raw_json)
        self.assertIn("error", parsed)

    def test_parse_resume_sections_valid(self):
        resume_text = (
            "Alice Johnson\nalice@example.com\n\n"
            "Summary\nExperienced AI Engineer with 5 years in production NLP.\n\n"
            "Experience\nSenior ML Engineer at TechCorp (2021-Present)\n- Built RAG pipelines.\n\n"
            "Education\nB.S. in Computer Science, Stanford University\n\n"
            "Skills\nPython, PyTorch, LangChain, Docker"
        )
        raw_json = parse_resume_sections(resume_text)
        data = json.loads(raw_json)
        self.assertIn("metadata", data)
        self.assertIn("sections", data)
        self.assertIn("summary", data["sections"])
        self.assertIn("experience", data["sections"])
        self.assertIn("education", data["sections"])
        self.assertIn("skills", data["sections"])
        self.assertEqual(data["metadata"]["candidate_name_guess"], "Alice Johnson")


if __name__ == "__main__":
    unittest.main()
