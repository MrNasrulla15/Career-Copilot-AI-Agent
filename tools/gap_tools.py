"""
tools/gap_tools.py
-------------------
FunctionTools for the Gap Analysis Agent.

These tools operate on structured data extracted by the Resume and Job agents
and stored in the shared session state. They compute overlap, prioritize gaps,
and estimate remediation effort.
"""

from typing import Any


# ---------------------------------------------------------------------------
# Tool: compute_skill_overlap
# ---------------------------------------------------------------------------

def compute_skill_overlap(
    candidate_skills: list[str],
    required_skills: list[str],
    preferred_skills: list[str] | None = None,
) -> dict[str, Any]:
    """
    Compute the overlap between a candidate's skills and a job's requirements.

    Calculates matched skills, critical gaps, and optional gaps. Returns a 
    quantitative match score (0–100) based on weighted coverage of required 
    vs. preferred skills.

    Args:
        candidate_skills: List of skills extracted from the candidate's resume.
        required_skills: List of hard-required skills from the job description.
        preferred_skills: Optional list of nice-to-have skills from the job.

    Returns:
        A dictionary with keys:
        - 'matched_skills': skills candidate has that the job requires
        - 'critical_gaps': required skills the candidate is missing
        - 'preferred_gaps': preferred skills the candidate is missing
        - 'bonus_skills': candidate skills not required but potentially valuable
        - 'match_score': integer 0–100 (required skills carry 80% weight)
        - 'status': 'success' or 'error'
    """
    if not candidate_skills or not required_skills:
        return {
            "status": "error",
            "error_message": "Both candidate_skills and required_skills must be non-empty lists.",
        }

    preferred_skills = preferred_skills or []

    # Normalize to lowercase for comparison
    candidate_set = {s.lower().strip() for s in candidate_skills}
    required_set = {s.lower().strip() for s in required_skills}
    preferred_set = {s.lower().strip() for s in preferred_skills}

    matched_skills = sorted(candidate_set & required_set)
    critical_gaps = sorted(required_set - candidate_set)
    preferred_gaps = sorted(preferred_set - candidate_set)
    bonus_skills = sorted(candidate_set - required_set - preferred_set)

    # Weighted match score: required skills = 80%, preferred = 20%
    required_coverage = len(matched_skills) / len(required_set) if required_set else 0
    preferred_matched = len(preferred_set & candidate_set)
    preferred_coverage = preferred_matched / len(preferred_set) if preferred_set else 1.0

    match_score = round((required_coverage * 80) + (preferred_coverage * 20))

    return {
        "status": "success",
        "matched_skills": matched_skills,
        "critical_gaps": critical_gaps,
        "preferred_gaps": preferred_gaps,
        "bonus_skills": bonus_skills,
        "match_score": match_score,
        "required_coverage_pct": round(required_coverage * 100, 1),
        "preferred_coverage_pct": round(preferred_coverage * 100, 1),
    }


# ---------------------------------------------------------------------------
# Tool: prioritize_gaps
# ---------------------------------------------------------------------------

def prioritize_gaps(
    critical_gaps: list[str],
    preferred_gaps: list[str],
    job_title: str = "",
) -> dict[str, Any]:
    """
    Prioritize identified skill gaps by impact level (HIGH / MEDIUM / LOW).

    Uses the type of gap (required vs. preferred), the job title context, and
    heuristics about skill learnability to assign priority levels and 
    recommended urgency for each gap.

    Args:
        critical_gaps: List of hard-required skills the candidate is missing.
        preferred_gaps: List of preferred skills the candidate is missing.
        job_title: The target job title (used to weight domain-critical skills).

    Returns:
        A dictionary with keys:
        - 'high_priority': gaps that are likely to disqualify the candidate
        - 'medium_priority': gaps that need addressing but aren't disqualifying
        - 'low_priority': gaps that are nice-to-have or easy to learn
        - 'total_gaps': total number of gaps across all priority levels
        - 'status': 'success' or 'error'
    """
    # Skills that are typically harder/slower to demonstrate (high weight)
    HARD_SKILLS = {
        "system design", "distributed systems", "machine learning", "deep learning",
        "kubernetes", "terraform", "rust", "scala", "c++", "leadership",
        "architecture", "security", "compliance",
    }

    # Skills that are learnable quickly with a project or tutorial
    QUICK_LEARN = {
        "docker", "git", "sql", "rest api", "graphql", "html", "css",
        "bash", "linux", "agile", "scrum", "swagger",
    }

    high_priority = []
    medium_priority = []
    low_priority = []

    for gap in critical_gaps:
        gap_lower = gap.lower()
        # Critical gaps are at least MEDIUM; hard ones are HIGH
        if any(hard in gap_lower for hard in HARD_SKILLS):
            high_priority.append(gap)
        elif any(quick in gap_lower for quick in QUICK_LEARN):
            low_priority.append(gap)
        else:
            medium_priority.append(gap)

    for gap in preferred_gaps:
        gap_lower = gap.lower()
        # Preferred gaps are mostly LOW; but complex ones become MEDIUM
        if any(hard in gap_lower for hard in HARD_SKILLS):
            medium_priority.append(gap)
        else:
            low_priority.append(gap)

    return {
        "status": "success",
        "high_priority": high_priority,
        "medium_priority": medium_priority,
        "low_priority": low_priority,
        "total_gaps": len(high_priority) + len(medium_priority) + len(low_priority),
    }


