"""FastMCP server for AbletonMCP v2."""

from __future__ import absolute_import, print_function, unicode_literals

import os
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP

from .client import AbletonRemoteClient
from .command_specs import FIRST_CLASS_MCP_COMMANDS, get_command_spec


JsonDict = Dict[str, Any]
NoteList = List[Dict[str, Any]]
DEFAULT_TRANSPORT = "stdio"
SUPPORTED_TRANSPORTS = ("stdio", "http", "streamable-http", "sse")
DEFAULT_BIND_HOST = "0.0.0.0"
DEFAULT_HTTP_PATH = "/mcp/"
DEFAULT_HTTP_PORT = 8080


def _make_client():
    return AbletonRemoteClient.from_env()


def _invoke(command_name, params):
    get_command_spec(command_name)
    client = _make_client()
    return client.send_command(command_name, params)


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


def _get_run_configuration():
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

# Keep these aliases for hosting platforms that infer object names.
server = mcp
app = mcp


@mcp.tool(description=get_command_spec("health_check").tool_description)
def health_check():
    return _invoke("health_check", {})


@mcp.tool(description=get_command_spec("get_session_info").tool_description)
def get_session_info():
    return _invoke("get_session_info", {})


@mcp.tool(description=get_command_spec("get_session_path").tool_description)
def get_session_path():
    return _invoke("get_session_path", {})


@mcp.tool(description=get_command_spec("get_current_song_time").tool_description)
def get_current_song_time():
    return _invoke("get_current_song_time", {})


@mcp.tool(description=get_command_spec("set_current_song_time").tool_description)
def set_current_song_time(time: float):
    return _invoke("set_current_song_time", {"time": time})


@mcp.tool(description=get_command_spec("set_tempo").tool_description)
def set_tempo(tempo: float):
    return _invoke("set_tempo", {"tempo": tempo})


@mcp.tool(description=get_command_spec("start_playback").tool_description)
def start_playback():
    return _invoke("start_playback", {})


@mcp.tool(description=get_command_spec("stop_playback").tool_description)
def stop_playback():
    return _invoke("stop_playback", {})


@mcp.tool(description=get_command_spec("get_all_track_names").tool_description)
def get_all_track_names():
    return _invoke("get_all_track_names", {})


@mcp.tool(description=get_command_spec("get_track_info").tool_description)
def get_track_info(track_index: int):
    return _invoke("get_track_info", {"track_index": track_index})


@mcp.tool(description=get_command_spec("create_midi_track").tool_description)
def create_midi_track(index: Optional[int] = None):
    params = {}
    if index is not None:
        params["index"] = index
    return _invoke("create_midi_track", params)


@mcp.tool(description=get_command_spec("create_audio_track").tool_description)
def create_audio_track(index: Optional[int] = None):
    params = {}
    if index is not None:
        params["index"] = index
    return _invoke("create_audio_track", params)


@mcp.tool(description=get_command_spec("set_track_name").tool_description)
def set_track_name(track_index: int, name: str):
    return _invoke("set_track_name", {"track_index": track_index, "name": name})


@mcp.tool(description=get_command_spec("set_track_color").tool_description)
def set_track_color(track_index: int, color: int):
    return _invoke("set_track_color", {"track_index": track_index, "color": color})


@mcp.tool(description=get_command_spec("set_track_volume").tool_description)
def set_track_volume(track_index: int, volume: float):
    return _invoke("set_track_volume", {"track_index": track_index, "volume": volume})


@mcp.tool(description=get_command_spec("set_track_pan").tool_description)
def set_track_pan(track_index: int, pan: float):
    return _invoke("set_track_pan", {"track_index": track_index, "pan": pan})


@mcp.tool(description=get_command_spec("set_track_mute").tool_description)
def set_track_mute(track_index: int, mute: bool):
    return _invoke("set_track_mute", {"track_index": track_index, "mute": mute})


