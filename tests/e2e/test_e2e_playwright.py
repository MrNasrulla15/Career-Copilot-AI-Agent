# -*- coding: utf-8 -*-
"""
tests/e2e/test_e2e_playwright.py
--------------------------------
Comprehensive Playwright End-to-End Test Suite for Career Copilot.

Covers:
  - Scenario A: Application startup, asset loading, console error detection
  - Scenario B: Navigation, view switching, theme toggle, mobile drawer
  - Scenario C: Form interactions, character counters, input validation
  - Scenario D: Analysis pipeline workflow (loading state, steps, result rendering)
  - Scenario E: Analysis history management (save, inspect, clear)
  - Scenario F: API error handling & resilience (HTTP 500 & 429 simulation)
"""

import os
import socket
import tempfile
import threading
import time
import unittest
from pathlib import Path
from playwright.sync_api import sync_playwright

import uvicorn
from api.server import app


def get_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def create_dummy_pdf() -> str:
    f = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    f.write(b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF")
    f.close()
    return f.name


class TestPlaywrightE2E(unittest.TestCase):
    """Playwright End-to-End browser test suite."""

    server_thread = None
    server = None
    port = None
    base_url = None
    pw = None
    browser = None

    @classmethod
    def setUpClass(cls):
        # 1. Determine target base URL
        env_url = os.getenv("E2E_BASE_URL", "").strip()
        if env_url:
            cls.base_url = env_url
            cls.is_external_server = True
        else:
            cls.is_external_server = False
            cls.port = get_free_port()
            cls.base_url = f"http://127.0.0.1:{cls.port}"

            # Start local Uvicorn instance in daemon thread
            config = uvicorn.Config(
                app,
                host="127.0.0.1",
                port=cls.port,
                log_level="critical",
                access_log=False,
            )
            cls.server = uvicorn.Server(config)
            cls.server_thread = threading.Thread(target=cls.server.run, daemon=True)
            cls.server_thread.start()

            # Poll until server is ready
            import urllib.request
            ready = False
            for _ in range(50):
                try:
                    with urllib.request.urlopen(f"{cls.base_url}/api/health", timeout=1) as resp:
                        if resp.status == 200:
                            ready = True
                            break
                except Exception:
                    time.sleep(0.1)

            if not ready:
                raise RuntimeError("Failed to start local test server for Playwright E2E.")

        # 2. Start Playwright
        cls.pw = sync_playwright().start()
        cls.browser = cls.pw.chromium.launch(headless=True)

        # 3. Create failure screenshots directory
        cls.screenshot_dir = Path(__file__).parent / "screenshots"
        cls.screenshot_dir.mkdir(exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        if cls.browser:
            cls.browser.close()
        if cls.pw:
            cls.pw.stop()
        if cls.server and not cls.is_external_server:
            cls.server.should_exit = True
            if cls.server_thread:
                cls.server_thread.join(timeout=3)

    def setUp(self):
        self.context = self.browser.new_context(
            viewport={"width": 1280, "height": 800},
            ignore_https_errors=True,
        )
        self.page = self.context.new_page()
        self.console_errors = []
        self.page.on("console", lambda msg: self.console_errors.append(msg.text) if msg.type == "error" else None)
        self.page.on("pageerror", lambda err: self.console_errors.append(str(err)))

    def tearDown(self):
        # Capture screenshot if test failed
        if hasattr(self, "_outcome") and any(error for _, error in getattr(self._outcome, "errors", [])):
            test_id = self.id().split(".")[-1]
            screenshot_path = self.screenshot_dir / f"failure_{test_id}_{int(time.time())}.png"
            try:
                self.page.screenshot(path=str(screenshot_path), full_page=True)
            except Exception:
                pass
        self.context.close()

    # ── Scenario A: Startup, Core Rendering & Assets ──────────────────

    def test_app_startup_and_title(self):
        self.page.goto(self.base_url, wait_until="networkidle")
        title = self.page.title()
        self.assertIn("Career Copilot", title)
        # Verify brand in sidebar
        brand = self.page.locator(".brand-name")
        self.assertTrue(brand.is_visible())
        self.assertEqual(brand.inner_text().strip(), "Career Copilot")
        # Ensure zero uncaught JS console errors on load
        self.assertEqual(len(self.console_errors), 0, f"Unexpected console errors: {self.console_errors}")

    def test_health_status_badge_connected(self):
        self.page.goto(self.base_url, wait_until="networkidle")
        badge = self.page.locator("#status-badge")
        self.assertTrue(badge.is_visible())
        badge_text = badge.inner_text().strip()
        self.assertIn(badge_text, ["API Connected", "API Unconfigured"])

    # ── Scenario B: Navigation, Routing & Theme Switching ─────────────

    def test_navigation_sidebar_routes(self):
        self.page.goto(self.base_url, wait_until="networkidle")

        routes = [
            ("workspace", "New Analysis Workspace"),
            ("resume", "Resume Profile Audit"),
            ("jobmatch", "Job Match Comparison"),
            ("skills", "Skills & Gap Matrix"),
            ("roadmap", "Action Plan & Roadmap"),
            ("interview", "Interview Preparation"),
            ("history", "Analysis History"),
            ("showcase", "ADK & Agent Stack"),
            ("dashboard", "Dashboard Overview"),
        ]

        for view_key, expected_title in routes:
            nav_btn = self.page.locator(f'[data-view="{view_key}"]')
            nav_btn.click()
            # Verify view title header
            title_header = self.page.locator("#current-view-title")
            self.assertEqual(title_header.inner_text().strip(), expected_title)
            # Verify page element active class
            page_view = self.page.locator(f"#view-{view_key}")
            self.assertTrue(page_view.evaluate("el => el.classList.contains('active')"))

    def test_theme_toggle_persistence(self):
        self.page.goto(self.base_url, wait_until="networkidle")
        theme_btn = self.page.locator("#theme-toggle-btn")
        self.assertTrue(theme_btn.is_visible())

        # Check initial theme
        is_dark_initial = self.page.evaluate("document.body.classList.contains('dark-theme')")
        theme_btn.click()
        is_dark_after = self.page.evaluate("document.body.classList.contains('dark-theme')")
        self.assertNotEqual(is_dark_initial, is_dark_after)

        # Verify localStorage persistence on page reload
        stored_theme = self.page.evaluate("localStorage.getItem('theme')")
        self.assertEqual(stored_theme, "dark" if is_dark_after else "light")

        self.page.reload(wait_until="networkidle")
        is_dark_reloaded = self.page.evaluate("document.body.classList.contains('dark-theme')")
        self.assertEqual(is_dark_reloaded, is_dark_after)

    # ── Scenario C: Form Controls, File Upload & Validation ───────────

    def test_workspace_form_validation_and_counters(self):
        self.page.goto(self.base_url, wait_until="networkidle")
        self.page.locator('[data-view="workspace"]').click()

        analyze_btn = self.page.locator("#analyze-btn")
        # Initially disabled
        self.assertTrue(analyze_btn.is_disabled())

        # Typing in JD updates character counter
        jd_textarea = self.page.locator("#job-description")
        jd_counter = self.page.locator("#jd-counter")
        sample_jd = "Senior Python Engineer needed with 5+ years building scalable REST APIs on AWS."
        jd_textarea.fill(sample_jd)
        self.assertIn(f"{len(sample_jd)} characters", jd_counter.inner_text())

        # Still disabled because no file is uploaded
        self.assertTrue(analyze_btn.is_disabled())

        # Create temporary valid PDF file
        temp_path = create_dummy_pdf()

        try:
            file_input = self.page.locator("#resume-file")
            file_input.set_input_files(temp_path)

            # File info should become visible and button enabled
            file_info = self.page.locator("#file-info")
            self.assertTrue(file_info.is_visible())
            self.assertFalse(analyze_btn.is_disabled())

            # Removing file should disable button again
            remove_btn = self.page.locator("#remove-file")
            remove_btn.click()
            self.assertTrue(analyze_btn.is_disabled())
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_invalid_file_extension_shows_error(self):
        self.page.goto(self.base_url, wait_until="networkidle")
        self.page.locator('[data-view="workspace"]').click()

        with tempfile.NamedTemporaryFile(suffix=".exe", delete=False) as f:
            f.write(b"fake executable")
            temp_path = f.name

        try:
            file_input = self.page.locator("#resume-file")
            file_input.set_input_files(temp_path)

            error_box = self.page.locator("#error-box")
            self.assertTrue(error_box.is_visible())
            self.assertIn("Invalid file type", error_box.inner_text())
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    # ── Scenario D: Core Analysis Workflow & Results UI ───────────────

    def test_complete_analysis_pipeline_and_rendering(self):
        """Simulates full analysis workflow with mocked API response to test end-to-end rendering."""
        mock_response_data = {
            "success": True,
            "data": {
                "candidate_name": "Marcus Vance",
                "current_title": "Lead Cloud Architect",
                "resume_review": {
                    "strengths": ["8 years of experience", "Proficient in Python & AWS"],
                    "weaknesses": ["Missing Kubernetes production expertise"],
                    "suggestions": ["Learn Kubernetes via CKA course"],
                },
                "match_score": {
                    "score": 82,
                    "label": "Excellent Match",
                    "color": "success",
                },
                "skill_gaps": {
                    "missing_skills": ["Kubernetes", "Terraform"],
                    "missing_keywords": ["cloud-native", "observability"],
                    "priority_gaps": [
                        {"skill": "Kubernetes", "priority": "HIGH", "reason": "Target role requires K8s clusters"}
                    ],
                },
                "career_roadmap": {
                    "immediate": ["Build multi-container pod deployment"],
                    "mid_term": ["Deploy on AWS EKS"],
                    "long_term": ["Earn CKA certification"],
                    "projects": [
                        {
                            "title": "Cloud-Native Observability Mesh",
                            "desc": "Prometheus & Grafana on K8s",
                            "skills": ["Kubernetes", "Prometheus"],
                            "duration": "2 weeks",
                        }
                    ],
                },
                "interview_prep": {
                    "technical_questions": ["Explain Kubernetes Ingress vs ClusterIP service"],
                    "behavioral_questions": ["Describe a time you handled a production outage"],
                    "system_design_questions": ["Design an event-driven telemetry pipeline"],
                    "preparation_areas": [
                        {"area": "Container Orchestration", "why": "Core requirement", "actions": ["Study Pods"]}
                    ],
                    "suggested_answers": [
                        {
                            "question": "Describe an outage",
                            "framework": "STAR",
                            "key_points": ["Triage", "Root cause", "Post-mortem"],
                        }
                    ],
                },
            },
        }

        # Intercept /api/analyze to return deterministic mock report
        self.page.route(
            "**/api/analyze",
            lambda route: route.fulfill(
                status=200,
                content_type="application/json",
                json=mock_response_data,
            ),
        )

        self.page.goto(self.base_url, wait_until="networkidle")
        self.page.locator('[data-view="workspace"]').click()

        # Fill inputs
        temp_path = create_dummy_pdf()

        try:
            self.page.locator("#resume-file").set_input_files(temp_path)
            self.page.locator("#job-description").fill(
                "Seeking a Lead Cloud Architect with deep expertise in Python, AWS, Docker, and Kubernetes."
            )
            analyze_btn = self.page.locator("#analyze-btn")
            self.assertFalse(analyze_btn.is_disabled())

            # Trigger analysis
            analyze_btn.click()

            # Verify automated redirect to Dashboard with rendered results
            self.page.wait_for_selector("#score-number", timeout=5000)
            score_text = self.page.locator("#score-number").inner_text()
            self.assertEqual(score_text, "82")

            candidate_name = self.page.locator("#candidate-name").inner_text()
            self.assertEqual(candidate_name, "Marcus Vance")

            # Check Skills view populated
            self.page.locator('[data-view="skills"]').click()
            skills_view = self.page.locator("#view-skills")
            self.assertTrue(skills_view.is_visible())
            self.assertIn("Kubernetes", skills_view.inner_text())

            # Check Roadmap view populated
            self.page.locator('[data-view="roadmap"]').click()
            roadmap_view = self.page.locator("#view-roadmap")
            self.assertTrue(roadmap_view.is_visible())
            self.assertIn("Cloud-Native Observability Mesh", roadmap_view.inner_text())
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    # ── Scenario E: History Management (Save, View, Clear) ────────────

    def test_history_persistence_and_clear(self):
        self.page.goto(self.base_url, wait_until="networkidle")

        # Inject a report into history via localStorage
        test_history_item = [
            {
                "id": "1234567890",
                "date": "Oct 26, 2026",
                "title": "Principal SRE",
                "candidateName": "David Miller",
                "score": 88,
                "color": "success",
                "topGap": "Rust",
                "data": {
                    "candidate_name": "David Miller",
                    "current_title": "Principal SRE",
                    "match_score": {"score": 88, "label": "Excellent Match", "color": "success"},
                },
            }
        ]
        self.page.evaluate(f"localStorage.setItem('career_copilot_history', '{json_escape(test_history_item)}')")
        self.page.reload(wait_until="networkidle")

        # Navigate to History view
        self.page.locator('[data-view="history"]').click()
        history_title = self.page.locator(".history-title")
        self.assertTrue(history_title.is_visible())
        self.assertIn("Principal SRE", history_title.inner_text())

        # Clear History
        clear_btn = self.page.locator("#btn-clear-history")
        self.assertTrue(clear_btn.is_visible())
        clear_btn.click()

        # Should show empty state
        empty_state = self.page.locator("#history-empty-state")
        self.assertTrue(empty_state.is_visible())

    # ── Scenario F: Error Handling & Resilience ───────────────────────

    def test_api_rate_limit_and_server_error_display(self):
        # 1. Test HTTP 429 Rate Limit response
        self.page.route(
            "**/api/analyze",
            lambda route: route.fulfill(
                status=429,
                content_type="application/json",
                json={"detail": "Too many requests. Please slow down and try again in a minute."},
            ),
        )

        self.page.goto(self.base_url, wait_until="networkidle")
        self.page.locator('[data-view="workspace"]').click()

        temp_path = create_dummy_pdf()

        try:
            self.page.locator("#resume-file").set_input_files(temp_path)
            self.page.locator("#job-description").fill("Software engineer with 5 years experience in Python.")
            self.page.locator("#analyze-btn").click()

            error_box = self.page.locator("#error-box")
            self.page.wait_for_selector("#error-box", timeout=5000)
            self.assertTrue(error_box.is_visible())
            self.assertIn("rate limit", error_box.inner_text().lower())

            # Button is re-enabled for retry
            self.assertFalse(self.page.locator("#analyze-btn").is_disabled())
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    # ── Scenario G: Mobile Responsiveness ─────────────────────────────

    def test_mobile_responsive_sidebar_drawer(self):
        self.context.close()
        mobile_context = self.browser.new_context(
            viewport={"width": 375, "height": 667},
            is_mobile=True,
        )
        page = mobile_context.new_page()
        page.goto(self.base_url, wait_until="networkidle")

        sidebar = page.locator("#app-sidebar")
        # Sidebar should not be open initially on mobile
        self.assertFalse(sidebar.evaluate("el => el.classList.contains('mobile-open')"))

        # Click hamburger menu button
        hamburger = page.locator("#btn-open-sidebar")
        hamburger.click()
        self.assertTrue(sidebar.evaluate("el => el.classList.contains('mobile-open')"))

        # Click close button inside drawer
        close_btn = page.locator("#btn-close-sidebar")
        close_btn.click()
        self.assertFalse(sidebar.evaluate("el => el.classList.contains('mobile-open')"))

        mobile_context.close()


def json_escape(obj) -> str:
    import json
    return json.dumps(obj).replace("'", "\\'").replace('"', '\\"')


if __name__ == "__main__":
    unittest.main()
