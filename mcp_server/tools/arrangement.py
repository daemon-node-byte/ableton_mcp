"""Arrangement View clip tools."""

from typing import Annotated, Any, Dict, List, Optional

from fastmcp import FastMCP
from pydantic import Field

from .. import _registry
from ._params import BeatLength, BeatTime, JsonCoerce, OptionalBeatTime, SlotIndex, TrackIndex


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
OptionalClipIndex = Annotated[
    Optional[int],
    Field(
        default=None,
        description=(
            "0-based index into the track's arrangement_clips list. "
            "Selector: pass exactly one of clip_index or start_time."
        ),
        ge=0,
    ),
]
OptionalClipStartTime = Annotated[
    Optional[float],
    Field(
        default=None,
        description=(
            "Existing clip's start time in Arrangement beats. "
            "Selector: pass exactly one of clip_index or start_time."
        ),
        ge=0.0,
    ),
]


def get_arrangement_clips(track_index: TrackIndex):
    return _registry.invoke("get_arrangement_clips", {"track_index": track_index})


def create_arrangement_midi_clip(
    track_index: TrackIndex,
    start_time: BeatTime,
    length: BeatLength = 4.0,
):
    return _registry.invoke(
        "create_arrangement_midi_clip",
        {"track_index": track_index, "start_time": start_time, "length": length},
    )


def create_arrangement_audio_clip(
    track_index: TrackIndex,
    file_path: Annotated[
        str,
        Field(
            description=(
                "Absolute filesystem path to the source audio file. The file must already exist on disk; "
                "relative paths are rejected."
            ),
            min_length=1,
        ),
    ],
    start_time: BeatTime,
):
    return _registry.invoke(
        "create_arrangement_audio_clip",
        {"track_index": track_index, "file_path": file_path, "start_time": start_time},
    )


def delete_arrangement_clip(
    track_index: TrackIndex,
    clip_index: OptionalClipIndex = None,
    start_time: OptionalClipStartTime = None,
):
    params: Dict[str, Any] = {"track_index": track_index}
    if clip_index is not None:
        params["clip_index"] = clip_index
    if start_time is not None:
        params["start_time"] = start_time
    return _registry.invoke("delete_arrangement_clip", params)


def resize_arrangement_clip(
    track_index: TrackIndex,
    length: BeatLength,
    clip_index: OptionalClipIndex = None,
    start_time: OptionalClipStartTime = None,
):
    params: Dict[str, Any] = {"track_index": track_index, "length": length}
    if clip_index is not None:
        params["clip_index"] = clip_index
    if start_time is not None:
        params["start_time"] = start_time
    return _registry.invoke("resize_arrangement_clip", params)


def move_arrangement_clip(
    track_index: TrackIndex,
    new_start_time: Annotated[
        float,
        Field(description="New clip start time in Arrangement beats (>= 0).", ge=0.0),
    ],
    clip_index: OptionalClipIndex = None,
    start_time: OptionalClipStartTime = None,
):
    params: Dict[str, Any] = {"track_index": track_index, "new_start_time": new_start_time}
    if clip_index is not None:
        params["clip_index"] = clip_index
    if start_time is not None:
        params["start_time"] = start_time
    return _registry.invoke("move_arrangement_clip", params)


def add_notes_to_arrangement_clip(
    track_index: TrackIndex,
    notes: NoteList,
    clip_index: OptionalClipIndex = None,
    start_time: OptionalClipStartTime = None,
):
    params: Dict[str, Any] = {"track_index": track_index, "notes": notes}
    if clip_index is not None:
        params["clip_index"] = clip_index
    if start_time is not None:
        params["start_time"] = start_time
    return _registry.invoke("add_notes_to_arrangement_clip", params)


def get_arrangement_clip_notes(
    track_index: TrackIndex,
    clip_index: OptionalClipIndex = None,
    start_time: OptionalClipStartTime = None,
):
    params: Dict[str, Any] = {"track_index": track_index}
    if clip_index is not None:
        params["clip_index"] = clip_index
    if start_time is not None:
        params["start_time"] = start_time
    return _registry.invoke("get_arrangement_clip_notes", params)


def duplicate_to_arrangement(
    track_index: TrackIndex,
    slot_index: SlotIndex,
    start_time: OptionalBeatTime = None,
):
    params: Dict[str, Any] = {"track_index": track_index, "slot_index": slot_index}
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