@mcp.tool(description=get_command_spec("set_track_solo").tool_description)
def set_track_solo(track_index: int, solo: bool):
    return _invoke("set_track_solo", {"track_index": track_index, "solo": solo})


@mcp.tool(description=get_command_spec("set_track_arm").tool_description)
def set_track_arm(track_index: int, arm: bool):
    return _invoke("set_track_arm", {"track_index": track_index, "arm": arm})


@mcp.tool(description=get_command_spec("fold_track").tool_description)
def fold_track(track_index: int):
    return _invoke("fold_track", {"track_index": track_index})


@mcp.tool(description=get_command_spec("unfold_track").tool_description)
def unfold_track(track_index: int):
    return _invoke("unfold_track", {"track_index": track_index})


@mcp.tool(description=get_command_spec("set_send_level").tool_description)
def set_send_level(track_index: int, send_index: int, level: float):
    return _invoke(
        "set_send_level",
        {"track_index": track_index, "send_index": send_index, "level": level},
    )


@mcp.tool(description=get_command_spec("get_return_tracks").tool_description)
def get_return_tracks():
    return _invoke("get_return_tracks", {})


@mcp.tool(description=get_command_spec("get_return_track_info").tool_description)
def get_return_track_info(return_index: int):
    return _invoke("get_return_track_info", {"return_index": return_index})


@mcp.tool(description=get_command_spec("set_return_volume").tool_description)
def set_return_volume(return_index: int, volume: float):
    return _invoke("set_return_volume", {"return_index": return_index, "volume": volume})


@mcp.tool(description=get_command_spec("set_return_pan").tool_description)
def set_return_pan(return_index: int, pan: float):
    return _invoke("set_return_pan", {"return_index": return_index, "pan": pan})


@mcp.tool(description=get_command_spec("select_track").tool_description)
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
    return _invoke("select_track", params)


@mcp.tool(description=get_command_spec("get_selected_track").tool_description)
def get_selected_track():
    return _invoke("get_selected_track", {})


@mcp.tool(description=get_command_spec("create_clip").tool_description)
def create_clip(track_index: int, slot_index: int, length: float = 4.0):
    return _invoke(
        "create_clip",
        {"track_index": track_index, "slot_index": slot_index, "length": length},
    )


@mcp.tool(description=get_command_spec("get_clip_notes").tool_description)
def get_clip_notes(track_index: int, slot_index: int):
    return _invoke("get_clip_notes", {"track_index": track_index, "slot_index": slot_index})


@mcp.tool(description=get_command_spec("add_notes_to_clip").tool_description)
def add_notes_to_clip(track_index: int, slot_index: int, notes: NoteList):
    return _invoke(
        "add_notes_to_clip",
        {"track_index": track_index, "slot_index": slot_index, "notes": notes},
    )


@mcp.tool(description=get_command_spec("get_arrangement_clips").tool_description)
def get_arrangement_clips(track_index: int):
    return _invoke("get_arrangement_clips", {"track_index": track_index})


@mcp.tool(description=get_command_spec("create_arrangement_midi_clip").tool_description)
def create_arrangement_midi_clip(track_index: int, start_time: float, length: float = 4.0):
    return _invoke(
        "create_arrangement_midi_clip",
        {"track_index": track_index, "start_time": start_time, "length": length},
    )


@mcp.tool(description=get_command_spec("create_arrangement_audio_clip").tool_description)
def create_arrangement_audio_clip(track_index: int, file_path: str, start_time: float):
    return _invoke(
        "create_arrangement_audio_clip",
        {"track_index": track_index, "file_path": file_path, "start_time": start_time},
    )


@mcp.tool(description=get_command_spec("delete_arrangement_clip").tool_description)
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
    return _invoke("delete_arrangement_clip", params)


@mcp.tool(description=get_command_spec("resize_arrangement_clip").tool_description)
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
    return _invoke("resize_arrangement_clip", params)


@mcp.tool(description=get_command_spec("move_arrangement_clip").tool_description)
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
    return _invoke("move_arrangement_clip", params)


