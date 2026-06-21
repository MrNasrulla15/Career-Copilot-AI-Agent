"""
agents/coordinator.py
----------------------
Career Copilot Coordinator — the root orchestrator of the multi-agent system.

Architecture: SequentialAgent (7 steps)
-----------------------------------------
Step 0: DocumentProcessorAgent  — MCP-powered PDF parsing + section detection
Step 1: ResumeAnalysisAgent     — structured candidate profile extraction
Step 2: JobAnalysisAgent        — structured job requirements extraction
Step 3: GapAnalysisAgent        — skill gap scoring (reads steps 1+2)
Step 4: CareerStrategyAgent     — 30/60/90-day action plan (reads step 3)
Step 5: InterviewPrepAgent      — interview kit (reads steps 1+2)
Step 6: CareerCopilotSynthesizer — Final Career Intelligence Report (reads all)

MCP Integration:
    The DocumentProcessorAgent connects to the career-copilot MCP server
    (mcp_server/server.py) via stdio transport using ADK's McpToolset.
    It exposes two tools:
        - extract_resume_text(file_path)   -> plain text from PDF
        - parse_resume_sections(text)      -> structured section dict JSON

    The MCP server is spawned as a subprocess at agent startup and
    communicates over stdin/stdout. McpToolset manages the lifecycle.

Why SequentialAgent?
    All specialist agents use output_schema (constrained JSON generation),
    which is mutually exclusive with tool calling in ADK. SequentialAgent
    is the correct ADK primitive for a fixed, ordered pipeline with
    automatic session state handoff between steps.
"""

import os
import sys
from pathlib import Path

from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
from mcp.client.stdio import StdioServerParameters
try:
    from google.adk.tools.mcp_tool.mcp_toolset import StdioConnectionParams
except ImportError:
    StdioConnectionParams = None  # fallback for older ADK versions

from prompts import COORDINATOR_INSTRUCTION, DOCUMENT_PROCESSOR_INSTRUCTION
from agents.resume_agent import resume_agent
from agents.job_agent import job_agent
from agents.gap_agent import gap_agent
from agents.strategy_agent import strategy_agent
from agents.interview_agent import interview_agent


# ---------------------------------------------------------------------------
# Step 0 — Document Processor Agent (MCP-powered)
# ---------------------------------------------------------------------------
# Connects to the MCP server subprocess and exposes its two tools to the LLM.
# Handles PDF input: if the user message contains a .pdf path, this agent
# calls extract_resume_text + parse_resume_sections and stores the result
# in session.state["raw_resume_text"] for ResumeAnalysisAgent to use.
#
# Also transparently passes through plain-text resumes if no PDF is detected.
# ---------------------------------------------------------------------------

# Path to the MCP server entry point
_MCP_SERVER_SCRIPT = str(
    Path(__file__).resolve().parent.parent / "mcp_server" / "server.py"
)

_document_processor_agent = LlmAgent(
    name="DocumentProcessorAgent",

    model=os.getenv("MODEL_NAME", "gemini-2.0-flash"),

    description=(
        "Handles document input preprocessing. If the user provides a PDF file "
        "path, uses MCP tools to extract text and parse resume sections. "
        "If the user provides plain text, passes it through unchanged. "
        "Stores the processed resume text in session state for the pipeline."
    ),

    instruction=DOCUMENT_PROCESSOR_INSTRUCTION,

    # MCP toolset — spawns mcp_server/server.py as a subprocess via stdio.
    # ADK's McpToolset manages the subprocess lifecycle automatically.
    tools=[
        McpToolset(
            connection_params=StdioServerParameters(
                command=sys.executable,
                args=[_MCP_SERVER_SCRIPT],
                env={
                    "PYTHONPATH": str(Path(_MCP_SERVER_SCRIPT).parent.parent),
                    **{k: v for k, v in os.environ.items()},
                },
            ),
            tool_filter=["extract_resume_text", "parse_resume_sections"],
        )
    ],

    # Saves processed resume text to session state for ResumeAnalysisAgent
    output_key="raw_resume_text",
)


# ---------------------------------------------------------------------------
# Step 6 — Synthesis Agent
# ---------------------------------------------------------------------------
# Reads all five specialist outputs from session state and produces the
# final Career Intelligence Report. No output_schema — speaks freely to user.
# ---------------------------------------------------------------------------

_synthesis_agent = LlmAgent(
    name="CareerCopilotSynthesizer",

    model=os.getenv("MODEL_NAME", "gemini-2.0-flash"),

    description=(
        "Reads all specialist agent outputs from session state and synthesizes "
        "them into a final, cohesive Career Intelligence Report for the user."
    ),

    instruction=COORDINATOR_INSTRUCTION,
)


# ---------------------------------------------------------------------------
# Root Coordinator — SequentialAgent (7 steps)
# ---------------------------------------------------------------------------

coordinator_agent = SequentialAgent(
    name="CareerCopilotCoordinator",

    description=(
        "Root Career Copilot orchestrator. Accepts resume (PDF or text) and "
        "job description, then runs a 7-agent pipeline: document parsing, "
        "resume analysis, job analysis, gap scoring, career strategy, "
        "interview prep, and final report synthesis."
    ),

    sub_agents=[
        _document_processor_agent,  # Step 0: PDF/text -> session["raw_resume_text"]
        resume_agent,               # Step 1: profile  -> session["resume_analysis"]
        job_agent,                  # Step 2: JD parse -> session["job_analysis"]
        gap_agent,                  # Step 3: gaps     -> session["gap_analysis"]
        strategy_agent,             # Step 4: plan     -> session["career_strategy"]
        interview_agent,            # Step 5: prep kit -> session["interview_prep"]
        _synthesis_agent,           # Step 6: final report -> user
    ],
)
