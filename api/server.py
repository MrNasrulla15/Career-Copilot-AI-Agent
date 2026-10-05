# -*- coding: utf-8 -*-
"""
api/server.py
--------------
Career Copilot — FastAPI backend server.

Serves the frontend as static files and exposes one endpoint:
  POST /api/analyze  — runs the full ADK pipeline and returns structured JSON

Pipeline (runs agents individually to control per-agent input):
  1. ResumeAnalysisAgent  (input: extracted resume text)
  2. JobAnalysisAgent     (input: job description text)
  3. GapAnalysisAgent     (reads session state: resume_analysis + job_analysis)
  4. CareerStrategyAgent  (reads session state: gap_analysis)
  5. InterviewPrepAgent   (reads session state: resume_analysis + job_analysis)

Run:
    uvicorn api.server:app --reload --port 8000

Then open: http://localhost:8000
"""

import json
import os
import re
import sys
import tempfile
import time
import uuid
from collections import defaultdict
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, File, Form, Header, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from agents.resume_agent import resume_agent
from agents.job_agent import job_agent
from agents.gap_agent import gap_agent
from agents.strategy_agent import strategy_agent
from agents.interview_agent import interview_agent


# ---------------------------------------------------------------------------
# App setup & Security Hardening
# ---------------------------------------------------------------------------

DEBUG = os.getenv("DEBUG", "false").lower() == "true"
app = FastAPI(
    title="Career Copilot API",
    version="1.0.0",
    docs_url="/docs" if DEBUG else None,
    redoc_url="/redoc" if DEBUG else None,
)

# 1. CORS Hardening
raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000")
allowed_origins = [o.strip() for o in raw_origins.split(",") if o.strip()]
if "*" in allowed_origins and not DEBUG:
    allowed_origins = ["http://localhost:8000", "http://127.0.0.1:8000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    allow_credentials=True,
)

# 2. Security Headers & Rate Limiting Middleware
RATE_LIMIT = int(os.getenv("RATE_LIMIT_PER_MINUTE", "10"))
rate_limit_records = defaultdict(list)

@app.middleware("http")
async def security_and_rate_limit_middleware(request: Request, call_next):
    # Rate limiting for API requests
    if request.url.path.startswith("/api/"):
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        # Filter requests from last 60 seconds
        window_starts = now - 60
        rate_limit_records[client_ip] = [t for t in rate_limit_records[client_ip] if t > window_starts]
        
        if len(rate_limit_records[client_ip]) >= RATE_LIMIT:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please slow down and try again in a minute."}
            )
        rate_limit_records[client_ip].append(now)

    response = await call_next(request)
    
    # OWASP Security Headers
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: blob:; "
        "connect-src 'self';"
    )
    return response


APP_NAME = "career_copilot_api"
USER_ID  = "api_user"


# ---------------------------------------------------------------------------
# Input Sanitization & Document Validation Helpers
# ---------------------------------------------------------------------------

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB limit

def sanitize_text(text: str) -> str:
    """Sanitize user text input to strip control characters and malicious scripts."""
    if not text:
        return ""
    # Strip HTML/script tags
    clean = re.sub(r'<[^>]*>', '', text)
    # Remove null bytes and non-printable control characters
    clean = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', clean)
    return clean.strip()


def extract_text_from_upload(file_bytes: bytes, filename: str) -> str:
    """Sanitize filename, validate file headers, and extract text from PDF or DOCX."""
    # Prevent Path Traversal attacks
    safe_filename = Path(filename).name
    ext = Path(safe_filename).suffix.lower()

    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File size exceeds maximum allowed limit of 10MB.")

    if ext == ".pdf":
        # Validate PDF Magic Bytes (%PDF)
        if not file_bytes.startswith(b"%PDF"):
            raise HTTPException(status_code=422, detail="Invalid PDF file header.")
        try:
            import fitz
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp.write(file_bytes)
                tmp_path = tmp.name
            doc = fitz.open(tmp_path)
            pages = []
            for i, page in enumerate(doc, 1):
                text = page.get_text("text").strip()
                if text:
                    pages.append(text)
            doc.close()
            os.unlink(tmp_path)
            return sanitize_text("\n\n".join(pages))
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"PDF text extraction failed: {e}")

    elif ext in (".docx", ".doc"):
        # Validate PK ZIP magic header for DOCX
        if ext == ".docx" and not file_bytes.startswith(b"PK\x03\x04"):
            raise HTTPException(status_code=422, detail="Invalid DOCX document header.")
        try:
            import docx
            import io
            doc = docx.Document(io.BytesIO(file_bytes))
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            return sanitize_text("\n".join(paragraphs))
        except HTTPException:
            raise
        except ImportError:
            raise HTTPException(status_code=422, detail="python-docx library not installed.")
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"DOCX extraction failed: {e}")

    else:
        try:
            return sanitize_text(file_bytes.decode("utf-8", errors="replace"))
        except Exception:
            raise HTTPException(status_code=422, detail=f"Unsupported file type extension: {ext}")


# ---------------------------------------------------------------------------
# ADK pipeline runner
# ---------------------------------------------------------------------------