@mcp.tool(description=get_command_spec("add_notes_to_arrangement_clip").tool_description)
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
    return _invoke("add_notes_to_arrangement_clip", params)


@mcp.tool(description=get_command_spec("get_arrangement_clip_notes").tool_description)
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
    return _invoke("get_arrangement_clip_notes", params)


@mcp.tool(description=get_command_spec("duplicate_to_arrangement").tool_description)
def duplicate_to_arrangement(track_index: int, slot_index: int, start_time: Optional[float] = None):
    params = {"track_index": track_index, "slot_index": slot_index}
    if start_time is not None:
        params["start_time"] = start_time
    return _invoke("duplicate_to_arrangement", params)


@mcp.tool(description=get_command_spec("get_browser_tree").tool_description)
def get_browser_tree(category_type: str = "all"):
    return _invoke("get_browser_tree", {"category_type": category_type})


@mcp.tool(description=get_command_spec("get_browser_items_at_path").tool_description)
def get_browser_items_at_path(path: str = ""):
    return _invoke("get_browser_items_at_path", {"path": path})


@mcp.tool(description=get_command_spec("search_browser").tool_description)
def search_browser(query: str, category: str = "all"):
    return _invoke("search_browser", {"query": query, "category": category})


@mcp.tool(description=get_command_spec("load_instrument_or_effect").tool_description)
def load_instrument_or_effect(
    track_index: int,
    device_name: Optional[str] = None,
    native_device_name: Optional[str] = None,
    uri: Optional[str] = None,
    target_index: Optional[int] = None,
):
    params = {"track_index": track_index}
    if device_name is not None:
        params["device_name"] = device_name
    if native_device_name is not None:
        params["native_device_name"] = native_device_name
    if uri is not None:
        params["uri"] = uri
    if target_index is not None:
        params["target_index"] = target_index
    return _invoke("load_instrument_or_effect", params)


@mcp.tool(description=get_command_spec("load_drum_kit").tool_description)
def load_drum_kit(track_index: int, rack_uri: str):
    return _invoke("load_drum_kit", {"track_index": track_index, "rack_uri": rack_uri})


@mcp.tool(description=get_command_spec("get_take_lanes").tool_description)
def get_take_lanes(track_index: int):
    return _invoke("get_take_lanes", {"track_index": track_index})


@mcp.tool(description=get_command_spec("create_take_lane").tool_description)
def create_take_lane(track_index: int):
    return _invoke("create_take_lane", {"track_index": track_index})


@mcp.tool(description=get_command_spec("set_take_lane_name").tool_description)
def set_take_lane_name(track_index: int, lane_index: int, name: str):
    return _invoke(
        "set_take_lane_name",
        {"track_index": track_index, "lane_index": lane_index, "name": name},
    )


@mcp.tool(description=get_command_spec("create_midi_clip_in_lane").tool_description)
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
    return _invoke("create_midi_clip_in_lane", params)


@mcp.tool(description=get_command_spec("get_clips_in_take_lane").tool_description)
def get_clips_in_take_lane(track_index: int, lane_index: int):
    return _invoke("get_clips_in_take_lane", {"track_index": track_index, "lane_index": lane_index})


@mcp.tool(description=get_command_spec("create_rack").tool_description)
def create_rack(track_index: int, rack_type: str, name: str, target_path: Optional[str] = None):
    params = {"track_index": track_index, "rack_type": rack_type, "name": name}
    if target_path is not None:
        params["target_path"] = target_path
    return _invoke("create_rack", params)


@mcp.tool(description=get_command_spec("insert_rack_chain").tool_description)
def insert_rack_chain(track_index: int, rack_path: str, name: str, index: Optional[int] = None):
    params = {"track_index": track_index, "rack_path": rack_path, "name": name}
    if index is not None:
        params["index"] = index
    return _invoke("insert_rack_chain", params)


