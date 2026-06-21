# -*- coding: utf-8 -*-
"""
test_job_agent.py
------------------
Standalone test for the Job Analysis Agent.

Runs the agent against a realistic sample job description and prints
the structured JSON output to verify all four fields are populated correctly.

Usage:
    python test_job_agent.py
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

# Import the agent under test
from agents.job_agent import job_agent


# ---------------------------------------------------------------------------
# Sample job description (realistic Senior Backend Engineer role)
# ---------------------------------------------------------------------------

SAMPLE_JOB_DESCRIPTION = """
Senior Backend Engineer — Payments Platform
Acme Fintech, Inc. | Remote (US) | Full-time

About the Role:
We're looking for a Senior Backend Engineer to join our Payments Platform team.
You'll design, build, and scale the core financial infrastructure that processes
over $2B in transactions annually. This is a high-ownership role — you'll architect
new systems, mentor junior engineers, and collaborate directly with product and
data teams.

What You'll Do:
- Design and implement scalable microservices for payment processing and reconciliation
- Own the reliability and performance of services handling 50,000+ TPS
- Lead technical design reviews and contribute to architecture decisions
- Mentor 2–3 junior engineers and conduct code reviews
- Partner with product managers and data engineers on cross-functional initiatives
- Drive incident response and post-mortems for production issues

Required Qualifications:
- 6+ years of professional software engineering experience
- Strong proficiency in Python or Go (we use both)
- Deep experience with PostgreSQL and Redis
- Experience designing and building RESTful APIs and event-driven systems
- Hands-on experience with AWS (EC2, RDS, SQS, Lambda)
- Proficiency with Docker and Kubernetes
- Strong understanding of distributed systems concepts (CAP theorem, consistency models)
- Experience with CI/CD pipelines (GitHub Actions or similar)

Preferred Qualifications:
- Experience in the payments or fintech domain
- Familiarity with Kafka or other message streaming platforms
- Knowledge of PCI-DSS compliance requirements
- Experience with Terraform or other IaC tools
- Contributions to open-source projects

Our Stack:
Python, Go, PostgreSQL, Redis, Kafka, AWS, Kubernetes, Docker, Terraform,
GitHub Actions, Datadog, gRPC, Protocol Buffers

Compensation:
$160,000 – $200,000 base + equity + benefits
"""


# ---------------------------------------------------------------------------
# Test runner
# ---------------------------------------------------------------------------

async def run_test():
    print("\n" + "=" * 60)
    print("  Career Copilot - Job Analysis Agent Test")
    print("=" * 60)

    # Validate API key
    if not os.getenv("GOOGLE_API_KEY") and not os.getenv("GOOGLE_GENAI_USE_VERTEXAI"):
        print("\n❌  GOOGLE_API_KEY not set. Check your .env file.")
        return

    # Setup session
    session_service = InMemorySessionService()
    session_id = str(uuid.uuid4())
    await session_service.create_session(
        app_name="career_copilot_test",
        user_id="test_user",
        session_id=session_id,
    )

    runner = Runner(
        agent=job_agent,
        app_name="career_copilot_test",
        session_service=session_service,
    )

    print("\n[INPUT] Sample Senior Backend Engineer JD (Fintech)")
    print("-" * 60)
    model_name = os.getenv('MODEL_NAME', 'gemini-2.0-flash')
    print(f"  Model  : {model_name}")
    print(f"  Session: {session_id[:8]}...")
    print("\n[...] Running Job Analysis Agent...\n")

    message = types.Content(
        role="user",
        parts=[types.Part(text=SAMPLE_JOB_DESCRIPTION)],
    )

    # Collect all events and find the final response
    # Retry up to 3 times on 429 rate-limit errors (free tier quota)
    final_text = None
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            async for event in runner.run_async(
                user_id="test_user",
                session_id=session_id,
                new_message=message,
            ):
                # ADK streams multiple events; we want the final text response
                if hasattr(event, "content") and event.content and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, "text") and part.text:
                            final_text = part.text
            break  # success — exit retry loop
        except Exception as e:
            err = str(e)
            if "429" in err or "RESOURCE_EXHAUSTED" in err:
                wait = 65  # free tier retry delay is ~58s; use 65s to be safe
                if attempt < max_retries:
                    print(f"  [RATE LIMIT] Attempt {attempt}/{max_retries} hit quota. Waiting {wait}s before retry...")
                    await asyncio.sleep(wait)
                else:
                    print(f"\n[ERROR] Rate limit hit after {max_retries} attempts.")
                    print("  -> gemini-2.5-flash free tier: 20 req/day")
                    print("  -> Fix: set MODEL_NAME=gemini-2.0-flash in .env (1500 req/day free)")
                    print("  -> Or wait until your daily quota resets.")
                    return
            else:
                raise

    print("=" * 60)
    print("  [OK] Raw Agent Response")
    print("=" * 60)
    print(final_text)

    # --- Validate and pretty-print the JSON ---
    print("\n" + "=" * 60)
    print("  [RESULT] Parsed & Validated Output")
    print("=" * 60)

    try:
        # Strip markdown fences if the model included them
        clean = final_text.strip()
        if clean.startswith("```"):
            clean = "\n".join(clean.split("\n")[1:])
        if clean.endswith("```"):
            clean = "\n".join(clean.split("\n")[:-1])

        parsed = json.loads(clean.strip())

        # Validate all four required fields are present
        required_fields = ["required_skills", "preferred_skills", "seniority_level", "keywords"]
        missing = [f for f in required_fields if f not in parsed]

        if missing:
            print(f"\n⚠️  Missing fields: {missing}")
        else:
            print("\n  [PASS] All 4 fields present\n")

        print(f"  seniority_level  : {parsed.get('seniority_level', 'N/A')}")
        print(f"\n  required_skills  ({len(parsed.get('required_skills', []))}):")
        for s in parsed.get("required_skills", []):
            print(f"    - {s}")
        print(f"\n  preferred_skills ({len(parsed.get('preferred_skills', []))}):")
        for s in parsed.get("preferred_skills", []):
            print(f"    - {s}")
        print(f"\n  keywords         ({len(parsed.get('keywords', []))}):")
        print(f"    {', '.join(parsed.get('keywords', []))}")

        # Also verify it's saved in session state
        session = await session_service.get_session(
            app_name="career_copilot_test",
            user_id="test_user",
            session_id=session_id,
        )
        state_value = session.state.get("job_analysis")
        print("\n" + "-" * 60)
        if state_value:
            print("  [PASS] session.state['job_analysis'] is set (downstream agents can read it)")
        else:
            print("  [WARN] session.state['job_analysis'] not found")

    except json.JSONDecodeError as e:
        print(f"\n[ERROR] JSON parse error: {e}")
        print("    The agent did not return valid JSON. Check the prompt/schema.")

    print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(run_test())
