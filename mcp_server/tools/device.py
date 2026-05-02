"""Device inspection, parameter access, and loading tools."""

from typing import Annotated, Any, Dict, Optional

from fastmcp import FastMCP
from pydantic import Field

from .. import _registry
from ._params import (
    DeviceIndex,
    DevicePath,
    ParameterIndex,
    ParameterValue,
    TrackIndex,
)


ParameterName = Annotated[
    str,
    Field(
        description=(
            "Live's parameter name. Validated EQ Eight shorthand aliases (e.g. 'Gain A', 'Frequency A', 'Q A') "
            "and device aliases (e.g. 'Eq8' -> 'EQ Eight') are normalized before lookup."
        ),
        min_length=1,
    ),
]
DeviceName = Annotated[
    str,
    Field(
        description="Live's display name for an instrument or effect.",
        min_length=1,
    ),
]
NativeDeviceName = Annotated[
    str,
    Field(
        description=(
            "Live's native device name (validated against Live's device list). "
            "Shorthand aliases like 'Eq8' are normalized to the canonical name."
        ),
        min_length=1,
    ),
]
DeviceUri = Annotated[
    str,
    Field(
        description=(
            "Browser URI for a built-in instrument, effect, or sounds preset (discoverable via search_browser). "
            "Third-party plugin URI loading is not currently discoverable through the validated browser roots."
        ),
        min_length=1,
    ),
]
TargetIndex = Annotated[
    int,
    Field(
        description=(
            "0-based insertion position for native-device insertion via Track.insert_device. "
            "Must be >= 0 and is native-only."
        ),
        ge=0,
    ),
]


def get_track_devices(track_index: TrackIndex):
    return _registry.invoke("get_track_devices", {"track_index": track_index})


def get_device_parameters(track_index: TrackIndex, device_index: DeviceIndex):
    return _registry.invoke(
        "get_device_parameters",
        {"track_index": track_index, "device_index": device_index},
    )


def set_device_parameter_by_name(
    track_index: TrackIndex,
    device_index: DeviceIndex,
    name: ParameterName,
    value: ParameterValue,
):
    return _registry.invoke(
        "set_device_parameter_by_name",
        {"track_index": track_index, "device_index": device_index, "name": name, "value": value},
    )


def get_device_parameter_by_name(
    track_index: TrackIndex,
    device_index: DeviceIndex,
    name: ParameterName,
):
    return _registry.invoke(
        "get_device_parameter_by_name",
        {"track_index": track_index, "device_index": device_index, "name": name},
    )


def get_device_parameters_at_path(track_index: TrackIndex, device_path: DevicePath):
    return _registry.invoke(
        "get_device_parameters_at_path",
        {"track_index": track_index, "device_path": device_path},
    )


def set_device_parameter_at_path(
    track_index: TrackIndex,
    device_path: DevicePath,
    parameter_index: ParameterIndex,
    value: ParameterValue,
):
    return _registry.invoke(
        "set_device_parameter_at_path",
        {
            "track_index": track_index,
            "device_path": device_path,
            "parameter_index": parameter_index,
            "value": value,
        },
    )


def set_device_parameter_by_name_at_path(
    track_index: TrackIndex,
    device_path: DevicePath,
    name: ParameterName,
    value: ParameterValue,
):
    return _registry.invoke(
        "set_device_parameter_by_name_at_path",
        {"track_index": track_index, "device_path": device_path, "name": name, "value": value},
    )


def load_instrument_or_effect(
    track_index: TrackIndex,
    device_name: Annotated[
        Optional[str],
        Field(
            default=None,
            description=(
                "Browser-discovered display name. Pass exactly one source: device_name, native_device_name, or uri."
            ),
            min_length=1,
        ),
    ] = None,
    native_device_name: Annotated[
        Optional[str],
        Field(
            default=None,
            description=(
                "Live's native device name (e.g. 'EQ Eight'; 'Eq8' is normalized). "
                "Pass exactly one source: device_name, native_device_name, or uri. "
                "Native insertion is limited to native Live devices."
            ),
            min_length=1,
        ),
    ] = None,
    uri: Annotated[
        Optional[str],
        Field(
            default=None,
            description=(
                "Browser URI for the device or preset (built-in content only on the validated build). "
                "Pass exactly one source: device_name, native_device_name, or uri."
            ),
            min_length=1,
        ),
    ] = None,
    target_index: Annotated[
        Optional[int],
        Field(
            default=None,
            description=(
                "0-based insertion position. Native-insertion only — used with native_device_name; "
                "ignored on URI loads."
            ),
            ge=0,
        ),
    ] = None,
):
    params: Dict[str, Any] = {"track_index": track_index}
    if device_name is not None:
        params["device_name"] = device_name
    if native_device_name is not None:
        params["native_device_name"] = native_device_name
    if uri is not None:
        params["uri"] = uri
    if target_index is not None:
        params["target_index"] = target_index
    return _registry.invoke("load_instrument_or_effect", params)


_TOOLS = (
    get_track_devices,
    get_device_parameters,
    set_device_parameter_by_name,
    get_device_parameter_by_name,
    get_device_parameters_at_path,
    set_device_parameter_at_path,
    set_device_parameter_by_name_at_path,
    load_instrument_or_effect,
)


def register(mcp: FastMCP) -> None:
    for fn in _TOOLS:
        _registry.ableton_tool(mcp, fn.__name__)(fn)