@mcp.tool(description=get_command_spec("insert_device_in_chain").tool_description)
def insert_device_in_chain(
    track_index: int,
    chain_path: str,
    native_device_name: str,
    target_index: Optional[int] = None,
):
    params = {
        "track_index": track_index,
        "chain_path": chain_path,
        "native_device_name": native_device_name,
    }
    if target_index is not None:
        params["target_index"] = target_index
    return _invoke("insert_device_in_chain", params)


@mcp.tool(description=get_command_spec("get_rack_chains").tool_description)
def get_rack_chains(track_index: int, device_index: int):
    return _invoke("get_rack_chains", {"track_index": track_index, "device_index": device_index})


@mcp.tool(description=get_command_spec("get_rack_macros").tool_description)
def get_rack_macros(track_index: int, device_index: int):
    return _invoke("get_rack_macros", {"track_index": track_index, "device_index": device_index})


@mcp.tool(description=get_command_spec("set_rack_macro").tool_description)
def set_rack_macro(track_index: int, device_index: int, macro_index: int, value: float):
    return _invoke(
        "set_rack_macro",
        {
            "track_index": track_index,
            "device_index": device_index,
            "macro_index": macro_index,
            "value": value,
        },
    )


@mcp.tool(description=get_command_spec("get_rack_structure").tool_description)
def get_rack_structure(track_index: int, rack_path: str):
    return _invoke("get_rack_structure", {"track_index": track_index, "rack_path": rack_path})


@mcp.tool(description=get_command_spec("get_chain_devices").tool_description)
def get_chain_devices(track_index: int, device_index: int, chain_index: int):
    return _invoke(
        "get_chain_devices",
        {"track_index": track_index, "device_index": device_index, "chain_index": chain_index},
    )


@mcp.tool(description=get_command_spec("set_chain_mute").tool_description)
def set_chain_mute(track_index: int, device_index: int, chain_index: int, mute: bool):
    return _invoke(
        "set_chain_mute",
        {
            "track_index": track_index,
            "device_index": device_index,
            "chain_index": chain_index,
            "mute": mute,
        },
    )


@mcp.tool(description=get_command_spec("set_chain_solo").tool_description)
def set_chain_solo(track_index: int, device_index: int, chain_index: int, solo: bool):
    return _invoke(
        "set_chain_solo",
        {
            "track_index": track_index,
            "device_index": device_index,
            "chain_index": chain_index,
            "solo": solo,
        },
    )


@mcp.tool(description=get_command_spec("set_chain_volume").tool_description)
def set_chain_volume(track_index: int, device_index: int, chain_index: int, volume: float):
    return _invoke(
        "set_chain_volume",
        {
            "track_index": track_index,
            "device_index": device_index,
            "chain_index": chain_index,
            "volume": volume,
        },
    )


@mcp.tool(description=get_command_spec("get_drum_rack_pads").tool_description)
def get_drum_rack_pads(track_index: int, device_index: int):
    return _invoke("get_drum_rack_pads", {"track_index": track_index, "device_index": device_index})


@mcp.tool(description=get_command_spec("set_drum_rack_pad_note").tool_description)
def set_drum_rack_pad_note(track_index: int, device_index: int, note: int, new_note: int):
    return _invoke(
        "set_drum_rack_pad_note",
        {"track_index": track_index, "device_index": device_index, "note": note, "new_note": new_note},
    )


@mcp.tool(description=get_command_spec("set_drum_rack_pad_mute").tool_description)
def set_drum_rack_pad_mute(track_index: int, device_index: int, note: int, mute: bool):
    return _invoke(
        "set_drum_rack_pad_mute",
        {"track_index": track_index, "device_index": device_index, "note": note, "mute": mute},
    )


@mcp.tool(description=get_command_spec("set_drum_rack_pad_solo").tool_description)
def set_drum_rack_pad_solo(track_index: int, device_index: int, note: int, solo: bool):
    return _invoke(
        "set_drum_rack_pad_solo",
        {"track_index": track_index, "device_index": device_index, "note": note, "solo": solo},
    )


