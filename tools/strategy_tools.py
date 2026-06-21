"""
tools/strategy_tools.py
------------------------
FunctionTools for the Career Strategy Agent.

These tools generate structured, time-boxed action plans and resource
recommendations based on gap analysis results.
"""

from typing import Any


# ---------------------------------------------------------------------------
# Tool: generate_action_items
# ---------------------------------------------------------------------------

def generate_action_items(
    high_priority_gaps: list[str],
    medium_priority_gaps: list[str],
    low_priority_gaps: list[str],
    job_title: str = "",
) -> dict[str, Any]:
    """
    Generate a structured 30/60/90-day action plan based on prioritized skill gaps.

    Maps HIGH-priority gaps to immediate (30-day) actions, MEDIUM-priority to
    the 60-day phase, and LOW-priority to the 90-day phase. Also generates
    non-skill actions such as networking and application strategy.

    Args:
        high_priority_gaps: Skills that are critical blockers (will disqualify if absent).
        medium_priority_gaps: Important but not immediately disqualifying gaps.
        low_priority_gaps: Nice-to-have gaps to address longer term.
        job_title: The target job title (used to customize action items).

    Returns:
        A dictionary with keys:
        - 'day_30_actions': list of immediate action items
        - 'day_60_actions': list of mid-term action items
        - 'day_90_actions': list of long-term action items
        - 'status': 'success' or 'error'
    """
    day_30 = []
    day_60 = []
    day_90 = []

    # High priority → Day 30 (immediate)
    for gap in high_priority_gaps[:5]:  # focus on top 5
        day_30.append(f"Start learning '{gap}' — identify a course and complete the first module this week.")

    # Universal Day 30 actions
    day_30.extend([
        "Rewrite resume summary to target this specific role and seniority level.",
        "Update LinkedIn headline, about section, and skills to match job requirements.",
        "Identify 5–10 target companies and research their engineering culture.",
        f"Find 3 people currently in '{job_title or 'this type of role'}' and send warm outreach messages.",
        "Set up a job tracker (Notion, spreadsheet) to manage applications systematically.",
    ])

    # Medium priority → Day 60
    for gap in medium_priority_gaps[:4]:
        day_60.append(f"Complete a hands-on project demonstrating '{gap}' and add it to your portfolio/GitHub.")

    day_60.extend([
        "Start applying to target roles (aim for 5–10 quality applications per week).",
        "Schedule 2–3 informational interviews with professionals in target companies.",
        "Complete at least 1 mock technical interview (via Pramp, interviewing.io, or peer).",
        "Request 2 LinkedIn recommendations from past colleagues or managers.",
    ])

    # Low priority → Day 90
    for gap in low_priority_gaps[:3]:
        day_90.append(f"Build familiarity with '{gap}' through side reading or small experiments.")

    day_90.extend([
        "Contribute to an open-source project relevant to the target tech stack.",
        "Write a technical blog post or LinkedIn article showcasing your expertise.",
        "Prepare salary negotiation research: document your target range and rationale.",
        "Revisit and iterate on your application strategy based on feedback from interviews.",
    ])

    return {
        "status": "success",
        "day_30_actions": day_30,
        "day_60_actions": day_60,
        "day_90_actions": day_90,
    }


# ---------------------------------------------------------------------------
# Tool: recommend_resources
# ---------------------------------------------------------------------------

