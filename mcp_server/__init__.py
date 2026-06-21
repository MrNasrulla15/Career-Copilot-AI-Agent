"""
mcp_server/__init__.py
-----------------------
Career Copilot MCP Server — Document Processing package.

Provides two MCP tools for resume document handling:
  - extract_resume_text   : PDF -> plain text
  - parse_resume_sections : plain text -> structured sections dict

The server runs as a subprocess via stdio transport.
ADK connects to it through McpToolset + StdioServerParameters.
"""