@mcp.tool(description=get_command_spec("apply_rack_blueprint").tool_description)
def apply_rack_blueprint(blueprint: JsonDict):
    return _invoke("apply_rack_blueprint", {"blueprint": blueprint})


@mcp.tool(description=get_command_spec("get_track_devices").tool_description)
def get_track_devices(track_index: int):
    return _invoke("get_track_devices", {"track_index": track_index})


@mcp.tool(description=get_command_spec("get_device_parameters").tool_description)
def get_device_parameters(track_index: int, device_index: int):
    return _invoke(
        "get_device_parameters",
        {"track_index": track_index, "device_index": device_index},
    )


@mcp.tool(description=get_command_spec("set_device_parameter_by_name").tool_description)
def set_device_parameter_by_name(track_index: int, device_index: int, name: str, value: float):
    return _invoke(
        "set_device_parameter_by_name",
        {"track_index": track_index, "device_index": device_index, "name": name, "value": value},
    )


@mcp.tool(description=get_command_spec("get_device_parameter_by_name").tool_description)
def get_device_parameter_by_name(track_index: int, device_index: int, name: str):
    return _invoke(
        "get_device_parameter_by_name",
        {"track_index": track_index, "device_index": device_index, "name": name},
    )


@mcp.tool(description=get_command_spec("get_device_parameters_at_path").tool_description)
def get_device_parameters_at_path(track_index: int, device_path: str):
    return _invoke(
        "get_device_parameters_at_path",
        {"track_index": track_index, "device_path": device_path},
    )


@mcp.tool(description=get_command_spec("set_device_parameter_at_path").tool_description)
def set_device_parameter_at_path(track_index: int, device_path: str, parameter_index: int, value: float):
    return _invoke(
        "set_device_parameter_at_path",
        {
            "track_index": track_index,
            "device_path": device_path,
            "parameter_index": parameter_index,
            "value": value,
        },
    )


@mcp.tool(description=get_command_spec("set_device_parameter_by_name_at_path").tool_description)
def set_device_parameter_by_name_at_path(track_index: int, device_path: str, name: str, value: float):
    return _invoke(
        "set_device_parameter_by_name_at_path",
        {"track_index": track_index, "device_path": device_path, "name": name, "value": value},
    )


@mcp.tool(description=get_command_spec("read_memory_bank").tool_description)
def read_memory_bank(file_name: str):
    return _invoke("read_memory_bank", {"file_name": file_name})


@mcp.tool(description=get_command_spec("write_memory_bank").tool_description)
def write_memory_bank(file_name: str, content: str):
    return _invoke("write_memory_bank", {"file_name": file_name, "content": content})


@mcp.tool(description=get_command_spec("append_rack_entry").tool_description)
def append_rack_entry(rack_data: str):
    return _invoke("append_rack_entry", {"rack_data": rack_data})


@mcp.tool(description=get_command_spec("get_system_owned_racks").tool_description)
def get_system_owned_racks():
    return _invoke("get_system_owned_racks", {})


@mcp.tool(description=get_command_spec("refresh_rack_memory_entry").tool_description)
def refresh_rack_memory_entry(track_index: int, rack_path: str):
    return _invoke(
        "refresh_rack_memory_entry",
        {"track_index": track_index, "rack_path": rack_path},
    )


@mcp.tool(
    description=(
        "Call any cataloged Ableton Remote Script command directly. "
        "Returns command metadata alongside the raw command result."
    )
)
def ableton_raw_command(type: str, params: Optional[JsonDict] = None):
    spec = get_command_spec(type)
    result = _invoke(type, params or {})
    return {
        "command": type,
        "domain": spec.domain,
        "stability": spec.stability,
        "mcp_exposed": spec.mcp_exposed,
        "result": result,
    }


def main():
    configuration = _get_run_configuration()
    mcp.run(transport=configuration["transport"], **configuration["kwargs"])


__all__ = ["FIRST_CLASS_MCP_COMMANDS", "ableton_raw_command", "main", "mcp", "server", "app"]
