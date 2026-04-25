"""Track, return, send, and selection tools."""

from __future__ import absolute_import, print_function, unicode_literals

from typing import Optional

from fastmcp import FastMCP

from .. import _registry


def get_all_track_names():
    return _registry.invoke("get_all_track_names", {})


def get_track_info(track_index: int):
    return _registry.invoke("get_track_info", {"track_index": track_index})


def create_midi_track(index: Optional[int] = None):
    params = {}
    if index is not None:
        params["index"] = index
    return _registry.invoke("create_midi_track", params)


def create_audio_track(index: Optional[int] = None):
    params = {}
    if index is not None:
        params["index"] = index
    return _registry.invoke("create_audio_track", params)


def set_track_name(track_index: int, name: str):
    return _registry.invoke("set_track_name", {"track_index": track_index, "name": name})


def set_track_color(track_index: int, color: int):
    return _registry.invoke("set_track_color", {"track_index": track_index, "color": color})


def set_track_volume(track_index: int, volume: float):
    return _registry.invoke("set_track_volume", {"track_index": track_index, "volume": volume})


def set_track_pan(track_index: int, pan: float):
    return _registry.invoke("set_track_pan", {"track_index": track_index, "pan": pan})


def set_track_mute(track_index: int, mute: bool):
    return _registry.invoke("set_track_mute", {"track_index": track_index, "mute": mute})


def set_track_solo(track_index: int, solo: bool):
    return _registry.invoke("set_track_solo", {"track_index": track_index, "solo": solo})


def set_track_arm(track_index: int, arm: bool):
    return _registry.invoke("set_track_arm", {"track_index": track_index, "arm": arm})


def fold_track(track_index: int):
    return _registry.invoke("fold_track", {"track_index": track_index})


def unfold_track(track_index: int):
    return _registry.invoke("unfold_track", {"track_index": track_index})


def set_send_level(track_index: int, send_index: int, level: float):
    return _registry.invoke(
        "set_send_level",
        {"track_index": track_index, "send_index": send_index, "level": level},
    )


def get_return_tracks():
    return _registry.invoke("get_return_tracks", {})


def get_return_track_info(return_index: int):
    return _registry.invoke("get_return_track_info", {"return_index": return_index})


def set_return_volume(return_index: int, volume: float):
    return _registry.invoke("set_return_volume", {"return_index": return_index, "volume": volume})


def set_return_pan(return_index: int, pan: float):
    return _registry.invoke("set_return_pan", {"return_index": return_index, "pan": pan})


def select_track(
    track_index: Optional[int] = None,
    return_index: Optional[int] = None,
    master: bool = False,
):
    params = {}
    if track_index is not None:
        params["track_index"] = track_index
    if return_index is not None:
        params["return_index"] = return_index
    if master:
        params["master"] = True
    return _registry.invoke("select_track", params)


def get_selected_track():
    return _registry.invoke("get_selected_track", {})


_TOOLS = (
    get_all_track_names,
    get_track_info,
    create_midi_track,
    create_audio_track,
    set_track_name,
    set_track_color,
    set_track_volume,
    set_track_pan,
    set_track_mute,
    set_track_solo,
    set_track_arm,
    fold_track,
    unfold_track,
    set_send_level,
    get_return_tracks,
    get_return_track_info,
    set_return_volume,
    set_return_pan,
    select_track,
    get_selected_track,
)


def register(mcp: FastMCP) -> None:
    for fn in _TOOLS:
        _registry.ableton_tool(mcp, fn.__name__)(fn)
