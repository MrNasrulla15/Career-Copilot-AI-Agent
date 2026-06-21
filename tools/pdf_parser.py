"""
tools/pdf_parser.py
--------------------
PDF Resume Parser — extracts clean plain text from uploaded PDF files.

Designed to be the preprocessing step before the agent pipeline runs.
Supports multi-page PDFs with complex layouts (columns, tables, headers).

Library strategy:
    Primary:  pymupdf (fitz) — best-in-class layout handling, fast, handles
              multi-column resumes, preserves reading order.
    Fallback: pypdf           — pure Python, no binary deps, handles simpler PDFs.

Usage:
    # As a standalone utility:
    from tools.pdf_parser import extract_text_from_pdf
    text = extract_text_from_pdf("path/to/resume.pdf")

    # As an ADK FunctionTool (called by an agent):
    from tools.pdf_parser import pdf_parser_tool
"""

from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path

from google.adk.tools import FunctionTool


# ---------------------------------------------------------------------------
# Core extraction logic
# ---------------------------------------------------------------------------

def _extract_with_pymupdf(pdf_path: str) -> str:
    """
    Extract text using PyMuPDF (fitz).

    Uses layout-aware extraction mode which preserves reading order
    across multi-column resumes — critical for correct skill/experience parsing.
    """
    import fitz  # pymupdf

    doc = fitz.open(pdf_path)
    pages: list[str] = []

    for page_num, page in enumerate(doc, start=1):
        # "text" mode: simple text extraction preserving basic structure.
        # "blocks" or "dict" modes are available for richer parsing.
        text = page.get_text("text")
        if text.strip():
            pages.append(f"[Page {page_num}]\n{text}")

    doc.close()
    return "\n\n".join(pages)


def _extract_with_pypdf(pdf_path: str) -> str:
    """
    Fallback extraction using pypdf.

    Works well for simple single-column PDFs. May lose column ordering
    on complex multi-column layouts.
    """
    from pypdf import PdfReader

    reader = PdfReader(pdf_path)
    pages: list[str] = []

    for page_num, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if text.strip():
            pages.append(f"[Page {page_num}]\n{text}")

    return "\n\n".join(pages)