async def run_agent_step(
    runner: Runner,
    session_id: str,
    message_text: str,
) -> None:
    """Run a single agent step, consuming all events, with retries for transient errors."""
    import asyncio
    import logging
    
    message = types.Content(
        role="user",
        parts=[types.Part(text=message_text)],
    )
    
    max_retries = 6
    base_delay = 4.0  # seconds
    
    for attempt in range(max_retries):
        try:
            async for _ in runner.run_async(
                user_id=USER_ID,
                session_id=session_id,
                new_message=message,
            ):
                pass
            return  # Success!
        except Exception as e:
            err_msg = str(e)
            is_transient = any(
                code in err_msg
                for code in ["503", "UNAVAILABLE", "429", "RESOURCE_EXHAUSTED", "500", "504"]
            )
            if is_transient and attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                logging.warning(
                    f"Transient error running agent {runner.agent.name}: {err_msg}. "
                    f"Retrying in {delay:.1f}s (Attempt {attempt + 1}/{max_retries})..."
                )
                await asyncio.sleep(delay)
            else:
                raise e


async def run_pipeline(resume_text: str, job_description: str) -> dict:
    """
    Run all 5 specialist agents with parallelization where independent.
    Returns the raw session state dict after all agents complete.
    """
    import asyncio

    session_service = InMemorySessionService()
    session_id = str(uuid.uuid4())

    await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=session_id,
    )

    # 1. Run Resume Analysis and Job Analysis concurrently
    runner_resume = Runner(agent=resume_agent, app_name=APP_NAME, session_service=session_service)
    runner_job = Runner(agent=job_agent, app_name=APP_NAME, session_service=session_service)

    await asyncio.gather(
        run_agent_step(runner_resume, session_id, resume_text),
        run_agent_step(runner_job, session_id, job_description)
    )

    # 2. Run Gap Analysis (followed by Career Strategy) concurrently with Interview Prep
    runner_gap = Runner(agent=gap_agent, app_name=APP_NAME, session_service=session_service)
    runner_strat = Runner(agent=strategy_agent, app_name=APP_NAME, session_service=session_service)
    runner_interview = Runner(agent=interview_agent, app_name=APP_NAME, session_service=session_service)

    async def run_gap_and_strategy():
        await run_agent_step(runner_gap, session_id, "Perform gap analysis using the resume and job data in session state.")
        await run_agent_step(runner_strat, session_id, "Generate a career strategy from the gap analysis in session state.")

    await asyncio.gather(
        run_gap_and_strategy(),
        run_agent_step(runner_interview, session_id, "Generate an interview preparation kit from the resume and job data in session state.")
    )

    session = await session_service.get_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=session_id,
    )
    return dict(session.state)


# ---------------------------------------------------------------------------
# Response builders
# ---------------------------------------------------------------------------

def _parse(value) -> dict:
    """Parse a session state value (str or dict) into a dict."""
    if not value:
        return {}
    if isinstance(value, str):
        try:
            return json.loads(value)
        except Exception:
            return {}
    if isinstance(value, dict):
        return value
    return {}


def _score_label(score: int) -> str:
    if score >= 80: return "Excellent Match"
    if score >= 65: return "Good Match"
    if score >= 50: return "Moderate Match"
    if score >= 35: return "Weak Match"
    return "Poor Match"


def _score_color(score: int) -> str:
    if score >= 70: return "success"
    if score >= 45: return "warning"
    return "danger"


