"""Session View clip and MIDI note tools."""

from typing import Annotated, Any, Dict, List

from fastmcp import FastMCP
from pydantic import Field

from .. import _registry
from ._params import BeatLength, JsonCoerce, SlotIndex, TrackIndex


NoteList = Annotated[
    List[Dict[str, Any]],
    JsonCoerce,
    Field(
        description=(
            "List of MIDI note dicts. Each note: "
            "{pitch (0..127), start_time (beats >= 0), duration (beats > 0), "
            "velocity (1..127), mute (bool, default false)}. "
            "Times are clip-relative. May be passed as a JSON-encoded string."
        )
    ),
]
ClipDefaultLength = Annotated[
    float,
    Field(
        default=4.0,
        description="Initial clip length in beats. Must be > 0.",
        gt=0.0,
    ),
]


def create_clip(track_index: TrackIndex, slot_index: SlotIndex, length: ClipDefaultLength = 4.0):
    return _registry.invoke(
        "create_clip",
        {"track_index": track_index, "slot_index": slot_index, "length": length},
    )


def get_clip_notes(track_index: TrackIndex, slot_index: SlotIndex):
    return _registry.invoke(
        "get_clip_notes",
        {"track_index": track_index, "slot_index": slot_index},
    )


def add_notes_to_clip(track_index: TrackIndex, slot_index: SlotIndex, notes: NoteList):
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
