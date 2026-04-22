"""Rack, chain, and drum-rack tools."""

from __future__ import absolute_import, print_function, unicode_literals

from typing import Any, Dict, Optional

from fastmcp import FastMCP

from .. import _registry


JsonDict = Dict[str, Any]


def create_rack(track_index: int, rack_type: str, name: str, target_path: Optional[str] = None):
    params = {"track_index": track_index, "rack_type": rack_type, "name": name}
    if target_path is not None:
        params["target_path"] = target_path
    return _registry.invoke("create_rack", params)


def insert_rack_chain(track_index: int, rack_path: str, name: str, index: Optional[int] = None):
    params = {"track_index": track_index, "rack_path": rack_path, "name": name}
    if index is not None:
        params["index"] = index
    return _registry.invoke("insert_rack_chain", params)


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
    return _registry.invoke("insert_device_in_chain", params)


def get_rack_chains(track_index: int, device_index: int):
    return _registry.invoke(
        "get_rack_chains",
        {"track_index": track_index, "device_index": device_index},
    )


def get_rack_macros(track_index: int, device_index: int):
    return _registry.invoke(
        "get_rack_macros",
        {"track_index": track_index, "device_index": device_index},
    )


def set_rack_macro(track_index: int, device_index: int, macro_index: int, value: float):
    return _registry.invoke(
        "set_rack_macro",
        {
            "track_index": track_index,
            "device_index": device_index,
            "macro_index": macro_index,
            "value": value,
        },
    )


def get_rack_structure(track_index: int, rack_path: str):
    return _registry.invoke(
        "get_rack_structure",
        {"track_index": track_index, "rack_path": rack_path},
    )


def get_chain_devices(track_index: int, device_index: int, chain_index: int):
    return _registry.invoke(
        "get_chain_devices",
        {"track_index": track_index, "device_index": device_index, "chain_index": chain_index},
    )


def set_chain_mute(track_index: int, device_index: int, chain_index: int, mute: bool):
    return _registry.invoke(
        "set_chain_mute",
        {
            "track_index": track_index,
            "device_index": device_index,
            "chain_index": chain_index,
            "mute": mute,
        },
    )


def set_chain_solo(track_index: int, device_index: int, chain_index: int, solo: bool):
    return _registry.invoke(
        "set_chain_solo",
        {
            "track_index": track_index,
            "device_index": device_index,
            "chain_index": chain_index,
            "solo": solo,
        },
    )


def set_chain_volume(track_index: int, device_index: int, chain_index: int, volume: float):
    return _registry.invoke(
        "set_chain_volume",
        {
            "track_index": track_index,
            "device_index": device_index,
            "chain_index": chain_index,
            "volume": volume,
        },
    )


def get_drum_rack_pads(track_index: int, device_index: int):
    return _registry.invoke(
        "get_drum_rack_pads",
        {"track_index": track_index, "device_index": device_index},
    )


def set_drum_rack_pad_note(track_index: int, device_index: int, note: int, new_note: int):
    return _registry.invoke(
        "set_drum_rack_pad_note",
        {
            "track_index": track_index,
            "device_index": device_index,
            "note": note,
            "new_note": new_note,
        },
    )


def set_drum_rack_pad_mute(track_index: int, device_index: int, note: int, mute: bool):
    return _registry.invoke(
        "set_drum_rack_pad_mute",
        {"track_index": track_index, "device_index": device_index, "note": note, "mute": mute},
    )


def set_drum_rack_pad_solo(track_index: int, device_index: int, note: int, solo: bool):
    return _registry.invoke(
        "set_drum_rack_pad_solo",
        {"track_index": track_index, "device_index": device_index, "note": note, "solo": solo},
    )


def apply_rack_blueprint(blueprint: JsonDict):
    return _registry.invoke("apply_rack_blueprint", {"blueprint": blueprint})


_TOOLS = (
    create_rack,
    insert_rack_chain,
    insert_device_in_chain,
    get_rack_chains,
    get_rack_macros,
    set_rack_macro,
    get_rack_structure,
    get_chain_devices,
    set_chain_mute,
    set_chain_solo,
    set_chain_volume,
    get_drum_rack_pads,
    set_drum_rack_pad_note,
    set_drum_rack_pad_mute,
    set_drum_rack_pad_solo,
    apply_rack_blueprint,
)


def register(mcp: FastMCP) -> None:
    for fn in _TOOLS:
        _registry.ableton_tool(mcp, fn.__name__)(fn)