def build_response(state: dict) -> dict:
    resume  = _parse(state.get("resume_analysis"))
    job     = _parse(state.get("job_analysis"))
    gap     = _parse(state.get("gap_analysis"))
    strat   = _parse(state.get("career_strategy"))
    prep    = _parse(state.get("interview_prep"))

    # --- Resume Review: derive strengths + weaknesses + suggestions ---
    strengths = []
    exp = resume.get("total_experience_years", 0)
    if exp >= 5:
        strengths.append(f"{exp} years of professional experience")
    elif exp >= 2:
        strengths.append(f"{exp} years of professional experience")

    job_required = {s.lower() for s in job.get("required_skills", [])}
    matched = [s for s in resume.get("technical_skills", []) if s.lower() in job_required]
    for s in matched[:5]:
        strengths.append(f"Proficient in {s} (required skill)")

    certs = resume.get("certifications", [])
    if certs:
        strengths.append(f"Holds {len(certs)} certification(s): {', '.join(certs[:2])}")

    edu = resume.get("education", "")
    if edu and edu != "Not provided":
        strengths.append(f"Education: {edu}")

    weaknesses = []
    for pg in gap.get("priority_gaps", []):
        if pg.get("priority") == "HIGH":
            reason = pg.get("reason", "")
            weaknesses.append(f"Missing {pg.get('skill','')}: {reason}")

    score = gap.get("match_score", 0)
    if score < 50:
        weaknesses.append(f"Overall fit score is {score}/100 — address HIGH-priority gaps before applying.")

    suggestions = []
    for lp in strat.get("learning_priorities", [])[:5]:
        sk = lp.get("skill","")
        rs = lp.get("resource","")
        tf = lp.get("timeframe","")
        if sk:
            suggestions.append(f"Learn {sk} in ~{tf} — {rs}" if tf else f"Learn {sk}: {rs}")

    # --- Interview Prep ---
    all_questions = prep.get("interview_questions", [])
    technical_qs  = [q["question"] for q in all_questions if q.get("category") == "technical"]
    behavioral_qs = [q["question"] for q in all_questions if q.get("category") == "behavioral"]
    sysdesign_qs  = [q["question"] for q in all_questions if q.get("category") == "system_design"]
    prep_areas    = [
        {"area": pa.get("area",""), "why": pa.get("why_important",""), "actions": pa.get("action_items",[])}
        for pa in prep.get("preparation_areas", [])
    ]
    answers = [
        {
            "question":   sa.get("question",""),
            "framework":  sa.get("answer_framework",""),
            "key_points": sa.get("key_points",[]),
        }
        for sa in prep.get("suggested_answers", [])[:3]
    ]

    return {
        "candidate_name": resume.get("candidate_name", ""),
        "current_title":  resume.get("current_title", ""),

        "resume_review": {
            "strengths":   strengths  or ["Strong technical background identified."],
            "weaknesses":  weaknesses or ["Some gaps exist (see Skill Gaps section)."],
            "suggestions": suggestions,
        },

        "match_score": {
            "score": score,
            "label": _score_label(score),
            "color": _score_color(score),
        },

        "skill_gaps": {
            "missing_skills":    gap.get("missing_skills", []),
            "missing_keywords":  gap.get("missing_keywords", []),
            "priority_gaps":     gap.get("priority_gaps", []),
        },

        "career_roadmap": {
            "immediate":  strat.get("plan_30_day", []),
            "mid_term":   strat.get("plan_60_day", []),
            "long_term":  strat.get("plan_90_day", []),
            "projects":   [
                {
                    "title":    p.get("title",""),
                    "desc":     p.get("description",""),
                    "skills":   p.get("skills_covered",[]),
                    "duration": p.get("duration",""),
                }
                for p in strat.get("recommended_projects",[])
            ],
        },

        "interview_prep": {
            "technical_questions":     technical_qs[:6],
            "behavioral_questions":    behavioral_qs[:5],
            "system_design_questions": sysdesign_qs[:3],
            "preparation_areas":       prep_areas,
            "suggested_answers":       answers,
        },
    }


# ---------------------------------------------------------------------------
# API endpoints
# ---------------------------------------------------------------------------

@app.post("/api/analyze")
async def analyze(
    resume_file: UploadFile = File(...),
    job_description: str    = Form(...),
    x_api_key: str | None   = Header(None, alias="X-API-Key"),
) -> JSONResponse:
    """
    Run the Career Copilot analysis pipeline.

    Accepts:
        resume_file     — PDF or DOCX upload
        job_description — plain text job description
        x_api_key       — optional client authentication key header
    """
    # 1. Authenticate API Key if configured in environment
    required_key = os.getenv("APP_API_KEY", "").strip()
    if required_key:
        if not x_api_key or x_api_key != required_key:
            raise HTTPException(status_code=401, detail="Unauthorized: Invalid or missing X-API-Key header.")

    # 2. Sanitize and validate inputs
    clean_jd = sanitize_text(job_description)
    if not clean_jd:
        raise HTTPException(status_code=400, detail="Job description text is required.")

    file_bytes = await resume_file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Resume file is empty.")

    # Extract resume text safely
    resume_text = extract_text_from_upload(file_bytes, resume_file.filename or "resume.pdf")

    if not resume_text.strip():
        raise HTTPException(status_code=422, detail="Could not extract readable text from resume. Ensure it is a text-based PDF or DOCX.")

    # Run the ADK pipeline
    try:
        state = await run_pipeline(resume_text, clean_jd)
    except Exception as e:
        err = str(e)
        if "429" in err or "RESOURCE_EXHAUSTED" in err:
            raise HTTPException(
                status_code=429,
                detail="API quota exhausted. Please wait for reset or update quota settings.",
            )
        # Avoid leaking internal exception tracebacks in production mode
        detail_msg = err if DEBUG else "An internal server error occurred while processing the pipeline."
        raise HTTPException(status_code=500, detail=f"Pipeline processing error: {detail_msg}")

    # Build and return response
    try:
        result = build_response(state)
    except Exception as e:
        detail_msg = str(e) if DEBUG else "An error occurred while building the report."
        raise HTTPException(status_code=500, detail=f"Response formatting error: {detail_msg}")

    return JSONResponse(content={"success": True, "data": result})


@app.get("/api/health")
async def health():
    """Health check endpoint."""
    model = os.getenv("MODEL_NAME", "gemini-2.0-flash")
    api_key = os.getenv("GOOGLE_API_KEY", "")
    api_key_configured = bool(api_key) and api_key not in ("your_api_key_here", "your_gemini_api_key_here")
    return {"status": "ok", "model": model, "api_key_configured": api_key_configured}


# ---------------------------------------------------------------------------
# Serve frontend static files
# ---------------------------------------------------------------------------

FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
