"""
Runtime patches for the Google Workspace MCP container.

We use sitecustomize so Python automatically imports this module before
`workspace-mcp` bootstraps. The patch strips unknown arguments like
`toolCallId` that n8n's MCP Client adds to tool calls, preventing FastMCP's
Pydantic validation from failing.
"""

from __future__ import annotations

import inspect
import logging
from typing import Any, Dict

from fastmcp.tools.tool import FunctionTool

log = logging.getLogger("workspace_mcp.arg_sanitizer")

_original_run = FunctionTool.run


async def _run_with_arg_sanitizer(self: FunctionTool, arguments: Dict[str, Any]) -> Any:  # type: ignore[override]
    """Sanitize tool arguments before invoking FastMCP's validator."""
    if not isinstance(arguments, dict):
        return await _original_run(self, arguments)

    if not hasattr(self, "_allowed_parameter_names"):
        signature = inspect.signature(self.fn)
        self._allowed_parameter_names = tuple(signature.parameters.keys())  # type: ignore[attr-defined]

    allowed = getattr(self, "_allowed_parameter_names")  # type: ignore[attr-defined]
    sanitized = {k: v for k, v in arguments.items() if k in allowed}

    if len(sanitized) != len(arguments):
        removed = sorted(set(arguments.keys()) - set(allowed))
        log.debug("Dropped unsupported fields for tool '%s': %s", getattr(self, "name", self.fn.__name__), removed)

    return await _original_run(self, sanitized)


FunctionTool.run = _run_with_arg_sanitizer  # type: ignore[assignment]