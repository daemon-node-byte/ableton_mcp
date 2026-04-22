"""Session View clip and MIDI note tools."""

from __future__ import absolute_import, print_function, unicode_literals

from typing import Any, Dict, List

from fastmcp import FastMCP

from .. import _registry


NoteList = List[Dict[str, Any]]


def create_clip(track_index: int, slot_index: int, length: float = 4.0):
    return _registry.invoke(
        "create_clip",
        {"track_index": track_index, "slot_index": slot_index, "length": length},
    )


def get_clip_notes(track_index: int, slot_index: int):
    return _registry.invoke(
        "get_clip_notes",
        {"track_index": track_index, "slot_index": slot_index},
    )


def add_notes_to_clip(track_index: int, slot_index: int, notes: NoteList):
    return _registry.invoke(
        "add_notes_to_clip",
        {"track_index": track_index, "slot_index": slot_index, "notes": notes},
    )


_TOOLS = (
    create_clip,
    get_clip_notes,
    add_notes_to_clip,
)


def register(mcp: FastMCP) -> None:
    for fn in _TOOLS:
        _registry.ableton_tool(mcp, fn.__name__)(fn)
