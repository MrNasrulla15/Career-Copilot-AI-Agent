"""
tools/job_tools.py
-------------------
FunctionTools for the Job Analysis Agent.

Each function is a pure Python callable that the LLM can invoke.
Docstrings are critical — ADK uses them to teach the LLM when/how to call each tool.
"""

import re
from typing import Any


# ---------------------------------------------------------------------------
# Tool: extract_job_requirements
# ---------------------------------------------------------------------------

def extract_job_requirements(job_text: str) -> dict[str, Any]:
    """
    Extract and categorize requirements from a job description.

    Parses the job description for explicit requirements, separating hard 
    requirements from preferred/bonus qualifications, and extracts experience 
    minimums and education requirements.

    Args:
        job_text: The raw text of the job description.

    Returns:
        A dictionary with keys:
        - 'hard_requirements': list of must-have skills/qualifications
        - 'preferred_requirements': list of nice-to-have skills/qualifications
        - 'min_experience_years': minimum years of experience required (int or None)
        - 'education_requirement': highest education level required (str)
        - 'status': 'success' or 'error'
    """
    text_lower = job_text.lower()
    lines = job_text.split("\n")

    hard_requirements = []
    preferred_requirements = []

    # Heuristic: lines with "required", "must", "need" → hard requirements
    # Lines with "prefer", "nice to have", "plus", "bonus" → preferred
    HARD_SIGNALS = ["required", "must have", "must be", "you will need", "you must", "minimum", "mandatory"]
    PREFERRED_SIGNALS = ["preferred", "nice to have", "plus", "bonus", "ideally", "desirable", "a plus", "advantage"]

    in_hard_section = False
    in_preferred_section = False

    for line in lines:
        line_lower = line.lower().strip()
        if not line_lower:
            continue

        if any(sig in line_lower for sig in HARD_SIGNALS):
            in_hard_section = True
            in_preferred_section = False
        elif any(sig in line_lower for sig in PREFERRED_SIGNALS):
            in_preferred_section = True
            in_hard_section = False

        if line_lower.startswith(("-", "•", "*", "·")) or line_lower[:2].strip().isdigit():
            bullet_text = line.strip().lstrip("-•*·").strip()
            if bullet_text:
                if in_preferred_section:
                    preferred_requirements.append(bullet_text)
                else:
                    hard_requirements.append(bullet_text)

    # Extract minimum years of experience
    exp_pattern = r"(\d+)\+?\s*(?:to\s*\d+)?\s*years?\s*(?:of\s*)?(?:professional\s*)?experience"
    exp_matches = re.findall(exp_pattern, text_lower)
    min_experience_years = int(exp_matches[0]) if exp_matches else None

    # Detect education requirements
    education_requirement = "Not specified"
    if "phd" in text_lower or "doctorate" in text_lower:
        education_requirement = "PhD"
    elif "master" in text_lower or "m.s." in text_lower or "msc" in text_lower:
        education_requirement = "Master's degree"
    elif "bachelor" in text_lower or "b.s." in text_lower or "b.e." in text_lower or "undergraduate" in text_lower:
        education_requirement = "Bachelor's degree"
    elif "degree" in text_lower:
        education_requirement = "Degree (level unspecified)"

    return {
        "status": "success",
        "hard_requirements": hard_requirements[:20],  # cap at 20 for readability
        "preferred_requirements": preferred_requirements[:15],
        "min_experience_years": min_experience_years,
        "education_requirement": education_requirement,
    }


# ---------------------------------------------------------------------------
# Tool: classify_seniority
# ---------------------------------------------------------------------------

