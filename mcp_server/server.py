"""
mcp_server/server.py
---------------------
Career Copilot MCP Server — Document Processing Tools.

Exposes two tools over the Model Context Protocol (MCP) stdio transport:

  1. extract_resume_text   — read a PDF file and return clean plain text
  2. parse_resume_sections — split plain text into structured resume sections

Run standalone:
    python -m mcp_server.server

Used by ADK via McpToolset with StdioServerParameters — the coordinator
agent spawns this as a subprocess and communicates over stdin/stdout.
"""

import json
import re
import sys
from pathlib import Path

# Ensure the project root is on sys.path when run as subprocess
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mcp.server.fastmcp import FastMCP


# ---------------------------------------------------------------------------
# MCP server instance
# ---------------------------------------------------------------------------

mcp = FastMCP(
    name="career-copilot-document-processor",
    instructions=(
        "Document processing tools for Career Copilot. "
        "Use extract_resume_text to read a PDF resume file, "
        "then parse_resume_sections to split the text into structured sections. "
        "Always call extract_resume_text first if you have a PDF path."
    ),
)


# ---------------------------------------------------------------------------
# Tool 1 — extract_resume_text
# ---------------------------------------------------------------------------

@mcp.tool(
    description=(
        "Extract clean plain text from a PDF resume file. "
        "Supports multi-page, multi-column PDFs. "
        "Returns the full text content ready for downstream analysis. "
        "Provide the absolute path to the PDF file."
    )
)
def extract_resume_text(file_path: str) -> str:
    """
    Read a PDF resume and return its full text content.

    Uses PyMuPDF (fitz) for layout-aware extraction with pypdf as fallback.
    The returned text includes [Page N] markers for multi-page documents
    and has been cleaned of control characters and ligature artifacts.

    Args:
        file_path: Absolute or relative path to the PDF file.

    Returns:
        Clean extracted text string, or an error message prefixed with
        'ERROR:' if extraction fails.
    """
    try:
        from tools.pdf_parser import extract_text_from_pdf
        return extract_text_from_pdf(file_path)
    except FileNotFoundError:
        return f"ERROR: File not found: {file_path}"
    except ValueError as e:
        return f"ERROR: {e}"
    except RuntimeError as e:
        return f"ERROR: {e}"
    except Exception as e:
        return f"ERROR: Unexpected error during PDF extraction: {e}"


# ---------------------------------------------------------------------------
# Tool 2 — parse_resume_sections
# ---------------------------------------------------------------------------

# Section header patterns — covers most common resume formats
_SECTION_PATTERNS = {
    "contact": [
        r"contact\s*(info|information|details)?",
        r"personal\s*(info|information|details)?",
    ],
    "summary": [
        r"(professional\s+)?summary",
        r"(career\s+)?objective",
        r"profile",
        r"about\s+me",
        r"overview",
    ],
    "experience": [
        r"(work\s+|professional\s+|employment\s+)?experience",
        r"work\s+history",
        r"employment\s+history",
        r"career\s+history",
        r"positions?\s+held",
    ],
    "education": [
        r"education(al\s+background)?",
        r"academic\s+(background|history|qualifications?)",
        r"qualifications?",
        r"degrees?",
    ],
    "skills": [
        r"(technical\s+|core\s+|key\s+)?skills?",
        r"competenc(y|ies)",
        r"technologies",
        r"tech(nical)?\s+stack",
        r"tools?\s+&?\s+technologies",
        r"expertise",
    ],
    "certifications": [
        r"certifications?",
        r"licenses?\s+(&\s+certifications?)?",
        r"credentials?",
        r"accreditations?",
    ],
    "projects": [
        r"(personal\s+|side\s+|key\s+)?projects?",
        r"portfolio",
        r"open[\s-]source",
    ],
    "awards": [
        r"awards?",
        r"honors?",
        r"achievements?",
        r"recognitions?",
        r"accomplishments?",
    ],
    "languages": [
        r"languages?",
        r"spoken\s+languages?",
    ],
    "interests": [
        r"interests?",
        r"hobbies",
        r"activities",
        r"volunteer(ing)?",
    ],
}


def _build_section_regex() -> re.Pattern:
    """Compile a single regex that matches any known section header line."""
    all_patterns = []
    for patterns in _SECTION_PATTERNS.values():
        all_patterns.extend(patterns)
    combined = "|".join(f"(?:{p})" for p in all_patterns)
    # Match a whole line that is (mostly) a section header
    return re.compile(
        rf"^\s*(?:{combined})\s*[:\-–—]?\s*$",
        re.IGNORECASE | re.MULTILINE,
    )


def _classify_section(header_text: str) -> str:
    """Map a raw header string to a canonical section name."""
    header_lower = header_text.strip().lower()
    for section_name, patterns in _SECTION_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, header_lower, re.IGNORECASE):
                return section_name
    return "other"


@mcp.tool(
    description=(
        "Parse plain resume text into structured sections "
        "(contact, summary, experience, education, skills, certifications, projects, etc.). "
        "Call extract_resume_text first if you have a PDF file. "
        "Pass the extracted text string as the 'text' argument."
    )
)
def parse_resume_sections(text: str) -> str:
    """
    Split resume plain text into labelled sections.

    Detects section headers using pattern matching and groups the content
    under canonical section names. Returns a JSON string with each section
    as a key and its content as the value.

    Sections detected: contact, summary, experience, education, skills,
    certifications, projects, awards, languages, interests, other.

    Args:
        text: Plain text extracted from a resume (e.g. from extract_resume_text).

    Returns:
        JSON string with keys for each detected section and their text content.
        Also includes top-level "metadata" with page count and character count.
    """
    if not text or not text.strip():
        return json.dumps({"error": "Empty text provided", "sections": {}})

    if text.startswith("ERROR:"):
        return json.dumps({"error": text, "sections": {}})

    header_re = _build_section_regex()
    lines = text.splitlines()

    sections: dict[str, list[str]] = {}
    current_section = "header"  # text before the first section header
    sections[current_section] = []

    for line in lines:
        if header_re.match(line):
            current_section = _classify_section(line)
            if current_section not in sections:
                sections[current_section] = []
            # Don't add the header line itself — just the content below
        else:
            sections[current_section].append(line)

    # Clean up each section: strip blank lines from edges, join content
    cleaned: dict[str, str] = {}
    for name, content_lines in sections.items():
        content = "\n".join(content_lines).strip()
        if content:  # only include non-empty sections
            cleaned[name] = content

    # Extract a best-guess candidate name from the header section
    candidate_name = ""
    if "header" in cleaned:
        first_lines = [
            l.strip() for l in cleaned["header"].splitlines()
            if l.strip() and not l.strip().startswith("[Page")
        ]
        # The first non-empty, non-email, non-URL line is likely the name
        for line in first_lines[:5]:
            if not re.search(r"[@/\\|]|http|www|\d{3}[-.\s]\d{3}", line):
                candidate_name = line
                break

    result = {
        "metadata": {
            "candidate_name_guess": candidate_name,
            "sections_found": list(cleaned.keys()),
            "total_characters": len(text),
            "page_count": text.count("[Page "),
        },
        "sections": cleaned,
    }

    return json.dumps(result, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Run with stdio transport (used by ADK McpToolset subprocess spawning)
    mcp.run(transport="stdio")
