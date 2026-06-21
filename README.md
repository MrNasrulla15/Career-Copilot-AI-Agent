# 🚀 Career Copilot

> A production-ready multi-agent AI system built with [Google ADK](https://google.github.io/adk-docs) that analyzes your resume, deconstructs job descriptions, identifies skill gaps, builds a personalized career strategy, and prepares you for interviews — all in one pipeline.

---

## Workflow Architecture

Below is the workflow diagram showing how the root **CareerCopilotCoordinator** orchestrates the specialized sub-agents and custom tools to compile your Career Intelligence Report:

![Career Copilot Architecture](docs/assets/career_copilot_architecture.png)

---

## Architecture

```
career_copilot/
│
├── agents/
│   ├── __init__.py          # Exports all specialist agent instances
│   ├── coordinator.py       # 🤝 Root orchestrator — wraps all sub-agents as tools
│   ├── resume_agent.py      # 📋 Parses resume → session.state["resume_analysis"]
│   ├── job_agent.py         # 💼 Parses job description → session.state["job_analysis"]
│   ├── gap_agent.py         # 📊 Computes gaps → session.state["gap_analysis"]
│   ├── strategy_agent.py    # 🗺️ Builds 30/60/90-day plan → session.state["career_strategy"]
│   └── interview_agent.py   # 🎤 Generates prep kit → session.state["interview_prep"]
│
├── tools/
│   ├── __init__.py          # Wraps all callables in FunctionTool, exports grouped lists
│   ├── resume_tools.py      # extract_skills, score_resume_section, detect_resume_format
│   ├── job_tools.py         # extract_job_requirements, classify_seniority, detect_tech_stack
│   ├── gap_tools.py         # compute_skill_overlap, prioritize_gaps, estimate_learning_time
│   ├── strategy_tools.py    # generate_action_items, recommend_resources, build_timeline
│   └── interview_tools.py   # generate_interview_questions, draft_star_answer, create_cheat_sheet
│
├── prompts/
│   ├── __init__.py          # Re-exports all prompt constants
│   ├── coordinator_prompts.py
│   ├── resume_prompts.py
│   ├── job_prompts.py
│   ├── gap_prompts.py
│   ├── strategy_prompts.py
│   └── interview_prompts.py
│
├── main.py                  # CLI entry point — async interactive session
├── requirements.txt         # Python dependencies
├── .env.example             # Environment variable template
└── README.md
```

## Multi-Agent Pipeline

```
User Input (resume + job description)
         │
         ▼
┌─────────────────────────┐
│  CareerCopilotCoordinator│  ← Root LlmAgent
│  (agents/coordinator.py) │
└────────────┬────────────┘
             │  delegates via AgentTool
    ┌────────┴──────────────────────────────────┐
    │        Sequential delegation order         │
    ▼                                            │
┌──────────────────┐                             │
│ ResumeAnalysis   │ → session["resume_analysis"]│
└──────────┬───────┘                             │
           ▼                                     │
┌──────────────────┐                             │
│ JobAnalysis      │ → session["job_analysis"]   │
└──────────┬───────┘                             │
           ▼                                     │
┌──────────────────┐                             │
│ GapAnalysis      │ → session["gap_analysis"]   │
└──────────┬───────┘                             │
           ▼                                     │
┌──────────────────┐                             │
│ CareerStrategy   │ → session["career_strategy"]│
└──────────┬───────┘                             │
           ▼                                     │
┌──────────────────┐                             │
│ InterviewPrep    │ → session["interview_prep"] │
└──────────┬───────┘                             │
           └────────────────────────────────────┘
                         │
                         ▼
             📄 Career Intelligence Report
```

### Key Design Patterns

| Pattern | Where Used | Why |
|---|---|---|
| **Agent-as-Tool** | `coordinator.py` | Each specialist agent wrapped in `AgentTool` — coordinator's LLM decides when to call each one |
| **output_key** | All specialist agents | Automatically saves agent output to `session.state[key]` for downstream consumption |
| **Session state sharing** | Gap, Strategy, Interview agents | Agents read from earlier agents' outputs without direct coupling |
| **Centralized prompts** | `prompts/` | System instructions kept separate for easy tuning without touching agent logic |
| **Grouped FunctionTools** | `tools/__init__.py` | All tools wrapped once and exported as lists for clean agent instantiation |

---

## Setup

### 1. Clone and create a virtual environment

```bash
cd career-copilot
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

Get a free API key at: https://aistudio.google.com/app/apikey

### 4. Run the Interactive CLI

```bash
python main.py
```

### 5. Run the Web Application (FastAPI + Web UI)

You can also run Career Copilot as a modern web app with a visual interface:

```bash
uvicorn api.server:app --port 8000
```
Then open **http://localhost:8000** in your browser to upload files and view results.

---

## Usage

When the CLI starts, paste your resume text, job description, or both.
Type **`DONE`** on a new line and press Enter to submit.

**Example inputs:**

```
[Turn 1] You → (press Enter twice when done):
Here's my resume:
[paste resume text]

Here's the job I'm targeting:
[paste job description]

```

The coordinator will:
1. Analyze your resume
2. Parse the job description  
3. Identify skill gaps and compute your match score
4. Build a personalized 30/60/90-day action plan
5. Generate a tailored interview prep kit
6. Deliver a complete Career Intelligence Report

---

## Agents Reference

| Agent | File | Tools | Output Key |
|---|---|---|---|
| Coordinator | `agents/coordinator.py` | AgentTools (5 sub-agents) | — |
| Resume Analysis | `agents/resume_agent.py` | `extract_skills`, `score_resume_section`, `detect_resume_format` | `resume_analysis` |
| Job Analysis | `agents/job_agent.py` | `extract_job_requirements`, `classify_seniority`, `detect_tech_stack` | `job_analysis` |
| Gap Analysis | `agents/gap_agent.py` | `compute_skill_overlap`, `prioritize_gaps`, `estimate_learning_time` | `gap_analysis` |
| Career Strategy | `agents/strategy_agent.py` | `generate_action_items`, `recommend_resources`, `build_timeline` | `career_strategy` |
| Interview Prep | `agents/interview_agent.py` | `generate_interview_questions`, `draft_star_answer`, `create_cheat_sheet` | `interview_prep` |

---

## Extending the System

**Add a new tool:**
1. Define a Python function with a clear docstring in `tools/<agent>_tools.py`
2. Add `FunctionTool(func=your_function)` to the relevant list in `tools/__init__.py`
3. Add the tool to the relevant agent's `tools=` list

**Add a new agent:**
1. Create `agents/new_agent.py` with an `LlmAgent` definition
2. Add its prompt to `prompts/new_prompts.py`
3. Export from `agents/__init__.py`
4. Wrap in `AgentTool` in `agents/coordinator.py`

**Swap to production session storage:**
Replace `InMemorySessionService` in `main.py` with a persistent implementation
(e.g., backed by Cloud Firestore or a SQL database).

**Deploy to Cloud Run:**
```bash
adk deploy cloud_run --project YOUR_GCP_PROJECT agents/coordinator.py
```
