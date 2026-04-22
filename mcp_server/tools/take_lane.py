"""Take-lane tools."""

from __future__ import absolute_import, print_function, unicode_literals

from typing import Optional

from fastmcp import FastMCP

from .. import _registry


def get_take_lanes(track_index: int):
    return _registry.invoke("get_take_lanes", {"track_index": track_index})


def create_take_lane(track_index: int):
    return _registry.invoke("create_take_lane", {"track_index": track_index})


def set_take_lane_name(track_index: int, lane_index: int, name: str):
    return _registry.invoke(
        "set_take_lane_name",
        {"track_index": track_index, "lane_index": lane_index, "name": name},
    )


def create_midi_clip_in_lane(
    track_index: int,
    lane_index: int,
    start_time: Optional[float] = None,
    length: Optional[float] = None,
):
    params = {"track_index": track_index, "lane_index": lane_index}
    if start_time is not None:
        params["start_time"] = start_time
    if length is not None:
        params["length"] = length
    return _registry.invoke("create_midi_clip_in_lane", params)


def get_clips_in_take_lane(track_index: int, lane_index: int):
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
