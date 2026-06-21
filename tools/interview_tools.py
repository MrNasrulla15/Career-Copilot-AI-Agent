"""
tools/interview_tools.py
-------------------------
FunctionTools for the Interview Preparation Agent.

These tools generate tailored interview questions, STAR-format answers,
and structured cheat sheets based on the candidate's profile and target role.
"""

from typing import Any


# ---------------------------------------------------------------------------
# Tool: generate_interview_questions
# ---------------------------------------------------------------------------

def generate_interview_questions(
    job_title: str,
    tech_stack: list[str],
    seniority_level: str = "mid",
) -> dict[str, Any]:
    """
    Generate a curated list of likely interview questions for a given role.

    Produces questions across multiple categories: technical (language/framework
    specific), system design, behavioral, and culture fit. Questions are tailored
    to the seniority level and technology stack of the target role.

    Args:
        job_title: The title of the target role (e.g., 'Senior Backend Engineer').
        tech_stack: List of key technologies in the job's stack (e.g., ['Python', 'AWS', 'Kafka']).
        seniority_level: One of: intern, junior, mid, senior, staff, principal, lead, manager.

    Returns:
        A dictionary with keys:
        - 'technical_questions': list of technical question dicts (question, difficulty, concepts)
        - 'behavioral_questions': list of behavioral questions
        - 'system_design_questions': list of system design prompts (for senior+)
        - 'culture_questions': list of culture/values questions
        - 'total_questions': total question count
        - 'status': 'success' or 'error'
    """
    tech_stack_lower = [t.lower() for t in tech_stack]

    # --- Core behavioral questions (universal) ---
    behavioral_questions = [
        "Tell me about a time you disagreed with a technical decision. How did you handle it?",
        "Describe a project where you had to learn a new technology under a tight deadline.",
        "Tell me about the most complex technical problem you've solved. Walk me through your approach.",
        "Describe a time you had to deal with ambiguity. How did you structure your approach?",
        "Tell me about a time you made a mistake that impacted production. What did you do?",
        "How do you prioritize when you have multiple competing deadlines?",
        "Describe a time you mentored someone or were mentored effectively.",
        "Tell me about a successful cross-functional collaboration. What made it work?",
    ]

    # Add seniority-specific behavioral questions
    if seniority_level in ("senior", "staff", "principal", "lead", "manager"):
        behavioral_questions.extend([
            "Tell me about a time you influenced technical direction without formal authority.",
            "Describe how you've driven adoption of a new engineering practice across a team.",
            "Tell me about a time you made a significant architectural decision. What trade-offs did you consider?",
        ])

    # --- Technical questions ---
    technical_questions = [
        {
            "question": "Explain the difference between concurrency and parallelism.",
            "difficulty": "medium",
            "concepts": ["threading", "async", "performance"],
        },
        {
            "question": "How would you design a scalable REST API? What considerations do you have?",
            "difficulty": "medium",
            "concepts": ["API design", "REST", "scalability"],
        },
        {
            "question": "Walk me through how you'd debug a latency spike in a production service.",
            "difficulty": "hard",
            "concepts": ["observability", "profiling", "distributed tracing"],
        },
        {
            "question": "What is the difference between SQL and NoSQL databases? When would you use each?",
            "difficulty": "easy",
            "concepts": ["databases", "data modeling", "trade-offs"],
        },
    ]

    # Stack-specific questions
    if "python" in tech_stack_lower:
        technical_questions.append({
            "question": "Explain Python's GIL. How does it affect concurrency in Python applications?",
            "difficulty": "medium",
            "concepts": ["Python internals", "threading", "async"],
        })
        technical_questions.append({
            "question": "What are Python generators and when would you use them over a list?",
            "difficulty": "easy",
            "concepts": ["memory efficiency", "iterators", "lazy evaluation"],
        })

    if "javascript" in tech_stack_lower or "typescript" in tech_stack_lower:
        technical_questions.append({
            "question": "Explain the JavaScript event loop. How does it handle async operations?",
            "difficulty": "medium",
            "concepts": ["event loop", "promises", "async/await"],
        })

    if "react" in tech_stack_lower:
        technical_questions.append({
            "question": "Explain React's reconciliation algorithm. What is the virtual DOM?",
            "difficulty": "medium",
            "concepts": ["React internals", "rendering", "performance"],
        })

    if "kubernetes" in tech_stack_lower or "k8s" in tech_stack_lower:
        technical_questions.append({
            "question": "Explain the difference between a Deployment and a StatefulSet in Kubernetes.",
            "difficulty": "medium",
            "concepts": ["Kubernetes", "orchestration", "stateful apps"],
        })

    if "machine learning" in tech_stack_lower or "ml" in tech_stack_lower:
        technical_questions.append({
            "question": "Explain the bias-variance tradeoff. How do you address overfitting?",
            "difficulty": "medium",
            "concepts": ["ML fundamentals", "regularization", "model evaluation"],
        })

    if "aws" in tech_stack_lower or "gcp" in tech_stack_lower or "azure" in tech_stack_lower:
        technical_questions.append({
            "question": f"Walk me through how you'd architect a highly available web application on {'AWS' if 'aws' in tech_stack_lower else 'GCP'}.",
            "difficulty": "hard",
            "concepts": ["cloud architecture", "HA", "disaster recovery"],
        })

    # --- System design (senior+) ---
    system_design_questions = []
    if seniority_level in ("senior", "staff", "principal", "lead", "manager"):
        system_design_questions = [
            f"Design a URL shortener (like bit.ly). Scale it to handle 10M requests/day.",
            f"Design a notification system that sends emails, SMS, and push notifications.",
            f"Design a rate limiter for a public API. What algorithms would you consider?",
        ]
        if "kafka" in tech_stack_lower or "rabbitmq" in tech_stack_lower:
            system_design_questions.append(
                "Design an event-driven order processing system using message queues."
            )

    # --- Culture/values questions ---
    culture_questions = [
        "What does a great engineering culture look like to you?",
        "How do you stay up-to-date with technology trends?",
        "What does your ideal development workflow look like?",
        "How do you balance shipping fast with maintaining code quality?",
    ]

    return {
        "status": "success",
        "technical_questions": technical_questions,
        "behavioral_questions": behavioral_questions,
        "system_design_questions": system_design_questions,
        "culture_questions": culture_questions,
        "total_questions": (
            len(technical_questions)
            + len(behavioral_questions)
            + len(system_design_questions)
            + len(culture_questions)
        ),
    }


