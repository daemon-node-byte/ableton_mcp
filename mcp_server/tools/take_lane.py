"""Take-lane tools."""

from typing import Annotated, Any, Dict, Optional

from fastmcp import FastMCP
from pydantic import Field

from .. import _registry
from ._params import LaneIndex, TrackIndex


TakeLaneName = Annotated[
    str,
    Field(description="Take-lane display name (non-empty).", min_length=1, max_length=200),
]
OptionalLaneStartTime = Annotated[
    Optional[float],
    Field(
        default=None,
        description="Clip start time in Arrangement beats (>= 0). Defaults to 0 if omitted.",
        ge=0.0,
    ),
]
OptionalLaneClipLength = Annotated[
    Optional[float],
    Field(
        default=None,
        description="Clip length in beats (> 0). Defaults to a Live-side default when omitted.",
        gt=0.0,
    ),
]


def get_take_lanes(track_index: TrackIndex):
    return _registry.invoke("get_take_lanes", {"track_index": track_index})


def create_take_lane(track_index: TrackIndex):
    return _registry.invoke("create_take_lane", {"track_index": track_index})


def set_take_lane_name(track_index: TrackIndex, lane_index: LaneIndex, name: TakeLaneName):
    return _registry.invoke(
        "set_take_lane_name",
        {"track_index": track_index, "lane_index": lane_index, "name": name},
    )


def create_midi_clip_in_lane(
    track_index: TrackIndex,
    lane_index: LaneIndex,
    start_time: OptionalLaneStartTime = None,
    length: OptionalLaneClipLength = None,
):
    params: Dict[str, Any] = {"track_index": track_index, "lane_index": lane_index}
    if start_time is not None:
        params["start_time"] = start_time
    if length is not None:
        params["length"] = length
    return _registry.invoke("create_midi_clip_in_lane", params)


def get_clips_in_take_lane(track_index: TrackIndex, lane_index: LaneIndex):
    return _registry.invoke(
        "get_clips_in_take_lane",
        {"track_index": track_index, "lane_index": lane_index},
    )


_TOOLS = (
    get_take_lanes,
    create_take_lane,
    set_take_lane_name,
    create_midi_clip_in_lane,
    get_clips_in_take_lane,
)


def register(mcp: FastMCP) -> None:
    for fn in _TOOLS:
        _registry.ableton_tool(mcp, fn.__name__)(fn)
