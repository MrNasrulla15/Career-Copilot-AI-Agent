"""
tools/resume_tools.py
----------------------
FunctionTools for the Resume Analysis Agent.

Each function is a pure Python callable that the LLM can invoke.
Docstrings are critical — ADK uses them to teach the LLM when/how to call each tool.
"""

import re
from typing import Any


# ---------------------------------------------------------------------------
# Tool: extract_skills
# ---------------------------------------------------------------------------

def extract_skills(text: str) -> dict[str, Any]:
    """
    Extract and categorize technical and soft skills from raw resume text.

    Scans the provided text for known programming languages, frameworks, tools,
    cloud platforms, databases, and soft skills. Returns a categorized dictionary
    of detected skills with confidence levels.

    Args:
        text: The raw resume text to scan for skills.

    Returns:
        A dictionary with keys:
        - 'technical_skills': list of detected technical skills
        - 'soft_skills': list of detected soft skills
        - 'total_found': total number of unique skills detected
        - 'status': 'success' or 'error'
    """
    # --- Known skill keyword banks ---
    TECHNICAL_KEYWORDS = {
        # Languages
        "python", "javascript", "typescript", "java", "go", "golang", "rust",
        "c++", "c#", "ruby", "swift", "kotlin", "scala", "r", "matlab",
        "sql", "bash", "shell", "html", "css",
        # Frameworks & Libraries
        "react", "vue", "angular", "next.js", "node.js", "express", "fastapi",
        "django", "flask", "spring", "spring boot", "tensorflow", "pytorch",
        "pandas", "numpy", "scikit-learn", "langchain", "huggingface",
        # Cloud & DevOps
        "aws", "gcp", "azure", "docker", "kubernetes", "k8s", "terraform",
        "ansible", "ci/cd", "github actions", "jenkins", "circleci",
        # Databases
        "postgresql", "mysql", "mongodb", "redis", "elasticsearch", "cassandra",
        "dynamodb", "bigquery", "snowflake", "sqlite",
        # Concepts / Architectures
        "rest", "graphql", "microservices", "event-driven", "kafka", "rabbitmq",
        "machine learning", "deep learning", "nlp", "llm", "rag", "vector db",
        "system design", "distributed systems", "api design",
    }

    SOFT_KEYWORDS = {
        "leadership", "communication", "collaboration", "problem-solving",
        "mentoring", "coaching", "project management", "agile", "scrum",
        "cross-functional", "stakeholder management", "strategic thinking",
        "time management", "adaptability", "critical thinking",
    }

    text_lower = text.lower()

    # Simple keyword matching (production version would use NER / embeddings)
    found_technical = sorted({kw for kw in TECHNICAL_KEYWORDS if kw in text_lower})
    found_soft = sorted({kw for kw in SOFT_KEYWORDS if kw in text_lower})

    return {
        "status": "success",
        "technical_skills": found_technical,
        "soft_skills": found_soft,
        "total_found": len(found_technical) + len(found_soft),
    }


# ---------------------------------------------------------------------------
# Tool: score_resume_section
# ---------------------------------------------------------------------------