def classify_seniority(job_text: str) -> dict[str, Any]:
    """
    Classify the seniority level of a job from the job description text.

    Analyzes both explicit seniority signals (title keywords) and implicit 
    signals (years of experience required, responsibilities described) to 
    produce a normalized seniority label.

    Args:
        job_text: The raw text of the job description.

    Returns:
        A dictionary with keys:
        - 'seniority_level': normalized label (intern / junior / mid / senior / staff / principal / lead / manager / director / vp / c-level)
        - 'confidence': 'high', 'medium', or 'low'
        - 'signals': list of specific text signals that drove the classification
        - 'status': 'success' or 'error'
    """
    text_lower = job_text.lower()
    signals = []
    seniority_level = "mid"  # default
    confidence = "low"

    SENIORITY_MAP = [
        (["intern", "internship", "co-op", "coop"], "intern"),
        (["junior", "jr.", "entry level", "entry-level", "associate", "graduate"], "junior"),
        (["senior", "sr.", "sr "], "senior"),
        (["staff engineer", "staff software"], "staff"),
        (["principal engineer", "principal software", "principal architect"], "principal"),
        (["lead engineer", "tech lead", "technical lead"], "lead"),
        (["engineering manager", "eng manager", "software manager"], "manager"),
        (["director of engineering", "engineering director", "director, engineering"], "director"),
        (["vp of engineering", "vice president of engineering", "head of engineering"], "vp"),
        (["cto", "chief technology", "chief engineer"], "c-level"),
    ]

    for keywords, level in SENIORITY_MAP:
        for kw in keywords:
            if kw in text_lower:
                seniority_level = level
                signals.append(f"Title/text contains '{kw}'")
                confidence = "high"
                break

    # Supplement with experience year signals
    exp_pattern = r"(\d+)\+?\s*(?:to\s*(\d+))?\s*years?"
    matches = re.findall(exp_pattern, text_lower)
    if matches:
        min_years = int(matches[0][0])
        signals.append(f"Requires {min_years}+ years of experience")
        if confidence == "low":
            confidence = "medium"
            if min_years < 2:
                seniority_level = "junior"
            elif min_years < 5:
                seniority_level = "mid"
            elif min_years < 8:
                seniority_level = "senior"
            else:
                seniority_level = "staff"

    return {
        "status": "success",
        "seniority_level": seniority_level,
        "confidence": confidence,
        "signals": signals,
    }


# ---------------------------------------------------------------------------
# Tool: detect_tech_stack
# ---------------------------------------------------------------------------

def detect_tech_stack(job_text: str) -> dict[str, Any]:
    """
    Detect and categorize the technology stack required by a job description.

    Scans the job description for known technologies and categorizes them by
    type: languages, frameworks, databases, cloud, DevOps, AI/ML tools, etc.

    Args:
        job_text: The raw text of the job description.

    Returns:
        A dictionary with keys:
        - 'stack': dict of category → list of detected technologies
        - 'primary_language': the most prominently mentioned programming language (str)
        - 'cloud_provider': detected cloud platform (str or None)
        - 'total_technologies': total unique technologies detected (int)
        - 'status': 'success' or 'error'
    """
    text_lower = job_text.lower()

    TECH_CATEGORIES = {
        "languages": [
            "python", "javascript", "typescript", "java", "go", "golang", "rust",
            "c++", "c#", "ruby", "swift", "kotlin", "scala", "r", "elixir", "php",
        ],
        "frontend": [
            "react", "vue", "angular", "svelte", "next.js", "nuxt", "remix",
            "html", "css", "tailwind", "webpack", "vite",
        ],
        "backend": [
            "node.js", "express", "fastapi", "django", "flask", "spring boot",
            "rails", "gin", "fiber", "nestjs", "graphql", "rest api",
        ],
        "databases": [
            "postgresql", "mysql", "sqlite", "mongodb", "redis", "elasticsearch",
            "cassandra", "dynamodb", "firestore", "bigquery", "snowflake", "supabase",
        ],
        "cloud": [
            "aws", "gcp", "google cloud", "azure", "vercel", "heroku", "fly.io",
            "cloudflare", "lambda", "ec2", "s3", "cloud run",
        ],
        "devops": [
            "docker", "kubernetes", "k8s", "terraform", "ansible", "github actions",
            "jenkins", "circleci", "gitlab ci", "argocd", "helm", "datadog", "grafana",
        ],
        "ai_ml": [
            "tensorflow", "pytorch", "scikit-learn", "huggingface", "langchain",
            "openai", "gemini", "llm", "rag", "vector database", "pinecone",
            "machine learning", "deep learning", "nlp", "mlops", "vertex ai",
        ],
        "mobile": [
            "ios", "android", "react native", "flutter", "swift", "kotlin", "expo",
        ],
        "messaging": [
            "kafka", "rabbitmq", "pubsub", "sqs", "celery", "redis streams",
        ],
    }

    stack = {}
    all_detected = []

    for category, keywords in TECH_CATEGORIES.items():
        found = [kw for kw in keywords if kw in text_lower]
        if found:
            stack[category] = found
            all_detected.extend(found)

    # Identify primary language (most prominent = first mentioned)
    primary_language = None
    for lang in TECH_CATEGORIES["languages"]:
        if lang in text_lower:
            primary_language = lang
            break

    # Identify cloud provider
    cloud_provider = None
    for cloud in ["aws", "gcp", "google cloud", "azure"]:
        if cloud in text_lower:
            cloud_provider = cloud
            break

    return {
        "status": "success",
        "stack": stack,
        "primary_language": primary_language,
        "cloud_provider": cloud_provider,
        "total_technologies": len(set(all_detected)),
    }
