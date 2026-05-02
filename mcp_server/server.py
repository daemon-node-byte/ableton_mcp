"""FastMCP entrypoint for AbletonMCP v2.

Tool definitions live under :mod:`mcp_server.tools`, grouped by domain. This
module builds the FastMCP instance, wires the domain tools, exposes the
``ableton_raw_command`` catch-all, and owns the transport configuration.

Three names point at the same FastMCP instance (``mcp``, ``server``, ``app``)
so that hosting platforms that infer the object by name (e.g. Horizon) all
resolve the same server. See ``docs/install-and-use-mcp.md`` §7.
"""

from __future__ import absolute_import, print_function, unicode_literals

import os
from typing import Annotated, Any, Dict, Optional

from fastmcp import FastMCP
from pydantic import Field

from . import _registry
from .command_specs import FIRST_CLASS_MCP_COMMANDS, get_command_spec
from .tools import register_all
from .tools._params import JsonCoerce


JsonDict = Dict[str, Any]
DEFAULT_TRANSPORT = "stdio"
SUPPORTED_TRANSPORTS = ("stdio", "http", "streamable-http", "sse")
DEFAULT_BIND_HOST = "0.0.0.0"
DEFAULT_HTTP_PATH = "/mcp/"
DEFAULT_HTTP_PORT = 8080


def _normalize_transport_name(value: Optional[str]) -> str:
    transport = (value or DEFAULT_TRANSPORT).strip().lower()
    if transport not in SUPPORTED_TRANSPORTS:
        raise ValueError("Unsupported ABLETON_MCP_TRANSPORT '{}'".format(transport))
    return transport


def _normalize_http_path(value: Optional[str]) -> str:
    path = (value or DEFAULT_HTTP_PATH).strip() or DEFAULT_HTTP_PATH
    if not path.startswith("/"):
        path = "/" + path
    if not path.endswith("/"):
        path = path + "/"
    return path


def _get_http_port() -> int:
    raw_value = os.environ.get("PORT", str(DEFAULT_HTTP_PORT))
    try:
        return int(raw_value)
    except ValueError:
        raise ValueError("Invalid PORT '{}'".format(raw_value))


def _get_run_configuration() -> Dict[str, Any]:
    requested_transport = _normalize_transport_name(os.environ.get("ABLETON_MCP_TRANSPORT"))
    if requested_transport == "stdio":
        return {"transport": "stdio", "kwargs": {}}

    transport = "http" if requested_transport in ("http", "streamable-http") else "sse"
    return {
        "transport": transport,
        "kwargs": {
            "host": os.environ.get("ABLETON_MCP_BIND_HOST", DEFAULT_BIND_HOST),
            "port": _get_http_port(),
            "path": _normalize_http_path(os.environ.get("ABLETON_MCP_HTTP_PATH")),
        },
    }


mcp = FastMCP(
    "ableton-mcp-v2",
    instructions=(
        "Ableton Live 12 MCP server backed by the AbletonMCP Remote Script over TCP. "
        "Only the audited tool slice is exposed as first-class MCP tools in this pass; "
        "use ableton_raw_command for the wider command surface."
    ),
)

# Hosting platforms that infer the FastMCP object by name look for one of these.
server = mcp
app = mcp

register_all(mcp)


@mcp.tool(
    name="ableton_raw_command",
    description=(
        "Call any cataloged Ableton Remote Script command directly. "
        "Returns command metadata alongside the raw command result."
    ),
    annotations={
        "title": "Ableton Raw Command",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
def ableton_raw_command(
    type: Annotated[
        str,
        Field(description="Cataloged command name from command_specs (e.g. 'set_track_volume')."),
    ],
    params: Annotated[
        Optional[Dict[str, Any]],
        JsonCoerce,
        Field(
            default=None,
            description=(
                "Parameter object for the command. May be passed as a JSON-encoded string."
            ),
        ),
    ] = None,
) -> JsonDict:
    spec = get_command_spec(type)
    result = _registry.invoke(type, params or {})
    return {
        "command": type,
        "domain": spec.domain,
        "stability": spec.stability,
        "mcp_exposed": spec.mcp_exposed,
        "result": result,
    }


def main() -> None:
    configuration = _get_run_configuration()
    mcp.run(transport=configuration["transport"], **configuration["kwargs"])


__all__ = [
    "FIRST_CLASS_MCP_COMMANDS",
    "ableton_raw_command",
    "app",
    "main",
    "mcp",
    "server",
]
