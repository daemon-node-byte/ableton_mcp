"""Rack, chain, and drum-rack tools."""

from typing import Annotated, Any, Dict, Optional

from fastmcp import FastMCP
from pydantic import Field

from .. import _registry
from ._params import (
    ChainIndex,
    ChainPath,
    DeviceIndex,
    JsonCoerce,
    MacroIndex,
    MidiNote,
    Mute,
    NormalizedVolume,
    ParameterValue,
    RackPath,
    Solo,
    TrackIndex,
)


RackType = Annotated[
    str,
    Field(
        description=(
            "Rack kind to create. Validated values: 'instrument' (Instrument Rack) and "
            "'audio_effect' (Audio Effect Rack)."
        ),
        min_length=1,
    ),
]
RackName = Annotated[
    str,
    Field(description="Rack display name (non-empty).", min_length=1, max_length=200),
]
OptionalRackTargetPath = Annotated[
    Optional[str],
    Field(
        default=None,
        description=(
            "Optional track-relative LOM-style path to a target chain to insert this rack into. "
            "Omit to create at the top of the track."
        ),
        min_length=1,
    ),
]
ChainName = Annotated[
    str,
    Field(description="Chain display name (non-empty).", min_length=1, max_length=200),
]
OptionalChainInsertIndex = Annotated[
    Optional[int],
    Field(
        default=None,
        description="Optional 0-based insertion position within the rack's chains. Omit to append.",
        ge=0,
    ),
]
NativeDeviceName = Annotated[
    str,
    Field(
        description=(
            "Live's native device name (e.g. 'EQ Eight'; shorthand 'Eq8' is normalized). "
            "Native-only — no third-party plugins."
        ),
        min_length=1,
    ),
]
OptionalDeviceDisplayName = Annotated[
    Optional[str],
    Field(
        default=None,
        description="Optional display name override for the inserted device.",
        min_length=1,
    ),
]
OptionalChainTargetIndex = Annotated[
    Optional[int],
    Field(
        default=None,
        description="Optional 0-based insertion position within the chain's devices. Omit to append.",
        ge=0,
    ),
]
RackBlueprint = Annotated[
    Dict[str, Any],
    JsonCoerce,
    Field(
        description=(
            "Declarative rack blueprint. Native macro-to-parameter and macro-to-macro mappings "
            "are explicitly unsupported and raise a stable error if included (no documented LOM API). "
            "May be passed as a JSON-encoded string."
        )
    ),
]


def create_rack(
    track_index: TrackIndex,
    rack_type: RackType,
    name: RackName,
    target_path: OptionalRackTargetPath = None,
):
    params: Dict[str, Any] = {"track_index": track_index, "rack_type": rack_type, "name": name}
    if target_path is not None:
        params["target_path"] = target_path
    return _registry.invoke("create_rack", params)


def insert_rack_chain(
    track_index: TrackIndex,
    rack_path: RackPath,
    name: ChainName,
    index: OptionalChainInsertIndex = None,
):
    params: Dict[str, Any] = {"track_index": track_index, "rack_path": rack_path, "name": name}
    if index is not None:
        params["index"] = index
    return _registry.invoke("insert_rack_chain", params)


def insert_device_in_chain(
    track_index: TrackIndex,
    chain_path: ChainPath,
    native_device_name: NativeDeviceName,
    device_name: OptionalDeviceDisplayName = None,
    target_index: OptionalChainTargetIndex = None,
):
    params: Dict[str, Any] = {
        "track_index": track_index,
        "chain_path": chain_path,
        "native_device_name": native_device_name,
    }
    if device_name is not None:
        params["device_name"] = device_name
    if target_index is not None:
        params["target_index"] = target_index
    return _registry.invoke("insert_device_in_chain", params)


def get_rack_chains(track_index: TrackIndex, device_index: DeviceIndex):
    return _registry.invoke(
        "get_rack_chains",
        {"track_index": track_index, "device_index": device_index},
    )


def get_rack_macros(track_index: TrackIndex, device_index: DeviceIndex):
    return _registry.invoke(
        "get_rack_macros",
        {"track_index": track_index, "device_index": device_index},
    )


def set_rack_macro(
    track_index: TrackIndex,
    device_index: DeviceIndex,
    macro_index: MacroIndex,
    value: ParameterValue,
):
    return _registry.invoke(
        "set_rack_macro",
        {
            "track_index": track_index,
            "device_index": device_index,
            "macro_index": macro_index,
            "value": value,
        },
    )


def get_rack_structure(track_index: TrackIndex, rack_path: RackPath):
    return _registry.invoke(
        "get_rack_structure",
        {"track_index": track_index, "rack_path": rack_path},
    )


def get_chain_devices(track_index: TrackIndex, device_index: DeviceIndex, chain_index: ChainIndex):
    return _registry.invoke(
        "get_chain_devices",
        {"track_index": track_index, "device_index": device_index, "chain_index": chain_index},
    )


def set_chain_mute(
    track_index: TrackIndex,
    device_index: DeviceIndex,
    chain_index: ChainIndex,
    mute: Mute,
):
    return _registry.invoke(
        "set_chain_mute",
        {
            "track_index": track_index,
            "device_index": device_index,
            "chain_index": chain_index,
            "mute": mute,
        },
    )


def set_chain_solo(
    track_index: TrackIndex,
    device_index: DeviceIndex,
    chain_index: ChainIndex,
    solo: Solo,
):
    return _registry.invoke(
        "set_chain_solo",
        {
            "track_index": track_index,
            "device_index": device_index,
            "chain_index": chain_index,
            "solo": solo,
        },
    )


def set_chain_volume(
    track_index: TrackIndex,
    device_index: DeviceIndex,
    chain_index: ChainIndex,
    volume: NormalizedVolume,
):
    return _registry.invoke(
        "set_chain_volume",
        {
            "track_index": track_index,
            "device_index": device_index,
            "chain_index": chain_index,
            "volume": volume,
        },
    )


def get_drum_rack_pads(track_index: TrackIndex, device_index: DeviceIndex):
    return _registry.invoke(
        "get_drum_rack_pads",
        {"track_index": track_index, "device_index": device_index},
    )


def set_drum_rack_pad_note(
    track_index: TrackIndex,
    device_index: DeviceIndex,
    note: MidiNote,
    new_note: MidiNote,
):
    return _registry.invoke(
        "set_drum_rack_pad_note",
        {
            "track_index": track_index,
            "device_index": device_index,
            "note": note,
            "new_note": new_note,
        },
    )


def set_drum_rack_pad_mute(
    track_index: TrackIndex,
    device_index: DeviceIndex,
    note: MidiNote,
    mute: Mute,
):
    return _registry.invoke(
        "set_drum_rack_pad_mute",
        {"track_index": track_index, "device_index": device_index, "note": note, "mute": mute},
    )


def set_drum_rack_pad_solo(
    track_index: TrackIndex,
    device_index: DeviceIndex,
    note: MidiNote,
    solo: Solo,
):
    return _registry.invoke(
        "set_drum_rack_pad_solo",
        {"track_index": track_index, "device_index": device_index, "note": note, "solo": solo},
    )


def apply_rack_blueprint(blueprint: RackBlueprint):
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
