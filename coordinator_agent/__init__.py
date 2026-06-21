"""
coordinator_agent/__init__.py
------------------------------
ADK web UI entry point for Career Copilot.

The ADK dev server (adk web) looks for a package with a variable named
`root_agent`. This file exposes the SequentialAgent coordinator as `root_agent`
so the system can be explored and tested via the browser UI.

Usage:
    adk web .          # from the career-copilot root directory
    adk run .          # run from CLI without the interactive main.py loop
"""

from agents.coordinator import coordinator_agent

# ADK convention: the dev server looks for a variable named `root_agent`
root_agent = coordinator_agent
