# -*- coding: utf-8 -*-
"""
main.py
--------
Career Copilot — CLI entry point.

Runs an interactive conversation with the CareerCopilotCoordinator pipeline.
Paste your resume text and job description when prompted.

Usage:
    python main.py

Environment variables (see .env.example):
    GOOGLE_API_KEY           -- your Google AI Studio API key
    MODEL_NAME               -- model override (default: gemini-2.0-flash)
    GOOGLE_GENAI_USE_VERTEXAI -- set "true" to use Vertex AI
"""

import asyncio
import os
import sys
import uuid

from dotenv import load_dotenv
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

load_dotenv()

# Force UTF-8 output on Windows to avoid cp1252 encoding errors
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from agents.coordinator import coordinator_agent
from tools.pdf_parser import extract_text_from_pdf


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

APP_NAME = "career_copilot"
USER_ID  = "local_user"


# ---------------------------------------------------------------------------
# Session + Runner
# ---------------------------------------------------------------------------

async def create_runner() -> tuple[Runner, str]:
    """Set up an in-memory ADK session and wire the coordinator agent."""
    session_service = InMemorySessionService()
    session_id = str(uuid.uuid4())

    await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=session_id,
    )

    runner = Runner(
        agent=coordinator_agent,
        app_name=APP_NAME,
        session_service=session_service,
    )

    return runner, session_id


# ---------------------------------------------------------------------------
# Response extraction
# ---------------------------------------------------------------------------

async def get_final_response(runner: Runner, session_id: str, user_input: str) -> str:
    """
    Send a message to the coordinator pipeline and collect the final
    text response from the synthesizer agent at the end of the sequence.
    """
    message = types.Content(
        role="user",
        parts=[types.Part(text=user_input)],
    )

    final_response = ""
    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=session_id,
        new_message=message,
    ):
        if hasattr(event, "content") and event.content and event.content.parts:
            for part in event.content.parts:
                if hasattr(part, "text") and part.text:
                    final_response = part.text  # last text wins

    return final_response or "[No response generated]"


# ---------------------------------------------------------------------------
# Interactive CLI
# ---------------------------------------------------------------------------

async def run_session(runner: Runner, session_id: str) -> None:
    """
    Interactive CLI loop. Accepts multi-line input (terminate with DONE)
    and streams the final Career Intelligence Report to stdout.
    """
    sep = "=" * 70

    print(f"\n{sep}")
    print("  Career Copilot -- Powered by Google ADK + Gemini")
    print(sep)
    print("  Paste your resume and/or job description, then type DONE.")
    print("  The pipeline will run all 5 specialist agents automatically.")
    print("  Type 'quit' or 'exit' to end the session.")
    print(f"{sep}\n")

    turn = 0

    while True:
        turn += 1
        model = os.getenv("MODEL_NAME", "gemini-2.0-flash")
        print(f"[Turn {turn}] ({model}) -- Paste input, then type DONE on a new line:")

        lines = []
        while True:
            try:
                line = input()
            except EOFError:
                break

            if line.strip().lower() in ("quit", "exit"):
                print("\nGoodbye! Good luck with your career journey.")
                return

            if line.strip().upper() == "DONE":
                break

            lines.append(line)

        user_input = "\n".join(lines).strip()

        if not user_input:
            print("  [!] No input received. Please paste your resume, job description,")
            print("      or a path to a PDF file (e.g. C:/Users/name/resume.pdf).\n")
            continue

        # --- PDF auto-detection ---
        # If the user pastes a single line ending in .pdf, parse it automatically.
        if user_input.strip().lower().endswith(".pdf") and "\n" not in user_input.strip():
            pdf_path = user_input.strip()
            print(f"\n[PDF] Detected PDF path: {pdf_path}")
            print("[PDF] Extracting text...")
            try:
                user_input = extract_text_from_pdf(pdf_path)
                import os as _os
                page_count = user_input.count("[Page ")
                print(f"[PDF] Extracted {page_count} page(s) successfully. Sending to pipeline.\n")
            except Exception as e:
                print(f"[PDF ERROR] {e}")
                print("  Tip: Make sure the file path is correct and the PDF is text-based.\n")
                continue

        print(f"\n[Career Copilot] Running pipeline (this may take 30-60s)...\n")
        print("-" * 70)

        try:
            response = await get_final_response(runner, session_id, user_input)
            print(response)
        except Exception as e:
            err = str(e)
            if "429" in err or "RESOURCE_EXHAUSTED" in err:
                print("[ERROR] API quota exhausted. Wait for quota reset or enable billing.")
                print("  -> https://ai.dev/rate-limit")
            else:
                print(f"[ERROR] {type(e).__name__}: {e}")

        print("\n" + "-" * 70)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def main() -> None:
    api_key   = os.getenv("GOOGLE_API_KEY")
    use_vertex = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "false").lower() == "true"

    if not api_key and not use_vertex:
        print("\n[ERROR] GOOGLE_API_KEY is not set.")
        print("  Create a .env file from .env.example and add your API key.")
        print("  Get a free key at: https://aistudio.google.com/app/apikey\n")
        return

    runner, session_id = await create_runner()
    print(f"  Session: {session_id[:8]}...")

    await run_session(runner, session_id)


if __name__ == "__main__":
    asyncio.run(main())