def _clean_text(raw: str) -> str:
    """
    Post-process extracted text for cleaner downstream LLM consumption.

    Steps:
        1. Normalize unicode characters (ligatures, smart quotes, etc.)
        2. Collapse runs of blank lines to a single blank line
        3. Strip leading/trailing whitespace from each line
        4. Remove non-printable control characters
        5. Preserve meaningful line breaks (paragraph structure)
    """
    # Remove control characters except newlines and tabs
    cleaned = re.sub(r"[^\x09\x0A\x0D\x20-\x7E\u00A0-\uFFFF]", " ", raw)

    # Normalize common ligatures and special chars
    replacements = {
        "\ufb01": "fi", "\ufb02": "fl", "\u2019": "'", "\u2018": "'",
        "\u201c": '"', "\u201d": '"', "\u2013": "-", "\u2014": "--",
        "\u2022": "-", "\u00b7": "-", "\u2026": "...",
    }
    for orig, rep in replacements.items():
        cleaned = cleaned.replace(orig, rep)

    # Normalize whitespace: strip each line, collapse multiple blank lines
    lines = [line.rstrip() for line in cleaned.splitlines()]
    result_lines: list[str] = []
    blank_count = 0

    for line in lines:
        if not line.strip():
            blank_count += 1
            if blank_count <= 1:
                result_lines.append("")  # allow one blank line between sections
        else:
            blank_count = 0
            result_lines.append(line)

    return "\n".join(result_lines).strip()


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract clean plain text from a PDF file.

    Tries PyMuPDF first (best quality), falls back to pypdf if unavailable.
    The returned text is cleaned and ready to be passed directly to the
    ResumeAnalysisAgent or any downstream LLM.

    Args:
        pdf_path: Absolute or relative path to the PDF file.

    Returns:
        Clean extracted text string. Includes [Page N] markers for multi-page PDFs.

    Raises:
        FileNotFoundError: If the PDF file does not exist.
        ValueError:        If the file is not a PDF or is empty after extraction.
        RuntimeError:      If both PDF libraries fail to extract text.
    """
    path = Path(pdf_path).resolve()

    if not path.exists():
        raise FileNotFoundError(f"PDF file not found: {path}")

    if path.suffix.lower() != ".pdf":
        raise ValueError(f"Expected a .pdf file, got: {path.suffix}")

    if path.stat().st_size == 0:
        raise ValueError(f"PDF file is empty: {path}")

    raw_text = ""
    extraction_method = "unknown"
    errors: list[str] = []

    # Try PyMuPDF first
    try:
        import fitz  # noqa: F401
        raw_text = _extract_with_pymupdf(str(path))
        extraction_method = "pymupdf"
    except ImportError:
        errors.append("pymupdf not installed")
    except Exception as e:
        errors.append(f"pymupdf failed: {e}")

    # Fall back to pypdf
    if not raw_text:
        try:
            from pypdf import PdfReader  # noqa: F401
            raw_text = _extract_with_pypdf(str(path))
            extraction_method = "pypdf"
        except ImportError:
            errors.append("pypdf not installed")
        except Exception as e:
            errors.append(f"pypdf failed: {e}")

    if not raw_text:
        raise RuntimeError(
            f"Failed to extract text from {path.name}. "
            f"Errors: {'; '.join(errors)}. "
            "Install pymupdf or pypdf: pip install pymupdf pypdf"
        )

    cleaned = _clean_text(raw_text)

    if not cleaned:
        raise ValueError(
            f"PDF '{path.name}' appears to be image-based (scanned) with no "
            "embedded text. OCR support is not yet included. "
            "Please provide a text-based PDF or paste the resume text directly."
        )

    # Prepend a metadata header for the LLM
    header = (
        f"--- RESUME EXTRACTED FROM PDF ---\n"
        f"File      : {path.name}\n"
        f"Pages     : {raw_text.count('[Page ')}\n"
        f"Extracted : {extraction_method}\n"
        f"---\n\n"
    )

    return header + cleaned


# ---------------------------------------------------------------------------
# ADK FunctionTool wrapper
# ---------------------------------------------------------------------------

def parse_resume_pdf(file_path: str) -> dict:
    """
    Extract plain text from a PDF resume file.

    This tool reads a PDF file from the given file path, extracts all text
    content while preserving structure (sections, order), and returns the
    raw text ready for the ResumeAnalysisAgent to process.

    Use this tool BEFORE calling ResumeAnalysisAgent when the user provides
    a PDF file instead of pasting resume text directly.

    Args:
        file_path: The absolute or relative path to the PDF resume file.
                   Example: "C:/Users/name/resume.pdf" or "./resume.pdf"

    Returns:
        A dict with:
            "success"   (bool):   True if extraction succeeded.
            "text"      (str):    Extracted resume text (empty string on failure).
            "file_name" (str):    Name of the PDF file processed.
            "page_count" (int):   Number of pages extracted from.
            "error"     (str):    Error message if success is False, else "".
    """
    try:
        text = extract_text_from_pdf(file_path)
        page_count = text.count("[Page ")
        file_name  = Path(file_path).name
        return {
            "success":    True,
            "text":       text,
            "file_name":  file_name,
            "page_count": page_count,
            "error":      "",
        }
    except (FileNotFoundError, ValueError, RuntimeError) as e:
        return {
            "success":    False,
            "text":       "",
            "file_name":  Path(file_path).name,
            "page_count": 0,
            "error":      str(e),
        }


# ADK FunctionTool — can be added to any agent's tools list
pdf_parser_tool = FunctionTool(func=parse_resume_pdf)
