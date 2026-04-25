"""Spec-driven registration helpers for AbletonMCP tools.

Domain modules under ``mcp_server.tools`` define plain Python functions and
register them with a FastMCP instance via :func:`ableton_tool`. This module is
the single source of:

- :func:`invoke` — the TCP call-through to the Ableton Remote Script bridge.
- :func:`ableton_tool` — a decorator that wires a function as an MCP tool
  using the description and annotations stored in :mod:`command_specs`.

Tests patch ``mcp_server._registry.invoke`` to intercept tool calls without
mocking the TCP layer.
"""

from __future__ import absolute_import, print_function, unicode_literals

from typing import Any, Callable, Dict, Optional

from fastmcp import FastMCP

from .client import AbletonRemoteClient
from .command_specs import CommandSpec, get_command_spec


def _make_client() -> AbletonRemoteClient:
    return AbletonRemoteClient.from_env()


def invoke(command_name: str, params: Optional[Dict[str, Any]] = None) -> Any:
    """Send ``command_name`` with ``params`` to the Ableton bridge.

    Raises whatever :meth:`AbletonRemoteClient.send_command` raises. The
    :func:`get_command_spec` lookup is retained as a registry sanity check so
    an unknown command fails before hitting the socket.
    """
    get_command_spec(command_name)
    return _make_client().send_command(command_name, params or {})


def _annotations_for(spec: CommandSpec) -> Dict[str, Any]:
    return {
        "title": spec.name.replace("_", " ").title(),
        "readOnlyHint": not spec.write,
        "destructiveHint": spec.write,
        "idempotentHint": not spec.write,
        "openWorldHint": True,
    }


def ableton_tool(mcp: FastMCP, command_name: str) -> Callable[[Callable], Callable]:
    """Return a decorator that registers ``fn`` as the MCP tool for ``command_name``.

    Description and annotations are pulled from the :class:`CommandSpec` in
    :mod:`command_specs`, so tool metadata stays in lockstep with the registry.
    """
    spec = get_command_spec(command_name)
    annotations = _annotations_for(spec)

    def decorator(fn: Callable) -> Callable:
        mcp.tool(
            name=command_name,
            description=spec.tool_description,
            annotations=annotations,
        )(fn)
        return fn

    return decorator