# ---------------------------------------------------------------------------
# Tool: draft_star_answer
# ---------------------------------------------------------------------------

def draft_star_answer(
    question: str,
    candidate_experience_summary: str,
    target_skill: str = "",
) -> dict[str, Any]:
    """
    Draft a STAR-method answer framework for a behavioral interview question.

    Uses the candidate's experience summary and target skill to create a
    structured answer template with specific guidance for each STAR component.
    The candidate fills in their own specific details.

    Args:
        question: The behavioral interview question to answer.
        candidate_experience_summary: A brief summary of the candidate's background
            (e.g., 'Senior Python engineer with 6 years experience in fintech, led 3-person team').
        target_skill: The competency this question is designed to probe (e.g., 'leadership').

    Returns:
        A dictionary with keys:
        - 'question': the original question
        - 'target_competency': what the interviewer is assessing
        - 'star_framework': dict with Situation, Task, Action, Result guidance
        - 'tips': list of specific tips for this question type
        - 'status': 'success' or 'error'
    """
    # Map common question types to competencies
    COMPETENCY_SIGNALS = {
        "disagreed": "constructive conflict / influence",
        "mistake": "accountability / growth mindset",
        "deadline": "time management / prioritization",
        "ambiguity": "autonomy / structured thinking",
        "mentor": "leadership / knowledge sharing",
        "complex": "technical depth / problem-solving",
        "cross-functional": "collaboration / communication",
        "prioritize": "prioritization / stakeholder management",
        "failure": "resilience / accountability",
        "influence": "leadership without authority",
    }

    question_lower = question.lower()
    detected_competency = target_skill or "general professional competency"
    for signal, competency in COMPETENCY_SIGNALS.items():
        if signal in question_lower:
            detected_competency = competency
            break

    star_framework = {
        "Situation": (
            f"Set the scene concisely. Describe the context at {candidate_experience_summary.split(',')[0] if candidate_experience_summary else 'your previous role'}. "
            "Include: team size, project stage, business context. Keep to 2–3 sentences."
        ),
        "Task": (
            "Clarify YOUR specific responsibility. What were YOU asked to do or what problem fell to you to solve? "
            "Be specific about your role vs. the team's role."
        ),
        "Action": (
            "This is the heart of the answer. Describe the specific steps YOU took. Use 'I' not 'we'. "
            "Explain your reasoning and decision-making process. Cover 3–5 concrete actions."
        ),
        "Result": (
            "End with a measurable, positive outcome. Include numbers where possible "
            "(e.g., 'reduced build time by 35%', 'team velocity increased 2x', 'shipped 3 weeks early'). "
            "Also mention what you learned from the experience."
        ),
    }

    tips = [
        f"This question tests: {detected_competency}.",
        "Keep the full answer to 2–3 minutes when spoken aloud.",
        "Practice the Situation and Task sections — candidates often spend too long here.",
        "The Action section should take 50–60% of your total answer time.",
        "Always end with a positive result, even if the situation was difficult.",
        "Have a follow-up detail ready in case the interviewer asks 'what would you do differently?'",
    ]

    return {
        "status": "success",
        "question": question,
        "target_competency": detected_competency,
        "star_framework": star_framework,
        "tips": tips,
    }


