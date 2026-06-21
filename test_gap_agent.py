# -*- coding: utf-8 -*-
"""
test_gap_agent.py
------------------
End-to-end test for the Gap Analysis Agent.

Pipeline:
    1. Seeds session.state["resume_analysis"] with a mock resume profile
    2. Seeds session.state["job_analysis"]    with a mock job analysis
       (matching the JobAnalysisOutput schema — as if JobAnalysisAgent ran)
    3. Runs GapAnalysisAgent and validates the 4-field structured output

This tests the agent in isolation without needing ResumeAnalysisAgent or
JobAnalysisAgent to run first — we inject the upstream outputs directly.

Usage:
    python test_gap_agent.py
"""

import asyncio
import json
import os
import uuid

from dotenv import load_dotenv
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

load_dotenv()

from agents.gap_agent import gap_agent


# ---------------------------------------------------------------------------
# Mock upstream outputs
# (simulates what ResumeAnalysisAgent + JobAnalysisAgent would have produced)
# ---------------------------------------------------------------------------

# What the ResumeAnalysisAgent would have stored in session.state
MOCK_RESUME_ANALYSIS = """
{
  "candidate_name": "Alex Rivera",
  "total_experience_years": 4,
  "current_title": "Backend Engineer",
  "technical_skills": [
    "Python", "FastAPI", "Django", "PostgreSQL", "Redis",
    "Docker", "AWS EC2", "AWS S3", "REST APIs", "Git",
    "GitHub Actions", "JavaScript", "SQL"
  ],
  "soft_skills": ["collaboration", "problem-solving", "communication"],
  "education": "B.S. Computer Science",
  "certifications": [],
  "summary": "4-year backend engineer with Python/FastAPI focus and AWS experience."
}
"""

# What the JobAnalysisAgent would have stored in session.state
MOCK_JOB_ANALYSIS = """
{
  "required_skills": [
    "Python", "Go", "PostgreSQL", "Redis", "AWS",
    "Docker", "Kubernetes", "distributed systems",
    "REST APIs", "CI/CD", "GitHub Actions"
  ],
  "preferred_skills": [
    "Kafka", "Terraform", "PCI-DSS compliance",
    "gRPC", "Protocol Buffers", "Datadog"
  ],
  "seniority_level": "senior",
  "keywords": [
    "microservices", "event-driven architecture", "high availability",
    "50000 TPS", "payments", "fintech", "reconciliation",
    "distributed systems", "CAP theorem", "Kubernetes", "Go",
    "Kafka", "Terraform", "PCI-DSS", "gRPC", "Datadog",
    "incident response", "post-mortem", "cross-functional", "TPS"
  ]
}
"""


# ---------------------------------------------------------------------------
# Test runner
# ---------------------------------------------------------------------------

