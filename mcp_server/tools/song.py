"""Health, session inspection, and song/transport tools."""

from __future__ import absolute_import, print_function, unicode_literals

from fastmcp import FastMCP

from .. import _registry


def health_check():
    return _registry.invoke("health_check", {})


def get_session_info():
    return _registry.invoke("get_session_info", {})


def get_session_path():
    return _registry.invoke("get_session_path", {})


def get_current_song_time():
    return _registry.invoke("get_current_song_time", {})


def set_current_song_time(time: float):
    return _registry.invoke("set_current_song_time", {"time": time})


def set_tempo(tempo: float):
    return _registry.invoke("set_tempo", {"tempo": tempo})


def start_playback():
    return _registry.invoke("start_playback", {})


def stop_playback():
    return _registry.invoke("stop_playback", {})


_TOOLS = (
    health_check,
    get_session_info,
    get_session_path,
    get_current_song_time,
    set_current_song_time,
    set_tempo,
    start_playback,
    stop_playback,
)


def register(mcp: FastMCP) -> None:
    for fn in _TOOLS:
        _registry.ableton_tool(mcp, fn.__name__)(fn)