def recommend_resources(skills: list[str], budget: str = "mixed") -> dict[str, Any]:
    """
    Recommend specific learning resources for a list of skills.

    Returns curated, specific resources (courses, books, platforms) for each
    skill, categorized by free vs. paid, with estimated time and platform.

    Args:
        skills: List of skills to find learning resources for.
        budget: 'free', 'paid', or 'mixed' (default). Controls which resources appear.

    Returns:
        A dictionary with keys:
        - 'resources': list of resource dicts, each with skill, name, url_hint, cost, time
        - 'free_count': number of free resources found
        - 'paid_count': number of paid resources found
        - 'status': 'success' or 'error'
    """
    RESOURCE_DB = {
        "python": [
            {"name": "Python for Everybody – Coursera", "url_hint": "coursera.org/specializations/python", "cost": "free_audit", "time": "2 months"},
            {"name": "Real Python tutorials", "url_hint": "realpython.com", "cost": "free_partial", "time": "ongoing"},
        ],
        "react": [
            {"name": "React official docs (react.dev)", "url_hint": "react.dev/learn", "cost": "free", "time": "2–3 weeks"},
            {"name": "Epic React by Kent C. Dodds", "url_hint": "epicreact.dev", "cost": "paid", "time": "6–8 weeks"},
        ],
        "system design": [
            {"name": "Designing Data-Intensive Applications (book)", "url_hint": "dataintensive.net", "cost": "paid", "time": "3–4 months"},
            {"name": "System Design Primer – GitHub", "url_hint": "github.com/donnemartin/system-design-primer", "cost": "free", "time": "1–2 months"},
        ],
        "kubernetes": [
            {"name": "Kubernetes the Hard Way – GitHub", "url_hint": "github.com/kelseyhightower/kubernetes-the-hard-way", "cost": "free", "time": "2–3 weeks"},
            {"name": "CKA (Certified Kubernetes Admin) prep – Udemy", "url_hint": "udemy.com/course/certified-kubernetes-administrator", "cost": "paid", "time": "6–8 weeks"},
        ],
        "machine learning": [
            {"name": "Machine Learning Specialization – Coursera (Andrew Ng)", "url_hint": "coursera.org/specializations/machine-learning-introduction", "cost": "free_audit", "time": "3 months"},
            {"name": "fast.ai Practical Deep Learning", "url_hint": "fast.ai", "cost": "free", "time": "3–4 months"},
        ],
        "aws": [
            {"name": "AWS Certified Solutions Architect – A Cloud Guru", "url_hint": "acloudguru.com", "cost": "paid", "time": "2 months"},
            {"name": "AWS Skill Builder (free tier)", "url_hint": "skillbuilder.aws", "cost": "free_partial", "time": "ongoing"},
        ],
        "sql": [
            {"name": "Mode SQL Tutorial", "url_hint": "mode.com/sql-tutorial", "cost": "free", "time": "1–2 weeks"},
            {"name": "SQLZoo", "url_hint": "sqlzoo.net", "cost": "free", "time": "1 week"},
        ],
        "docker": [
            {"name": "Docker official Get Started guide", "url_hint": "docs.docker.com/get-started", "cost": "free", "time": "1 week"},
            {"name": "Docker & Kubernetes – Udemy (Stephan Grider)", "url_hint": "udemy.com/course/docker-and-kubernetes-the-complete-guide", "cost": "paid", "time": "3–4 weeks"},
        ],
        "typescript": [
            {"name": "TypeScript Handbook (official)", "url_hint": "typescriptlang.org/docs/handbook", "cost": "free", "time": "2 weeks"},
            {"name": "Execute Program – TypeScript course", "url_hint": "executeprogram.com/courses/typescript", "cost": "paid", "time": "3–4 weeks"},
        ],
        "leadership": [
            {"name": "The Manager's Path (Camille Fournier)", "url_hint": "amazon.com — O'Reilly book", "cost": "paid", "time": "3–4 weeks reading"},
            {"name": "Managing Humans (Michael Lopp)", "url_hint": "managinghumans.com", "cost": "paid", "time": "2 weeks reading"},
        ],
        "nlp": [
            {"name": "Hugging Face NLP Course (free)", "url_hint": "huggingface.co/learn/nlp-course", "cost": "free", "time": "6–8 weeks"},
        ],
        "default": [
            {"name": "Udemy (search for the skill)", "url_hint": "udemy.com", "cost": "paid", "time": "varies"},
            {"name": "YouTube (free tutorials)", "url_hint": "youtube.com", "cost": "free", "time": "varies"},
            {"name": "O'Reilly Learning (book/video)", "url_hint": "oreilly.com", "cost": "paid", "time": "varies"},
        ],
    }

    resources = []
    free_count = 0
    paid_count = 0

    for skill in skills:
        skill_lower = skill.lower().strip()
        skill_resources = RESOURCE_DB.get(skill_lower) or RESOURCE_DB.get("default")

        for r in skill_resources[:2]:  # max 2 resources per skill
            cost = r.get("cost", "unknown")
            include = True
            if budget == "free" and cost not in ("free", "free_audit", "free_partial"):
                include = False
            elif budget == "paid" and cost == "free":
                include = False

            if include:
                resources.append({
                    "skill": skill,
                    "resource_name": r["name"],
                    "where_to_find": r["url_hint"],
                    "cost": cost.replace("_", " "),
                    "estimated_time": r["time"],
                })
                if "free" in cost:
                    free_count += 1
                else:
                    paid_count += 1

    return {
        "status": "success",
        "resources": resources,
        "free_count": free_count,
        "paid_count": paid_count,
        "total": len(resources),
    }