async def run_test():
    print("\n" + "=" * 62)
    print("  Career Copilot - Gap Analysis Agent Test")
    print("=" * 62)

    if not os.getenv("GOOGLE_API_KEY") and os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "false").lower() != "true":
        print("\n[ERROR] GOOGLE_API_KEY not set. Check your .env file.")
        return

    model_name = os.getenv("MODEL_NAME", "gemini-2.0-flash")
    print(f"\n  Model   : {model_name}")

    # --- Setup session ---
    session_service = InMemorySessionService()
    session_id = str(uuid.uuid4())

    # Seed the session state with mock upstream outputs.
    # This is exactly what ResumeAnalysisAgent + JobAnalysisAgent
    # would write via their output_key fields in production.
    await session_service.create_session(
        app_name="career_copilot_test",
        user_id="test_user",
        session_id=session_id,
        state={
            "resume_analysis": MOCK_RESUME_ANALYSIS,
            "job_analysis": MOCK_JOB_ANALYSIS,
        },
    )
    print(f"  Session : {session_id[:8]}...")
    print("\n  [INFO] Session state seeded:")
    print("    - resume_analysis : 4-yr Python backend engineer (Alex Rivera)")
    print("    - job_analysis    : Senior Backend Engineer, Payments (Go+K8s required)")

    runner = Runner(
        agent=gap_agent,
        app_name="career_copilot_test",
        session_service=session_service,
    )

    print("\n[...] Running Gap Analysis Agent...\n")

    # The gap agent reads from session state via {{resume_analysis}} / {{job_analysis}}
    # placeholders in its instruction. We send a minimal trigger message.
    message = types.Content(
        role="user",
        parts=[types.Part(text="Please perform the gap analysis using the resume and job data provided.")],
    )

    final_text = None
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            async for event in runner.run_async(
                user_id="test_user",
                session_id=session_id,
                new_message=message,
            ):
                if hasattr(event, "content") and event.content and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, "text") and part.text:
                            final_text = part.text
            break
        except Exception as e:
            err = str(e)
            if "429" in err or "RESOURCE_EXHAUSTED" in err:
                wait = 65
                if attempt < max_retries:
                    print(f"  [RATE LIMIT] Attempt {attempt}/{max_retries}. Waiting {wait}s...")
                    await asyncio.sleep(wait)
                else:
                    print(f"\n[ERROR] Rate limit hit after {max_retries} attempts.")
                    print("  -> Fix: set MODEL_NAME=gemini-2.0-flash in .env")
                    return
            else:
                raise

    # --- Print & validate ---
    print("=" * 62)
    print("  [OK] Raw Agent Response")
    print("=" * 62)
    print(final_text)

    print("\n" + "=" * 62)
    print("  [RESULT] Parsed & Validated Output")
    print("=" * 62)

    try:
        clean = final_text.strip()
        if clean.startswith("```"):
            clean = "\n".join(clean.split("\n")[1:])
        if clean.endswith("```"):
            clean = "\n".join(clean.split("\n")[:-1])

        parsed = json.loads(clean.strip())

        required_fields = ["match_score", "missing_skills", "missing_keywords", "priority_gaps"]
        missing_fields = [f for f in required_fields if f not in parsed]

        if missing_fields:
            print(f"\n[WARN] Missing fields in response: {missing_fields}")
        else:
            print("\n  [PASS] All 4 required fields present\n")

        # match_score
        score = parsed.get("match_score", "N/A")
        bar = "#" * (score // 5) + "-" * (20 - score // 5) if isinstance(score, int) else ""
        print(f"  match_score      : {score}/100  [{bar}]")

        # missing_skills
        ms = parsed.get("missing_skills", [])
        print(f"\n  missing_skills   ({len(ms)}):")
        for s in ms:
            print(f"    - {s}")

        # missing_keywords
        mk = parsed.get("missing_keywords", [])
        print(f"\n  missing_keywords ({len(mk)}):")
        print(f"    {', '.join(mk)}")

        # priority_gaps
        pg = parsed.get("priority_gaps", [])
        print(f"\n  priority_gaps    ({len(pg)}):")
        for gap in pg:
            priority = gap.get("priority", "?")
            skill    = gap.get("skill", "?")
            reason   = gap.get("reason", "")
            tag = {"HIGH": "[!!!]", "MEDIUM": "[!!] ", "LOW":  "[ !] "}.get(priority, "[?]  ")
            print(f"    {tag} {skill}")
            print(f"           {reason}")

        # Verify session state was saved
        session = await session_service.get_session(
            app_name="career_copilot_test",
            user_id="test_user",
            session_id=session_id,
        )
        saved = session.state.get("gap_analysis")
        print("\n" + "-" * 62)
        if saved:
            print("  [PASS] session.state['gap_analysis'] is set")
            print("         (CareerStrategyAgent and InterviewPrepAgent can now read it)")
        else:
            print("  [WARN] session.state['gap_analysis'] not found")

    except json.JSONDecodeError as e:
        print(f"\n[ERROR] JSON parse error: {e}")
        print("  The agent did not return valid JSON.")

    print("\n" + "=" * 62 + "\n")


if __name__ == "__main__":
    asyncio.run(run_test())
