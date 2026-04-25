"""Arrangement View clip tools."""

from __future__ import absolute_import, print_function, unicode_literals

from typing import Any, Dict, List, Optional

from fastmcp import FastMCP

from .. import _registry


NoteList = List[Dict[str, Any]]


def get_arrangement_clips(track_index: int):
    return _registry.invoke("get_arrangement_clips", {"track_index": track_index})


def create_arrangement_midi_clip(track_index: int, start_time: float, length: float = 4.0):
    return _registry.invoke(
        "create_arrangement_midi_clip",
        {"track_index": track_index, "start_time": start_time, "length": length},
    )


def create_arrangement_audio_clip(track_index: int, file_path: str, start_time: float):
    return _registry.invoke(
        "create_arrangement_audio_clip",
        {"track_index": track_index, "file_path": file_path, "start_time": start_time},
    )


def delete_arrangement_clip(
    track_index: int,
    clip_index: Optional[int] = None,
    start_time: Optional[float] = None,
):
    params = {"track_index": track_index}
    if clip_index is not None:
        params["clip_index"] = clip_index
    if start_time is not None:
        params["start_time"] = start_time
    return _registry.invoke("delete_arrangement_clip", params)


def resize_arrangement_clip(
    track_index: int,
    length: float,
    clip_index: Optional[int] = None,
    start_time: Optional[float] = None,
):
    params = {"track_index": track_index, "length": length}
    if clip_index is not None:
        params["clip_index"] = clip_index
    if start_time is not None:
        params["start_time"] = start_time
    return _registry.invoke("resize_arrangement_clip", params)


def move_arrangement_clip(
    track_index: int,
    new_start_time: float,
    clip_index: Optional[int] = None,
    start_time: Optional[float] = None,
):
    params = {"track_index": track_index, "new_start_time": new_start_time}
    if clip_index is not None:
        params["clip_index"] = clip_index
    if start_time is not None:
        params["start_time"] = start_time
    return _registry.invoke("move_arrangement_clip", params)


def add_notes_to_arrangement_clip(
    track_index: int,
    notes: NoteList,
    clip_index: Optional[int] = None,
    start_time: Optional[float] = None,
):
    params = {"track_index": track_index, "notes": notes}
    if clip_index is not None:
        params["clip_index"] = clip_index
    if start_time is not None:
        params["start_time"] = start_time
    return _registry.invoke("add_notes_to_arrangement_clip", params)


def get_arrangement_clip_notes(
    track_index: int,
    clip_index: Optional[int] = None,
    start_time: Optional[float] = None,
):
    params = {"track_index": track_index}
    if clip_index is not None:
        params["clip_index"] = clip_index
    if start_time is not None:
        params["start_time"] = start_time
    return _registry.invoke("get_arrangement_clip_notes", params)


def duplicate_to_arrangement(
    track_index: int,
    slot_index: int,
    start_time: Optional[float] = None,
):
    params = {"track_index": track_index, "slot_index": slot_index}
    if start_time is not None:
        params["start_time"] = start_time
    return _registry.invoke("duplicate_to_arrangement", params)


_TOOLS = (
    get_arrangement_clips,
    create_arrangement_midi_clip,
    create_arrangement_audio_clip,
    delete_arrangement_clip,
    resize_arrangement_clip,
    move_arrangement_clip,
    add_notes_to_arrangement_clip,
    get_arrangement_clip_notes,
    duplicate_to_arrangement,
)


def register(mcp: FastMCP) -> None:
    for fn in _TOOLS:
        _registry.ableton_tool(mcp, fn.__name__)(fn)