# ---------------------------------------------------------------------------
# Tool: build_timeline
# ---------------------------------------------------------------------------

def build_timeline(
    action_items_30: list[str],
    action_items_60: list[str],
    action_items_90: list[str],
    start_date_hint: str = "today",
) -> dict[str, Any]:
    """
    Build a structured, week-by-week timeline from the 30/60/90-day action items.

    Distributes action items across weekly milestones and creates a phased plan
    with clear weekly goals and checkpoints.

    Args:
        action_items_30: List of Day-30 action items.
        action_items_60: List of Day-60 action items.
        action_items_90: List of Day-90 action items.
        start_date_hint: When the candidate intends to start (informational).

    Returns:
        A dictionary with keys:
        - 'phases': list of phase dicts (weeks 1–4, 5–8, 9–12)
        - 'total_weeks': 12
        - 'milestones': key milestones at weeks 4, 8, and 12
        - 'status': 'success' or 'error'
    """
    def chunk_items(items: list[str], num_weeks: int) -> list[dict]:
        """Distribute items roughly evenly across weeks."""
        weeks = []
        items_per_week = max(1, len(items) // num_weeks)
        for i in range(num_weeks):
            start = i * items_per_week
            end = start + items_per_week if i < num_weeks - 1 else len(items)
            week_items = items[start:end]
            weeks.append({
                "week": i + 1,
                "focus_items": week_items,
            })
        return weeks

    phases = [
        {
            "phase": "Phase 1: Foundation (Weeks 1–4)",
            "goal": "Close critical gaps, optimize application materials, begin networking.",
            "weeks": chunk_items(action_items_30, 4),
        },
        {
            "phase": "Phase 2: Momentum (Weeks 5–8)",
            "goal": "Build visible evidence of skills, start applying, mock interviews.",
            "weeks": chunk_items(action_items_60, 4),
        },
        {
            "phase": "Phase 3: Polish & Position (Weeks 9–12)",
            "goal": "Finalize application pipeline, negotiate, handle long-term gaps.",
            "weeks": chunk_items(action_items_90, 4),
        },
    ]

    milestones = {
        "week_4_checkpoint": "Resume & LinkedIn fully updated. At least 1 critical gap started. First networking messages sent.",
        "week_8_checkpoint": "5–10 applications submitted. 1+ mock interview completed. Portfolio project shipped.",
        "week_12_checkpoint": "In active interview pipeline. Salary research done. Long-term learning plan established.",
    }

    return {
        "status": "success",
        "start_date_hint": start_date_hint,
        "phases": phases,
        "total_weeks": 12,
        "milestones": milestones,
    }