# ---------------------------------------------------------------------------
# Tool: create_cheat_sheet
# ---------------------------------------------------------------------------

def create_cheat_sheet(
    top_strengths: list[str],
    key_gaps: list[str],
    key_stories: list[str],
    target_salary_range: str = "research required",
    job_title: str = "",
) -> dict[str, Any]:
    """
    Create a one-page interview cheat sheet summarizing key talking points.

    Synthesizes the candidate's strengths, gap mitigation strategies, best 
    stories to tell, and salary negotiation guidance into a compact reference 
    card to review before any interview.

    Args:
        top_strengths: List of 3–5 key strengths to emphasize in every interview.
        key_gaps: List of top 2–3 gaps to address proactively.
        key_stories: List of 2–4 signature stories/examples with brief descriptions.
        target_salary_range: Candidate's researched salary expectation (e.g., '$140K–$160K').
        job_title: The target job title.

    Returns:
        A dictionary with keys:
        - 'strengths_to_emphasize': formatted list of strengths with talking point hints
        - 'gaps_to_address': how to proactively frame each gap
        - 'stories_bank': formatted story references for behavioral answers
        - 'salary_guidance': negotiation talking points
        - 'pre_interview_checklist': quick checklist for the day of the interview
        - 'status': 'success' or 'error'
    """
    # Format strengths with talking point hints
    strengths_with_hints = [
        {"strength": s, "talking_point": f"Weave '{s}' into technical and behavioral answers naturally."}
        for s in top_strengths
    ]

    # Frame gaps positively
    gap_framings = []
    for gap in key_gaps:
        gap_framings.append({
            "gap": gap,
            "how_to_address": (
                f"If asked about '{gap}', acknowledge it honestly and immediately pivot: "
                f"'I haven't worked with {gap} professionally yet, but I've been actively learning it — "
                f"[describe what you've done]. I pick up new technologies quickly, as I demonstrated when...'"
            ),
        })

    # Format stories bank
    formatted_stories = []
    for i, story in enumerate(key_stories, 1):
        formatted_stories.append({
            "story_id": f"Story {i}",
            "description": story,
            "use_for": "Behavioral questions about impact, leadership, problem-solving",
        })

    # Salary guidance
    salary_guidance = {
        "target_range": target_salary_range,
        "negotiation_tips": [
            "Never give the first number — deflect with 'I'm flexible, what's the budgeted range for this role?'",
            "If pressed, give a range where your target is the lower bound.",
            "Consider total comp: base + equity + bonus + benefits.",
            "Use competing offers (real or pending) as leverage if available.",
            f"Research: levels.fyi, Glassdoor, LinkedIn Salary for '{job_title or 'this role'}' in your market.",
        ],
    }

    # Pre-interview checklist
    pre_interview_checklist = [
        "✅ Re-read the job description and company's engineering blog/careers page.",
        "✅ Review your top 3 strengths and practice weaving them naturally into answers.",
        "✅ Rehearse 1–2 STAR stories out loud (time yourself — aim for 2–3 minutes each).",
        "✅ Prepare 5+ questions to ask the interviewer.",
        "✅ Check your tech setup if virtual: camera, mic, background, internet.",
        "✅ Have water nearby.",
        "✅ Arrive 10–15 min early (or log in 5 min early for virtual).",
        "✅ Bring copies of your resume if in-person.",
        "✅ Review the interviewer's LinkedIn profile if you know who it is.",
    ]

    return {
        "status": "success",
        "strengths_to_emphasize": strengths_with_hints,
        "gaps_to_address": gap_framings,
        "stories_bank": formatted_stories,
        "salary_guidance": salary_guidance,
        "pre_interview_checklist": pre_interview_checklist,
    }