# ---------------------------------------------------------------------------
# Tool: estimate_learning_time
# ---------------------------------------------------------------------------

def estimate_learning_time(skills: list[str]) -> dict[str, Any]:
    """
    Estimate the time required to learn or demonstrate proficiency in each skill.

    Uses heuristics based on skill complexity and typical learning curves to
    provide realistic time estimates and recommend the best learning modality.

    Args:
        skills: List of skill names to estimate learning time for.

    Returns:
        A dictionary with keys:
        - 'estimates': list of dicts, each with 'skill', 'time_estimate', 'learning_mode'
        - 'total_min_weeks': minimum total weeks if learning all skills sequentially
        - 'status': 'success' or 'error'
    """
    # Heuristic time buckets (in weeks) and recommended learning modes
    SKILL_TIME_MAP = {
        # Quick wins (1–2 weeks)
        "docker": (2, "Tutorial + hands-on project"),
        "git": (1, "Interactive tutorial (e.g., Learn Git Branching)"),
        "sql": (2, "Mode Analytics / SQLZoo course"),
        "html": (1, "MDN Web Docs + small project"),
        "css": (2, "CSS Tricks + build a landing page"),
        "bash": (2, "Linux command line course on Udemy"),
        "rest api": (1, "Build a simple REST API"),
        "graphql": (2, "How to GraphQL tutorial"),
        "agile": (1, "Coursera Agile Fundamentals"),
        "scrum": (1, "Scrum.org free resources"),
        # Medium investments (3–8 weeks)
        "react": (6, "React official docs + build a full project"),
        "node.js": (4, "Node.js full course on YouTube"),
        "fastapi": (3, "FastAPI official tutorial"),
        "django": (6, "Django for Beginners book"),
        "postgresql": (4, "PostgreSQL Tutorial + PgExercises"),
        "mongodb": (3, "MongoDB University free courses"),
        "redis": (3, "Redis University free courses"),
        "typescript": (4, "TypeScript Handbook + refactor a project"),
        "terraform": (5, "HashiCorp Learn platform"),
        "kubernetes": (8, "Kubernetes The Hard Way or CKA prep"),
        "aws": (8, "AWS Solutions Architect – Associate course"),
        "gcp": (8, "Google Cloud Associate course on Coursera"),
        "azure": (8, "Microsoft Learn paths"),
        # Longer investments (3–6 months)
        "machine learning": (16, "fast.ai or Andrew Ng's ML Specialization"),
        "deep learning": (20, "fast.ai Deep Learning for Coders"),
        "system design": (12, "Designing Data-Intensive Applications book + practice"),
        "rust": (16, "The Rust Programming Language book"),
        "scala": (12, "Functional Programming in Scala course"),
        "c++": (20, "C++ Primer book + competitive programming"),
        "distributed systems": (20, "MIT 6.824 Distributed Systems lectures"),
        "security": (12, "OWASP resources + TryHackMe/HackTheBox"),
        "nlp": (16, "Hugging Face NLP course"),
        "leadership": (12, "The Manager's Path book + mentoring practice"),
    }

    DEFAULT_ESTIMATE = (4, "Search for a dedicated online course or book")

    estimates = []
    total_min_weeks = 0

    for skill in skills:
        skill_lower = skill.lower().strip()
        weeks, mode = DEFAULT_ESTIMATE

        # Try exact match first, then partial
        if skill_lower in SKILL_TIME_MAP:
            weeks, mode = SKILL_TIME_MAP[skill_lower]
        else:
            for key, val in SKILL_TIME_MAP.items():
                if key in skill_lower or skill_lower in key:
                    weeks, mode = val
                    break

        time_label = f"{weeks} week{'s' if weeks != 1 else ''}" if weeks < 12 else f"~{weeks // 4} months"
        estimates.append({
            "skill": skill,
            "time_estimate": time_label,
            "learning_mode": mode,
        })
        total_min_weeks += weeks

    return {
        "status": "success",
        "estimates": estimates,
        "total_min_weeks": total_min_weeks,
        "total_sequential_estimate": f"~{total_min_weeks // 4} months (sequential learning)",
        "note": "Time estimates assume ~10–15 hours/week of focused study.",
    }
