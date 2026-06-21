# -*- coding: utf-8 -*-
"""
test_strategy_agent.py
-----------------------
Standalone test for the Career Strategy Agent.

Pipeline:
    1. Seeds session.state["gap_analysis"] with a mock gap report
       (as if GapAnalysisAgent already ran)
    2. Runs CareerStrategyAgent
    3. Validates all 5 output fields and nested model structures

Usage:
    python test_strategy_agent.py
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

from agents.strategy_agent import strategy_agent


# ---------------------------------------------------------------------------
# Mock gap_analysis (what GapAnalysisAgent would have produced)
# ---------------------------------------------------------------------------

MOCK_GAP_ANALYSIS = """
{
  "match_score": 57,
  "missing_skills": [
    "Go", "Kubernetes", "distributed systems", "gRPC", "Kafka", "Terraform"
  ],
  "missing_keywords": [
    "microservices", "event-driven architecture", "high availability",
    "TPS", "payments", "fintech", "reconciliation", "CAP theorem",
    "PCI-DSS", "Datadog", "Protocol Buffers", "incident response"
  ],
  "priority_gaps": [
    {
      "skill": "Go",
      "priority": "HIGH",
      "reason": "Go is explicitly required in the job description and used for core payment services; candidate only has Python experience."
    },
    {
      "skill": "Kubernetes",
      "priority": "HIGH",
      "reason": "Kubernetes is a hard requirement for managing payment microservices at scale; not present in the candidate's resume."
    },
    {
      "skill": "distributed systems",
      "priority": "HIGH",
      "reason": "The role requires handling 50,000+ TPS with high availability; deep distributed systems knowledge is essential."
    },
    {
      "skill": "Kafka",
      "priority": "MEDIUM",
      "reason": "Listed as preferred for event-driven payment processing; important for the fintech domain."
    },
    {
      "skill": "Terraform",
      "priority": "MEDIUM",
      "reason": "Listed as preferred for infrastructure-as-code; increasingly expected for senior backend engineers."
    },
    {
      "skill": "gRPC",
      "priority": "LOW",
      "reason": "Listed as preferred; can be learned quickly given existing REST API experience."
    }
  ]
}
"""


# ---------------------------------------------------------------------------
# Test runner
# ---------------------------------------------------------------------------

async def run_test():
    print("\n" + "=" * 65)
    print("  Career Copilot - Career Strategy Agent Test")
    print("=" * 65)

    if not os.getenv("GOOGLE_API_KEY") and os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "false").lower() != "true":
        print("\n[ERROR] GOOGLE_API_KEY not set. Check your .env file.")
        return

    model_name = os.getenv("MODEL_NAME", "gemini-2.0-flash")
    print(f"\n  Model   : {model_name}")

    # --- Setup session with mock gap_analysis in state ---
    session_service = InMemorySessionService()
    session_id = str(uuid.uuid4())

    await session_service.create_session(
        app_name="career_copilot_test",
        user_id="test_user",
        session_id=session_id,
        state={"gap_analysis": MOCK_GAP_ANALYSIS},
    )

    print(f"  Session : {session_id[:8]}...")
    print("\n  [INFO] Session state seeded:")
    print("    - gap_analysis : match_score=57, 3x HIGH gaps (Go, K8s, distributed systems)")

    runner = Runner(
        agent=strategy_agent,
        app_name="career_copilot_test",
        session_service=session_service,
    )

    print("\n[...] Running Career Strategy Agent...\n")

    message = types.Content(
        role="user",
        parts=[types.Part(text="Please generate the career strategy based on the gap analysis provided.")],
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
                    print("  -> Quota exhausted for today. Try again tomorrow or enable billing.")
                    return
            else:
                raise

    print("=" * 65)
    print("  [OK] Raw Agent Response")
    print("=" * 65)
    print(final_text)

    print("\n" + "=" * 65)
    print("  [RESULT] Parsed & Validated Output")
    print("=" * 65)

    try:
        clean = final_text.strip()
        if clean.startswith("```"):
            clean = "\n".join(clean.split("\n")[1:])
        if clean.endswith("```"):
            clean = "\n".join(clean.split("\n")[:-1])

        parsed = json.loads(clean.strip())

        required_fields = [
            "plan_30_day", "plan_60_day", "plan_90_day",
            "recommended_projects", "learning_priorities"
        ]
        missing_fields = [f for f in required_fields if f not in parsed]

        if missing_fields:
            print(f"\n[WARN] Missing fields: {missing_fields}")
        else:
            print("\n  [PASS] All 5 required fields present\n")

        # --- 30-day plan ---
        p30 = parsed.get("plan_30_day", [])
        print(f"  plan_30_day ({len(p30)} items):")
        for i, item in enumerate(p30, 1):
            print(f"    {i}. {item}")

        # --- 60-day plan ---
        p60 = parsed.get("plan_60_day", [])
        print(f"\n  plan_60_day ({len(p60)} items):")
        for i, item in enumerate(p60, 1):
            print(f"    {i}. {item}")

        # --- 90-day plan ---
        p90 = parsed.get("plan_90_day", [])
        print(f"\n  plan_90_day ({len(p90)} items):")
        for i, item in enumerate(p90, 1):
            print(f"    {i}. {item}")

        # --- Recommended projects ---
        projects = parsed.get("recommended_projects", [])
        print(f"\n  recommended_projects ({len(projects)}):")
        for p in projects:
            print(f"\n    [{p.get('duration', '?')}] {p.get('title', '?')}")
            print(f"      {p.get('description', '')}")
            skills = ", ".join(p.get("skills_covered", []))
            print(f"      Skills: {skills}")

        # --- Learning priorities ---
        priorities = parsed.get("learning_priorities", [])
        print(f"\n  learning_priorities ({len(priorities)}):")
        print(f"  {'SKILL':<22} {'PRIORITY':<10} {'TIMEFRAME':<15} RESOURCE")
        print(f"  {'-'*22} {'-'*10} {'-'*15} {'-'*30}")
        for lp in priorities:
            skill     = lp.get("skill", "?")[:20]
            priority  = lp.get("priority", "?")
            timeframe = lp.get("timeframe", "?")[:13]
            resource  = lp.get("resource", "?")[:50]
            print(f"  {skill:<22} {priority:<10} {timeframe:<15} {resource}")

        # --- Verify session state ---
        session = await session_service.get_session(
            app_name="career_copilot_test",
            user_id="test_user",
            session_id=session_id,
        )
        saved = session.state.get("career_strategy")
        print("\n" + "-" * 65)
        if saved:
            print("  [PASS] session.state['career_strategy'] is set")
            print("         (InterviewPrepAgent and Coordinator can now read it)")
        else:
            print("  [WARN] session.state['career_strategy'] not found")

    except json.JSONDecodeError as e:
        print(f"\n[ERROR] JSON parse error: {e}")
        print("  The agent did not return valid JSON.")

    print("\n" + "=" * 65 + "\n")


if __name__ == "__main__":
    asyncio.run(run_test())