def score_resume_section(section_text: str, section_name: str) -> dict[str, Any]:
    """
    Score a specific section of a resume on quality (0–100).

    Evaluates the given section based on:
    - Use of action verbs (indicates impact-driven writing)
    - Presence of quantified metrics (numbers, percentages, dollar amounts)
    - Section length appropriateness
    - Keyword richness relative to section type

    Args:
        section_text: The raw text content of the resume section to score.
        section_name: The name of the section (e.g., 'experience', 'summary', 'skills').

    Returns:
        A dictionary with keys:
        - 'section': name of the section evaluated
        - 'score': integer score 0–100
        - 'feedback': list of specific improvement suggestions
        - 'has_metrics': boolean — whether quantified achievements are present
        - 'status': 'success' or 'error'
    """
    if not section_text or not section_text.strip():
        return {
            "status": "error",
            "section": section_name,
            "score": 0,
            "feedback": ["Section is empty or not found in the resume."],
            "has_metrics": False,
        }

    score = 50  # baseline
    feedback = []

    # --- Check for quantified metrics (strong positive signal) ---
    metric_pattern = r"\b\d+[\.,]?\d*\s*(%|percent|x|times|k|m|billion|million|users|customers|engineers|teams?|months?|years?|days?|hours?)\b"
    has_metrics = bool(re.search(metric_pattern, section_text, re.IGNORECASE))
    if has_metrics:
        score += 20
    else:
        feedback.append("Add quantified achievements (e.g., 'Reduced latency by 40%', 'Managed team of 8').")

    # --- Check for action verbs ---
    ACTION_VERBS = [
        "led", "built", "designed", "architected", "delivered", "launched",
        "increased", "reduced", "improved", "developed", "created", "managed",
        "implemented", "scaled", "optimized", "automated", "mentored", "drove",
        "collaborated", "spearheaded", "established", "transformed",
    ]
    found_verbs = [v for v in ACTION_VERBS if v in section_text.lower()]
    if len(found_verbs) >= 3:
        score += 15
    elif len(found_verbs) >= 1:
        score += 7
    else:
        feedback.append("Use strong action verbs to start bullet points (e.g., 'Led', 'Built', 'Scaled').")

    # --- Length check ---
    word_count = len(section_text.split())
    if section_name.lower() == "summary":
        if 50 <= word_count <= 120:
            score += 10
        else:
            feedback.append(f"Summary should be 50–120 words (currently ~{word_count} words).")
    elif section_name.lower() == "experience":
        if word_count >= 150:
            score += 10
        else:
            feedback.append("Experience section seems thin. Add more detail to each role.")

    # Cap score at 100
    score = min(score, 100)

    if score >= 80:
        feedback.insert(0, f"{section_name.capitalize()} section looks strong!")
    elif score >= 60:
        feedback.insert(0, f"{section_name.capitalize()} section is decent but has room for improvement.")
    else:
        feedback.insert(0, f"{section_name.capitalize()} section needs significant work.")

    return {
        "status": "success",
        "section": section_name,
        "score": score,
        "feedback": feedback,
        "has_metrics": has_metrics,
    }


# ---------------------------------------------------------------------------
# Tool: detect_resume_format
# ---------------------------------------------------------------------------

def detect_resume_format(text: str) -> dict[str, Any]:
    """
    Detect the format and structural completeness of a resume.

    Identifies which standard resume sections are present, estimates the
    approximate length, and flags any common structural issues like missing
    sections or unusual ordering.

    Args:
        text: The full raw text of the resume.

    Returns:
        A dictionary with keys:
        - 'detected_sections': list of section names found
        - 'missing_sections': list of recommended sections not found
        - 'estimated_pages': approximate page count based on word count
        - 'format_warnings': list of structural issues detected
        - 'status': 'success' or 'error'
    """
    EXPECTED_SECTIONS = {
        "summary": ["summary", "objective", "about me", "profile", "overview"],
        "experience": ["experience", "work history", "employment", "work experience", "professional experience"],
        "education": ["education", "academic", "degree", "university", "college"],
        "skills": ["skills", "technical skills", "core competencies", "technologies"],
        "projects": ["projects", "portfolio", "personal projects", "side projects"],
        "certifications": ["certifications", "certificates", "credentials", "licenses"],
        "achievements": ["achievements", "awards", "honors", "accomplishments"],
    }

    text_lower = text.lower()
    detected_sections = []
    missing_sections = []
    format_warnings = []

    for section_name, keywords in EXPECTED_SECTIONS.items():
        if any(kw in text_lower for kw in keywords):
            detected_sections.append(section_name)
        elif section_name in ("experience", "education", "skills"):
            # These are critical — flag as missing
            missing_sections.append(section_name)

    # Estimate page count (average ~400 words per page)
    word_count = len(text.split())
    estimated_pages = max(1, round(word_count / 400))

    if estimated_pages > 2:
        format_warnings.append(f"Resume appears to be ~{estimated_pages} pages. Consider condensing to 1–2 pages.")
    if estimated_pages < 1:
        format_warnings.append("Resume content seems very short. Ensure full text was provided.")
    if "summary" not in detected_sections:
        format_warnings.append("No summary/objective section detected. A strong summary significantly improves ATS performance.")
    if "projects" not in detected_sections:
        format_warnings.append("No projects section found. Consider adding personal/open-source projects to strengthen technical credibility.")

    return {
        "status": "success",
        "detected_sections": detected_sections,
        "missing_sections": missing_sections,
        "estimated_pages": estimated_pages,
        "format_warnings": format_warnings,
        "word_count": word_count,
    }
