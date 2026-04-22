"""Domain-grouped MCP tool registration for AbletonMCP."""

from __future__ import absolute_import, print_function, unicode_literals

from fastmcp import FastMCP

from . import (
    arrangement,
    browser,
    device,
    memory_bank,
    rack,
    session_clip,
    song,
    take_lane,
    track,
)

_DOMAINS = (
    song,
    track,
    session_clip,
    arrangement,
    browser,
    device,
    take_lane,
    rack,
    memory_bank,
)


def register_all(mcp: FastMCP) -> None:
    """Register every first-class MCP tool on the given FastMCP instance."""
    for module in _DOMAINS:
        module.register(mcp)


__all__ = ["register_all"]
